import os
from typing import Optional, Dict, Any


class PatchTSTTrainer:
    def __init__(self, context_length: int = 32, prediction_length: int = 12, num_features: int = 8):
        self.context_length = context_length
        self.prediction_length = prediction_length
        self.num_features = num_features
        self.available = False
        try:
            import torch  # noqa
            from transformers import PatchTSTConfig, PatchTSTForPrediction  # noqa
            self.available = True
        except Exception:
            self.available = False

    def train(self, csv_path: str, target_column: str, feature_columns: list[str], save_dir: str = "models/patchtst") -> Dict[str, Any]:
        if not self.available:
            return {"status": "unavailable", "reason": "transformers or torch not installed"}
        import pandas as pd
        import torch
        from torch.utils.data import Dataset, DataLoader
        from transformers import PatchTSTConfig, PatchTSTForPrediction

        df = pd.read_csv(csv_path)
        for c in [target_column] + feature_columns:
            if c not in df.columns:
                return {"status": "error", "reason": f"missing column {c}"}

        class TSData(Dataset):
            def __init__(self, data, ctx, pred, feats, tgt):
                self.X = []
                self.Y = []
                vals = data[feats + [tgt]].values.astype('float32')
                n = len(vals)
                L = ctx + pred
                for i in range(n - L):
                    past = vals[i:i+ctx, :len(feats)]
                    future = vals[i+ctx:i+L, len(feats):]
                    self.X.append(past)
                    self.Y.append(future)
            def __len__(self):
                return len(self.X)
            def __getitem__(self, idx):
                x = torch.tensor(self.X[idx])
                y = torch.tensor(self.Y[idx])
                return x, y

        ds = TSData(df, self.context_length, self.prediction_length, feature_columns, target_column)
        if len(ds) == 0:
            return {"status": "error", "reason": "not enough rows for sliding window"}
        dl = DataLoader(ds, batch_size=32, shuffle=True)
        cfg = PatchTSTConfig(num_input_channels=len(feature_columns), context_length=self.context_length, prediction_length=self.prediction_length, num_targets=1)
        model = PatchTSTForPrediction(cfg)
        model.train()
        opt = torch.optim.Adam(model.parameters(), lr=1e-3)
        loss_fn = torch.nn.MSELoss()
        for _ in range(3):
            for xb, yb in dl:
                past_values = xb.transpose(0,1)
                future_values = yb.transpose(0,1)
                out = model(past_values=past_values, future_values=future_values)
                loss = out.loss if hasattr(out, 'loss') and out.loss is not None else loss_fn(out.prediction_outputs, future_values)
                opt.zero_grad()
                loss.backward()
                opt.step()
        os.makedirs(save_dir, exist_ok=True)
        torch.save(model.state_dict(), os.path.join(save_dir, "patchtst.pt"))
        return {"status": "ok", "samples": len(ds)}

