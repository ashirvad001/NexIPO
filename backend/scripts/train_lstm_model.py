"""
Train LSTM Volatility Model – Phase 2
=======================================
Loads the prepared .npz data, builds the BiLSTM,
trains with early stopping, and saves the best checkpoint.

Run from ``backend/``:
    python scripts/train_lstm_model.py
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ml_service.volatility.lstm_model import LSTMVolatilityPredictor


DATA_PATH = "models/training_data.npz"
MODEL_PATH = "models/lstm_volatility_model.pth"


# ---------------------------------------------------------------------------
def load_training_data():
    data = np.load(DATA_PATH)
    return data["X_train"], data["y_train"], data["X_val"], data["y_val"]


def train_model():
    print("=" * 55)
    print("  TRAINING LSTM MODEL")
    print("=" * 55)

    # ---- load data ----
    print("\n📊 Loading training data …")
    X_train_raw, y_train, X_val_raw, y_val = load_training_data()
    print(f"   Raw train: {X_train_raw.shape}  |  Val: {X_val_raw.shape}")

    # ---- create predictor & prepare sequences ----
    lstm = LSTMVolatilityPredictor(
        sequence_length=30,
        lstm_units=128,
        dropout_rate=0.2,
    )

    # Scale features
    lstm.scaler.fit(X_train_raw)
    X_train_sc = lstm.scaler.transform(X_train_raw)
    X_val_sc = lstm.scaler.transform(X_val_raw)

    # Scale targets
    y_train_2d = y_train.reshape(-1, 1)
    y_val_2d = y_val.reshape(-1, 1)
    lstm.target_scaler.fit(y_train_2d)
    y_train_sc = lstm.target_scaler.transform(y_train_2d).ravel()
    y_val_sc = lstm.target_scaler.transform(y_val_2d).ravel()

    # Create sequences
    X_tr_seq, y_tr_seq = lstm.prepare_sequences(X_train_sc, y_train_sc)
    X_v_seq, y_v_seq = lstm.prepare_sequences(X_val_sc, y_val_sc)

    print(f"   Sequence train: {X_tr_seq.shape}  |  Val: {X_v_seq.shape}")
    print(f"   Input shape per sample: ({lstm.sequence_length}, {X_tr_seq.shape[2]})")

    # ---- build model ----
    print("\n🏗️  Building LSTM model …")
    lstm.build_model(input_size=X_tr_seq.shape[2])

    # ---- train ----
    print("\n🚀 Starting training …\n")
    history = lstm.train(
        X_tr_seq, y_tr_seq,
        X_v_seq, y_v_seq,
        epochs=100,
        batch_size=32,
        patience=10,
        model_save_path=MODEL_PATH,
    )

    print("\n" + "=" * 55)
    print("  TRAINING COMPLETE!")
    print("=" * 55)
    print(f"  Best epoch:   {history['best_epoch']}")
    print(f"  Train loss:   {history['train_loss']:.6f}")
    print(f"  Val   loss:   {history['val_loss']:.6f}")

    # ---- save model + scalers ----
    print("\n💾 Saving model …")
    lstm.save_model(MODEL_PATH)
    print(f"  ✓ Model saved to {MODEL_PATH}")

    # ---- quick test prediction ----
    print("\n🧪 Testing prediction …")
    sample = X_v_seq[:1]
    pred_mean, pred_std = lstm.predict_with_confidence(sample, n_iterations=50)

    # Inverse-transform to original scale
    pred_orig = lstm.target_scaler.inverse_transform(
        pred_mean.reshape(-1, 1)
    ).ravel()

    vol = float(pred_orig[0])
    print(f"  Predicted volatility : {vol:.4f} ({vol * 100:.2f}%)")
    print(f"  Confidence std       : {float(pred_std[0]):.6f}")
    print(f"  Risk level           : {lstm.calculate_risk_level(vol)}")

    return lstm, history


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    model, hist = train_model()
