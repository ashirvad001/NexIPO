"""
Daily job to update volatility forecasts
"""

import sys
import os
import logging
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.database import get_db
from app.models.ipo import IPO, IPOStatus
from app.ml_service.volatility.volatility_predictor import VolatilityForecaster

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)s  %(levelname)s  %(message)s",
)
logger = logging.getLogger(__name__)

def send_volatility_alert(ipo: IPO, result: dict):
    """
    Simulated alerting system (e.g. Email, Slack, Push Notification)
    """
    logger.warning(
        f"🚨 VOLATILITY ALERT: {ipo.symbol} ({ipo.company_name}) "
        f"Predicted Risk: {result['risk_level']} "
        f"({result['predicted_volatility_percentage']:.2f}%)"
    )

def update_all_volatility_forecasts():
    """
    Run daily to update volatility predictions
    
    1. Get all listed IPOs
    2. Predict volatility for each
    3. Store in database
    4. Send alerts if HIGH/VERY HIGH
    """
    logger.info("🔄 Starting daily volatility update...")
    
    db = next(get_db())
    try:
        forecaster = VolatilityForecaster()
    except Exception as e:
        logger.error(f"Failed to initialize forecaster for cron job: {e}")
        sys.exit(1)
    
    # Get listed IPOs
    ipos = db.query(IPO).filter(IPO.status == IPOStatus.LISTED).all()
    logger.info(f"Found {len(ipos)} listed IPOs to forecast.")
    
    success_count = 0
    
    for ipo in ipos:
        if not ipo.symbol:
            continue
            
        try:
            logger.info(f"Predicting for {ipo.symbol}...")
            # Predict volatility
            result = forecaster.predict_volatility(
                ipo.symbol,
                ipo.company_name
            )
            
            # Save volatility prediction
            ipo.risk_score = result.get('predicted_volatility_percentage')
            ipo.risk_category = result.get('risk_level')
            ipo.ml_processed = True
            ipo.ml_processed_at = datetime.now()
            db.commit()
            
            success_count += 1
            
            # Send alert if high volatility
            if result['risk_level'] in ['HIGH', 'VERY HIGH']:
                send_volatility_alert(ipo, result)
            
        except Exception as e:
            logger.error(f"❌ Failed for {ipo.symbol}: {e}")
    
    logger.info(f"✅ Daily volatility update complete. Processed {success_count}/{len(ipos)} IPOs.")

if __name__ == "__main__":
    update_all_volatility_forecasts()
