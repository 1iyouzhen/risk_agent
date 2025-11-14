from typing import Dict, Any


def train_model(kind: str, params: Dict[str, Any]) -> Dict[str, Any]:
    if kind == "patchtst":
        from .models.patchtst import PatchTSTTrainer
        trainer = PatchTSTTrainer(
            context_length=int(params.get("context_length", 32)),
            prediction_length=int(params.get("prediction_length", 12)),
            num_features=int(params.get("num_features", 8))
        )
        return trainer.train(
            csv_path=params.get("csv_path", "synthetic_training.csv"),
            target_column=params.get("target_column", "target"),
            feature_columns=params.get("feature_columns", ["amount", "income", "credit_score", "delinquencies", "market_index"]),
            save_dir=params.get("save_dir", "models/patchtst")
        )
    if kind == "deeplob":
        from .models.deeplob import DeepLOBTrainer
        trainer = DeepLOBTrainer(window=int(params.get("window", 100)), features=int(params.get("features", 40)), num_classes=int(params.get("num_classes", 3)))
        return trainer.train(npz_path=params.get("npz_path", "lob_data.npz"), save_dir=params.get("save_dir", "models/deeplob"))
    return {"status": "error", "reason": "unknown kind"}

