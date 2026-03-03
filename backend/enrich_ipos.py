"""
Standalone IPO Data Enrichment Script
=====================================
Reads all IPOs from the database, identifies missing fields, scrapes
Moneycontrol detail pages to fill gaps, and generates a report.

Usage:
    python enrich_ipos.py              # Enrich all IPOs with missing data
    python enrich_ipos.py --report     # Show report only (no scraping)
    python enrich_ipos.py --force      # Re-enrich even if recently enriched

Priority order:
    1. Open/Active IPOs (most important)
    2. Recently Closed IPOs (last 30 days)
    3. Upcoming IPOs
    4. Listed/Historical IPOs
"""

import sys
import asyncio
import argparse
from datetime import datetime, timedelta
from collections import defaultdict

from app.db.database import SessionLocal, engine, Base
from app.models.ipo import IPO, IPOStatus
from app.services.ipo_scraper import (
    sync_ipos,
    scrape_moneycontrol_ipo_links,
    enrich_from_moneycontrol,
    scrape_gmp_data,
    _normalize_name,
    _count_missing_fields,
)


def generate_report(db) -> str:
    """Generate a report of data completeness for all IPOs."""
    ipos = db.query(IPO).order_by(IPO.created_at.desc()).all()

    lines = []
    lines.append("=" * 80)
    lines.append(f"  NexIPO Data Completeness Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 80)
    lines.append(f"\n  Total IPOs in database: {len(ipos)}\n")

    # Group by status
    by_status = defaultdict(list)
    for ipo in ipos:
        by_status[ipo.status.value if ipo.status else "unknown"].append(ipo)

    for status, group in sorted(by_status.items()):
        lines.append(f"  [{status.upper()}] — {len(group)} IPOs")

    lines.append("")

    # Detail per IPO
    all_fields = [
        "price_band_lower", "price_band_upper", "issue_price", "listing_price",
        "current_price", "open_date", "close_date", "allotment_date", "listing_date",
        "issue_size_rs_cr", "fresh_issue_size", "offer_for_sale", "shares_offered",
        "face_value", "lot_size", "min_investment",
        "qib_subscription", "nii_subscription", "retail_subscription", "total_subscription",
        "gmp_amount", "gmp_percentage", "estimated_listing_price",
        "industry_sector", "registrar", "lead_managers", "description",
        "pe_ratio", "roce", "roe", "eps", "revenue_cr", "profit_cr", "market_cap_cr",
    ]

    total_fields = len(all_fields)
    total_filled = 0
    total_possible = 0

    lines.append("-" * 80)
    lines.append(f"  {'Company':<35} {'Status':<10} {'Filled':>6} {'Missing':>7} {'%':>5}  Missing Fields")
    lines.append("-" * 80)

    for ipo in ipos:
        missing = []
        filled = 0
        for f in all_fields:
            val = getattr(ipo, f, None)
            if val is None:
                missing.append(f)
            else:
                filled += 1

        total_filled += filled
        total_possible += total_fields

        pct = (filled / total_fields * 100) if total_fields > 0 else 0
        status_str = ipo.status.value if ipo.status else "?"

        # Show up to 3 missing field names
        missing_str = ", ".join(missing[:4])
        if len(missing) > 4:
            missing_str += f" (+{len(missing)-4} more)"

        name = ipo.company_name[:33] if ipo.company_name else "?"
        lines.append(
            f"  {name:<35} {status_str:<10} {filled:>3}/{total_fields:<2} {len(missing):>5}  {pct:>5.1f}%  {missing_str}"
        )

    lines.append("-" * 80)
    overall_pct = (total_filled / total_possible * 100) if total_possible > 0 else 0
    lines.append(f"\n  Overall completeness: {total_filled}/{total_possible} ({overall_pct:.1f}%)")
    lines.append("")

    return "\n".join(lines)


async def run_enrichment(force: bool = False):
    """Main enrichment pipeline."""
    db = SessionLocal()

    try:
        print("\n🚀 NexIPO Data Enrichment Pipeline")
        print("=" * 50)

        # Step 1: Run base sync (IPO Central + GMP)
        print("\n📡 Step 1: Syncing from IPO Central...")
        summary = await sync_ipos(db)
        print(f"   Added: {summary['added']}, Updated: {summary['updated']}, "
              f"Enriched: {summary['enriched']}, Errors: {summary['errors']}")

        # Step 2: Additional GMP enrichment for existing IPOs
        print("\n📊 Step 2: Enriching GMP data for all IPOs...")
        gmp_data = await scrape_gmp_data()
        gmp_enriched = 0

        if gmp_data:
            all_ipos = db.query(IPO).all()
            for ipo in all_ipos:
                norm_name = _normalize_name(ipo.company_name)
                matched_gmp = None

                if norm_name in gmp_data:
                    matched_gmp = gmp_data[norm_name]
                else:
                    for gmp_name, gmp_vals in gmp_data.items():
                        if len(norm_name) > 5 and len(gmp_name) > 5:
                            if norm_name in gmp_name or gmp_name in norm_name:
                                matched_gmp = gmp_vals
                                break

                if matched_gmp:
                    updated = False
                    for field, value in matched_gmp.items():
                        if value is not None and getattr(ipo, field, None) is None:
                            setattr(ipo, field, value)
                            updated = True
                    if updated:
                        gmp_enriched += 1

            db.commit()
        print(f"   GMP enriched: {gmp_enriched} IPOs")

        # Step 3: Moneycontrol enrichment for IPOs with many missing fields
        print("\n🔍 Step 3: Enriching from Moneycontrol detail pages...")
        mc_links = await scrape_moneycontrol_ipo_links()
        mc_enriched = 0

        if mc_links:
            all_ipos = db.query(IPO).all()
            # Priority: open > closed > upcoming > listed
            priority_order = {
                IPOStatus.OPEN: 0,
                IPOStatus.CLOSED: 1,
                IPOStatus.UPCOMING: 2,
                IPOStatus.LISTED: 3,
            }
            sorted_ipos = sorted(all_ipos, key=lambda x: priority_order.get(x.status, 4))

            for ipo in sorted_ipos:
                # Skip if recently enriched (unless forced)
                if not force and ipo.last_enriched_at:
                    age = datetime.now() - ipo.last_enriched_at
                    if age < timedelta(hours=12):
                        continue

                missing = _count_missing_fields(ipo)
                if len(missing) < 2 and not force:
                    continue

                try:
                    result = await enrich_from_moneycontrol(db, ipo, mc_links)
                    if result["fields_updated"] > 0:
                        mc_enriched += 1
                        print(f"   ✅ {ipo.company_name}: +{result['fields_updated']} fields")
                    elif result["status"] == "no_match":
                        print(f"   ⚠️  {ipo.company_name}: no Moneycontrol match found")
                except Exception as e:
                    print(f"   ❌ {ipo.company_name}: error - {e}")

        print(f"\n   Moneycontrol enriched: {mc_enriched} IPOs")

        # Step 4: Final report
        print("\n" + "=" * 50)
        print("📋 Final Report:")
        print("=" * 50)
        report = generate_report(db)
        print(report)

        # Save report to file
        report_path = "enrichment_report.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n📄 Report saved to: {report_path}")

        # Summary
        print("\n✅ Enrichment complete!")
        print(f"   Total synced: {summary['total_scraped']}")
        print(f"   Added: {summary['added']}")
        print(f"   Updated: {summary['updated']}")
        print(f"   GMP enriched: {gmp_enriched}")
        print(f"   MC enriched: {mc_enriched}")
        print(f"   Errors: {summary['errors']}")

    except Exception as e:
        print(f"\n❌ Enrichment failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="NexIPO Data Enrichment")
    parser.add_argument("--report", action="store_true", help="Show report only")
    parser.add_argument("--force", action="store_true", help="Force re-enrichment")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)

    if args.report:
        db = SessionLocal()
        try:
            print(generate_report(db))
        finally:
            db.close()
        return

    asyncio.run(run_enrichment(force=args.force))


if __name__ == "__main__":
    main()
