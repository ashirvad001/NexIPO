"""
Prepare Training Data – Phase 2 of Stock Volatility Forecaster
===============================================================
Downloads price data for 50+ historical Indian IPOs via yfinance,
engineers 8 daily features, and saves train/val splits as .npz.

Run from ``backend/``:
    python scripts/prepare_training_data.py
"""

import os
import sys
import warnings

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore", category=FutureWarning)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ---------------------------------------------------------------------------
# 50+ historical Indian IPO symbols (Yahoo Finance .NS suffix)
# ---------------------------------------------------------------------------
HISTORICAL_IPOS = [
    # ---- 2024 IPOs ----
    "TATATECH.NS",
    "IDEAFORGE.NS",
    "JSWINFRA.NS",
    "IREDA.NS",
    "CELLO.NS",
    "DOMS.NS",

    # ---- 2023 IPOs ----
    "YATRA.NS",
    "MANKIND.NS",
    "JIOFI.NS",
    "CONCORDBIO.NS",
    "SENCO.NS",
    "NETWEB.NS",

    # ---- 2022 IPOs ----
    "DELHIVERY.NS",
    "RAINBOW.NS",
    "CAMPUS.NS",
    "EMUDHRA.NS",
    "KAYNES.NS",
    "VEDANT.NS",

    # ---- 2021 IPOs ----
    "ZOMATO.NS",
    "NYKAA.NS",
    "PAYTM.NS",
    "POLICYBZR.NS",
    "CARTRADE.NS",
    "TATVA.NS",
    "CLEAN.NS",
    "HAPPSTMNDS.NS",
    "ROUTE.NS",
    "LATENTVIEW.NS",
    "SBICARD.NS",
    "EASEMYTRIP.NS",
    "NAZARA.NS",
    "KRSNAA.NS",
    "DEVYANI.NS",
    "APTUS.NS",
    "GLENMARK.NS",
    "LODHA.NS",
    "MEDPLUS.NS",
    "STARHEALTH.NS",
    "SAPPHIRE.NS",
    "RATEGAIN.NS",

    # ---- 2020 IPOs ----
    "BARBEQUE.NS",
    "CHEMCON.NS",
    "BURGER.NS",
    "ROSARI.NS",
    "MAZAGON.NS",
    "UTI.NS",
    "ANGELONE.NS",
    "INDIGO.NS",

    # ---- Established large-caps for extra data diversity ----
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",
    "WIPRO.NS",
    "LT.NS",
    "BAJFINANCE.NS",
]

N_FEATURES = 8  # must match the feature engineering below


# ---------------------------------------------------------------------------
# Feature engineering helpers
# ---------------------------------------------------------------------------
def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index."""
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / (loss + 1e-10)
    return 100 - 100 / (1 + rs)


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    From OHLCV data, create 8 daily features:
        0  log_return           ln(Close/Close_prev)
        1  rolling_vol_7d       7-day rolling std of log returns × √252
        2  volume_change        ln(Volume/Volume_prev)
        3  high_low_range       (High - Low) / Close
        4  rsi_14               14-day RSI normalised to [0,1]
        5  sma_ratio_20         Close / SMA(20) − 1
        6  sentiment_proxy      sign(return) × |return| (price-action proxy)
        7  momentum_5d          Close / Close_5_ago − 1
    """
    close = df["Close"].squeeze()
    high = df["High"].squeeze()
    low = df["Low"].squeeze()
    volume = df["Volume"].squeeze()

    feat = pd.DataFrame(index=df.index)
    feat["log_return"] = np.log(close / close.shift(1))
    feat["rolling_vol_7d"] = feat["log_return"].rolling(7).std() * np.sqrt(252)
    feat["volume_change"] = np.log((volume + 1) / (volume.shift(1) + 1))
    feat["high_low_range"] = (high - low) / (close + 1e-10)
    feat["rsi_14"] = _rsi(close, 14) / 100.0
    sma20 = close.rolling(20).mean()
    feat["sma_ratio_20"] = (close / (sma20 + 1e-10)) - 1
    feat["sentiment_proxy"] = np.sign(feat["log_return"]) * feat["log_return"].abs()
    feat["momentum_5d"] = (close / close.shift(5)) - 1

    return feat


def compute_target(df: pd.DataFrame, window: int = 7) -> pd.Series:
    """Next-day rolling annualised volatility (shifted forward by 1)."""
    close = df["Close"].squeeze()
    log_ret = np.log(close / close.shift(1))
    rolling_vol = log_ret.rolling(window).std() * np.sqrt(252)
    return rolling_vol.shift(-1)  # predict tomorrow's vol


# ---------------------------------------------------------------------------
# Per-symbol collection
# ---------------------------------------------------------------------------
def collect_ipo_data(symbol: str, period: str = "2y") -> dict | None:
    """
    Download price data for *symbol*, engineer features + target.

    Returns dict with ``features`` (N, 8) and ``targets`` (N,), or ``None``
    if the symbol has insufficient data.
    """
    try:
        df = yf.download(symbol, period=period, progress=False)
    except Exception as exc:
        print(f"  ✗ yfinance error for {symbol}: {exc}")
        return None

    if df.empty or len(df) < 40:
        print(f"  ✗ Not enough data for {symbol} ({len(df)} rows)")
        return None

    # Flatten MultiIndex columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    features = engineer_features(df)
    targets = compute_target(df)

    # Merge and drop NaN rows
    combined = features.copy()
    combined["target"] = targets
    combined.dropna(inplace=True)

    if len(combined) < 30:
        print(f"  ✗ Too few valid rows for {symbol} ({len(combined)})")
        return None

    X = combined.drop(columns=["target"]).values.astype(np.float32)
    y = combined["target"].values.astype(np.float32)
    return {"features": X, "targets": y, "rows": len(X)}


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def prepare_training_dataset():
    """
    Collect data for all symbols, stack, and split 80/20 chronologically.
    """
    all_X, all_y = [], []
    success = 0

    for idx, symbol in enumerate(HISTORICAL_IPOS, 1):
        print(f"[{idx:2d}/{len(HISTORICAL_IPOS)}] {symbol:<20s}", end="")
        result = collect_ipo_data(symbol)
        if result is not None:
            all_X.append(result["features"])
            all_y.append(result["targets"])
            success += 1
            print(f"  ✓ {result['rows']} rows")
        # (failure message already printed inside collect_ipo_data)

    if success == 0:
        raise RuntimeError("No data collected – check your internet connection.")

    X_all = np.concatenate(all_X, axis=0)
    y_all = np.concatenate(all_y, axis=0)

    # Chronological-like split (80 / 20)
    split = int(len(X_all) * 0.8)
    X_train, X_val = X_all[:split], X_all[split:]
    y_train, y_val = y_all[:split], y_all[split:]

    print(f"\n{'─' * 50}")
    print(f"Symbols processed: {success}/{len(HISTORICAL_IPOS)}")
    print(f"Total rows:        {len(X_all):,}")
    print(f"Train rows:        {len(X_train):,}")
    print(f"Val   rows:        {len(X_val):,}")
    print(f"Features:          {X_train.shape[1]}")

    return X_train, y_train, X_val, y_val


def save_training_data(X_train, y_train, X_val, y_val, out_dir="models"):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "training_data.npz")
    np.savez(path, X_train=X_train, y_train=y_train, X_val=X_val, y_val=y_val)
    print(f"\n✓ Training data saved to {path}")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 55)
    print("  PREPARING TRAINING DATA – Volatility Forecaster")
    print("=" * 55 + "\n")

    X_tr, y_tr, X_v, y_v = prepare_training_dataset()
    save_training_data(X_tr, y_tr, X_v, y_v)

    print("\n" + "=" * 55)
    print("  ✅  DATA PREPARATION COMPLETE")
    print("=" * 55)
