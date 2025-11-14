import os
from typing import Dict, Any


class DeepLOBTrainer:
    def __init__(self, window: int = 100, features: int = 40, num_classes: int = 3):
        self.window = window
        self.features = features
        self.num_classes = num_classes
        try:
            import torch  # noqa
            self.available = True
        except Exception:
            self.available = False

    def train(self, npz_path: str, save_dir: str = "models/deeplob") -> Dict[str, Any]:
        if not self.available:
            return {"status": "unavailable", "reason": "torch not installed"}
        import numpy as np
        import torch
        import torch.nn as nn
        from torch.utils.data import Dataset, DataLoader

        data = np.load(npz_path)
        X = data.get('X')
        y = data.get('y')
        if X is None or y is None:
            return {"status": "error", "reason": "npz missing X/y"}
        class LobDS(Dataset):
            def __init__(self, X, y):
                self.X = X.astype('float32')
                self.y = y.astype('int64')
            def __len__(self):
                return len(self.X)
            def __getitem__(self, idx):
                return torch.tensor(self.X[idx]), torch.tensor(self.y[idx])
        ds = LobDS(X, y)
        dl = DataLoader(ds, batch_size=64, shuffle=True)
        class Net(nn.Module):
            def __init__(self):
                super().__init__()
                self.conv1 = nn.Conv2d(1, 16, (3, 2), padding=(1,0))
                self.conv2 = nn.Conv2d(16, 32, (3, 2), padding=(1,0))
                self.fc = nn.Linear(32 * self.window * (self.features//4), 64)
                self.head = nn.Linear(64, self.num_classes)
            def forward(self, x):
                x = x.unsqueeze(1)
                x = torch.relu(self.conv1(x))
                x = torch.relu(self.conv2(x))
                x = torch.flatten(x, 1)
                x = torch.relu(self.fc(x))
                return self.head(x)
        net = Net()
        opt = torch.optim.Adam(net.parameters(), lr=1e-3)
        loss_fn = nn.CrossEntropyLoss()
        net.train()
        for _ in range(3):
            for xb, yb in dl:
                out = net(xb)
                loss = loss_fn(out, yb)
                opt.zero_grad(); loss.backward(); opt.step()
        os.makedirs(save_dir, exist_ok=True)
        torch.save(net.state_dict(), os.path.join(save_dir, "deeplob.pt"))
        return {"status": "ok", "samples": len(ds)}

