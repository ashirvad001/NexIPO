"""
Evaluate LSTM Volatility Model – Phase 2
==========================================
Loads the trained model and validation data, computes regression
metrics (MAE, RMSE, R²), risk-classification accuracy, and
generates a predicted-vs-actual scatter plot.

Run from ``backend/``:
    python scripts/evaluate_model.py
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from app.ml_service.volatility.lstm_model import LSTMVolatilityPredictor

DATA_PATH = "models/training_data.npz"
MODEL_PATH = "models/lstm_volatility_model.pth"
PLOT_PATH = "models/predictions_plot.png"


def evaluate_model():
    # ---- load model ----
    lstm = LSTMVolatilityPredictor()
    lstm.load_model(MODEL_PATH)

    # ---- load & prepare validation data ----
    data = np.load(DATA_PATH)
    X_val_raw = data["X_val"]
    y_val_raw = data["y_val"]

    X_val_sc = lstm.scaler.transform(X_val_raw)
    y_val_sc = lstm.target_scaler.transform(y_val_raw.reshape(-1, 1)).ravel()

    X_seq, y_seq = lstm.prepare_sequences(X_val_sc, y_val_sc)

    # ---- predict ----
    y_pred_sc = lstm.predict(X_seq)

    # Inverse-transform both to original scale
    y_actual = lstm.target_scaler.inverse_transform(
        y_seq.reshape(-1, 1)
    ).ravel()
    y_pred = lstm.target_scaler.inverse_transform(
        y_pred_sc.reshape(-1, 1)
    ).ravel()

    # ---- regression metrics ----
    mae = mean_absolute_error(y_actual, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_actual, y_pred)))
    r2 = r2_score(y_actual, y_pred)

    print("=" * 55)
    print("  MODEL EVALUATION")
    print("=" * 55)
    print(f"  Samples : {len(y_actual):,}")
    print(f"  MAE     : {mae:.6f}")
    print(f"  RMSE    : {rmse:.6f}")
    print(f"  R²      : {r2:.4f}")

    # ---- risk-level accuracy ----
    actual_levels = [lstm.calculate_risk_level(v) for v in y_actual]
    pred_levels = [lstm.calculate_risk_level(v) for v in y_pred]
    correct = sum(a == p for a, p in zip(actual_levels, pred_levels))
    risk_acc = correct / len(actual_levels) * 100
    print(f"\n  Risk-level accuracy: {risk_acc:.1f}%  ({correct}/{len(actual_levels)})")

    # ---- scatter plot ----
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.scatter(y_actual, y_pred, alpha=0.35, s=10, color="#4C72B0")
        lo = min(y_actual.min(), y_pred.min())
        hi = max(y_actual.max(), y_pred.max())
        ax.plot([lo, hi], [lo, hi], "r--", linewidth=1.2, label="Perfect")
        ax.set_xlabel("Actual Volatility")
        ax.set_ylabel("Predicted Volatility")
        ax.set_title(f"Predicted vs Actual Volatility  (R²={r2:.3f})")
        ax.legend()
        fig.tight_layout()
        fig.savefig(PLOT_PATH, dpi=150)
        plt.close(fig)
        print(f"\n  ✓ Plot saved to {PLOT_PATH}")
    except ImportError:
        print("\n  ⚠ matplotlib not installed – skipping plot.")

    return {"mae": mae, "rmse": rmse, "r2": r2, "risk_accuracy": risk_acc}


if __name__ == "__main__":
    evaluate_model()
