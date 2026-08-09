"""
LSTM Volatility Prediction Model – Phase 2 of Stock Volatility Forecaster
===========================================================================
Bidirectional LSTM built in PyTorch that predicts annualised stock-price
volatility from multi-feature daily sequences.
"""

import logging
import os
from typing import Dict, Optional, Tuple

import joblib
import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)s  %(levelname)s  %(message)s",
)


# ---------------------------------------------------------------------------
# PyTorch network definition
# ---------------------------------------------------------------------------
class _BiLSTMNetwork(nn.Module):
    """Internal PyTorch module – Bidirectional LSTM → LSTM → Dense."""

    def __init__(
        self,
        input_size: int,
        lstm_units: int = 128,
        dropout_rate: float = 0.2,
    ) -> None:
        super().__init__()
        # Layer 1 – Bidirectional LSTM
        self.bilstm = nn.LSTM(
            input_size=input_size,
            hidden_size=lstm_units,
            batch_first=True,
            bidirectional=True,
        )
        self.drop1 = nn.Dropout(dropout_rate)

        # Layer 2 – unidirectional LSTM (input = 2 × lstm_units because of bidir)
        self.lstm2 = nn.LSTM(
            input_size=lstm_units * 2,
            hidden_size=lstm_units // 2,
            batch_first=True,
        )
        self.drop2 = nn.Dropout(dropout_rate)

        # Dense head
        self.fc1 = nn.Linear(lstm_units // 2, 64)
        self.relu1 = nn.ReLU()
        self.drop3 = nn.Dropout(dropout_rate)
        self.fc2 = nn.Linear(64, 32)
        self.relu2 = nn.ReLU()
        self.fc3 = nn.Linear(32, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # (B, T, F)
        out, _ = self.bilstm(x)      # (B, T, 2*H)
        out = self.drop1(out)
        out, _ = self.lstm2(out)      # (B, T, H/2)
        out = self.drop2(out[:, -1, :])  # last time-step  (B, H/2)
        out = self.drop3(self.relu1(self.fc1(out)))
        out = self.relu2(self.fc2(out))
        out = self.fc3(out)           # (B, 1)
        return out.squeeze(-1)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
class LSTMVolatilityPredictor:
    """Train / predict stock volatility with a Bidirectional LSTM."""

    def __init__(
        self,
        sequence_length: int = 30,
        lstm_units: int = 128,
        dropout_rate: float = 0.2,
    ) -> None:
        self.sequence_length = sequence_length
        self.lstm_units = lstm_units
        self.dropout_rate = dropout_rate

        self.model: Optional[_BiLSTMNetwork] = None
        self.scaler = MinMaxScaler()
        self.target_scaler = MinMaxScaler()
        self.is_fitted = False

        # Use GPU if available
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info("Using device: %s", self.device)

    # ----- model construction -----------------------------------------------

    def build_model(self, input_size: int) -> _BiLSTMNetwork:
        """Build and return the BiLSTM network."""
        self.model = _BiLSTMNetwork(
            input_size=input_size,
            lstm_units=self.lstm_units,
            dropout_rate=self.dropout_rate,
        ).to(self.device)

        n_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        logger.info("Model built with %s trainable parameters.", f"{n_params:,}")
        return self.model

    # ----- sequence preparation ---------------------------------------------

    def prepare_sequences(
        self,
        data: np.ndarray,
        targets: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sliding-window sequences for the LSTM.

        Args:
            data: (N, F) feature matrix.
            targets: (N,) target volatility values.

        Returns:
            ``(X, y)`` where X is ``(samples, sequence_length, F)``
            and y is ``(samples,)``.
        """
        X, y = [], []
        for i in range(self.sequence_length, len(data)):
            X.append(data[i - self.sequence_length : i])
            y.append(targets[i])
        return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)

    # ----- training ---------------------------------------------------------

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        epochs: int = 100,
        batch_size: int = 32,
        learning_rate: float = 1e-3,
        patience: int = 10,
        model_save_path: str = "models/lstm_volatility_model.pth",
    ) -> Dict:
        """
        Train the LSTM model with early stopping.

        Returns:
            ``{"train_loss": float, "val_loss": float,
              "train_losses": [...], "val_losses": [...],
              "best_epoch": int}``
        """
        input_size = X_train.shape[2]
        if self.model is None:
            self.build_model(input_size)

        # Convert to tensors
        X_tr = torch.tensor(X_train, dtype=torch.float32, device=self.device)
        y_tr = torch.tensor(y_train, dtype=torch.float32, device=self.device)
        X_v = torch.tensor(X_val, dtype=torch.float32, device=self.device)
        y_v = torch.tensor(y_val, dtype=torch.float32, device=self.device)

        optimiser = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        criterion = nn.MSELoss()

        train_dataset = torch.utils.data.TensorDataset(X_tr, y_tr)
        train_loader = torch.utils.data.DataLoader(
            train_dataset, batch_size=batch_size, shuffle=True,
        )

        best_val_loss = float("inf")
        epochs_no_improve = 0
        best_epoch = 0
        train_losses, val_losses = [], []

        os.makedirs(os.path.dirname(model_save_path) or ".", exist_ok=True)

        for epoch in range(1, epochs + 1):
            # --- train ---
            self.model.train()
            epoch_loss = 0.0
            n_batches = 0
            for xb, yb in train_loader:
                optimiser.zero_grad()
                preds = self.model(xb)
                loss = criterion(preds, yb)
                loss.backward()
                optimiser.step()
                epoch_loss += loss.item()
                n_batches += 1
            avg_train = epoch_loss / n_batches

            # --- validate ---
            self.model.eval()
            with torch.no_grad():
                val_preds = self.model(X_v)
                val_loss = criterion(val_preds, y_v).item()

            train_losses.append(avg_train)
            val_losses.append(val_loss)

            if epoch % 10 == 0 or epoch == 1:
                logger.info(
                    "Epoch %3d/%d  train_loss=%.6f  val_loss=%.6f",
                    epoch, epochs, avg_train, val_loss,
                )

            # --- early stopping + checkpoint ---
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_epoch = epoch
                epochs_no_improve = 0
                torch.save(self.model.state_dict(), model_save_path)
            else:
                epochs_no_improve += 1
                if epochs_no_improve >= patience:
                    logger.info(
                        "Early stopping at epoch %d (best=%d).", epoch, best_epoch,
                    )
                    break

        # Reload best weights
        self.model.load_state_dict(torch.load(model_save_path, weights_only=True))
        self.model.eval()
        self.is_fitted = True

        return {
            "train_loss": train_losses[best_epoch - 1],
            "val_loss": best_val_loss,
            "train_losses": train_losses,
            "val_losses": val_losses,
            "best_epoch": best_epoch,
        }

    # ----- inference --------------------------------------------------------

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Return volatility predictions for input sequences."""
        if self.model is None:
            raise RuntimeError("Model has not been built / loaded.")
        self.model.eval()
        with torch.no_grad():
            tensor = torch.tensor(X, dtype=torch.float32, device=self.device)
            preds = self.model(tensor).cpu().numpy()
        return preds

    def predict_with_confidence(
        self,
        X: np.ndarray,
        n_iterations: int = 50,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Monte Carlo Dropout: run *n_iterations* forward passes with dropout
        enabled, then return the mean and std of predictions.
        """
        if self.model is None:
            raise RuntimeError("Model has not been built / loaded.")

        self.model.train()  # enable dropout
        tensor = torch.tensor(X, dtype=torch.float32, device=self.device)

        all_preds = []
        with torch.no_grad():
            for _ in range(n_iterations):
                preds = self.model(tensor).cpu().numpy()
                all_preds.append(preds)

        self.model.eval()
        stacked = np.stack(all_preds, axis=0)  # (iters, N)
        return stacked.mean(axis=0), stacked.std(axis=0)

    # ----- risk classification ----------------------------------------------

    @staticmethod
    def calculate_risk_level(volatility: float) -> str:
        """Classify annualised volatility into a risk bucket."""
        if volatility < 0.02:
            return "LOW"
        elif volatility < 0.05:
            return "MEDIUM"
        elif volatility < 0.10:
            return "HIGH"
        else:
            return "VERY HIGH"

    # ----- persistence ------------------------------------------------------

    def save_model(self, path: str) -> None:
        """Save model weights, scalers, and config."""
        if self.model is None:
            raise RuntimeError("No model to save.")
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

        torch.save(self.model.state_dict(), path)

        meta_path = path.replace(".pth", "_meta.pkl")
        joblib.dump(
            {
                "scaler": self.scaler,
                "target_scaler": self.target_scaler,
                "sequence_length": self.sequence_length,
                "lstm_units": self.lstm_units,
                "dropout_rate": self.dropout_rate,
                "input_size": next(self.model.parameters()).shape[-1]
                if list(self.model.parameters())
                else 0,
            },
            meta_path,
        )
        logger.info("Model saved to %s", path)

    def load_model(self, path: str) -> None:
        """Load model weights, scalers, and config."""
        meta_path = path.replace(".pth", "_meta.pkl")
        meta = joblib.load(meta_path)

        self.scaler = meta["scaler"]
        self.target_scaler = meta["target_scaler"]
        self.sequence_length = meta["sequence_length"]
        self.lstm_units = meta["lstm_units"]
        self.dropout_rate = meta["dropout_rate"]

        input_size = meta.get("input_size", 8)
        self.build_model(input_size)
        self.model.load_state_dict(
            torch.load(path, map_location=self.device, weights_only=True),
        )
        self.model.eval()
        self.is_fitted = True
        logger.info("Model loaded from %s", path)
