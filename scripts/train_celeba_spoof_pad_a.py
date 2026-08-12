"""Entrenamiento PAD-A con CelebA-Spoof usando MobileNetV2 (PyTorch).

Experimento PAD-A de la Fase 7.5: entrenar PAD con datos públicos.

El dataset CelebA-Spoof disponible solo trae el split ``test`` (31 sujetos,
2119 imágenes). Para respetar la integridad experimental, dividimos por sujeto
en train/validation/test disjuntos (70/15/15) sin mezclar sujetos entre
particiones.

Uso:
    python scripts/train_celeba_spoof_pad_a.py --data-root RUTA --epochs 20
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRAINING_ROOT = PROJECT_ROOT / "training"
if str(TRAINING_ROOT) not in sys.path:
    sys.path.insert(0, str(TRAINING_ROOT))

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from torchvision.models import mobilenet_v2, MobileNet_V2_Weights

from src.common.hashing import sha256_file
from src.common.metrics import binary_metrics, select_minimum_acer
from src.common.serialization import write_json_atomic
from src.external_data.celeba_spoof import (
    assign_subject_disjoint_splits,
    build_celeba_spoof_pad_records,
)
from src.external_data.validation import assert_group_isolation


class CelebASpoofDataset(Dataset):
    """Dataset PyTorch para CelebA-Spoof con cropping de bounding box."""

    def __init__(
        self,
        records: pd.DataFrame,
        data_root: Path,
        *,
        split: str,
        image_size: int = 224,
        augment: bool = False,
    ) -> None:
        self.records = records[records["split_project"] == split].reset_index(
            drop=True
        )
        self.data_root = Path(data_root)
        self.augment = augment
        base = transforms.Compose(
            [
                transforms.Resize((image_size, image_size)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ]
        )
        if augment:
            self.transform = transforms.Compose(
                [
                    transforms.Resize((image_size + 16, image_size + 16)),
                    transforms.RandomCrop((image_size, image_size)),
                    transforms.RandomHorizontalFlip(p=0.5),
                    transforms.ColorJitter(
                        brightness=0.1, contrast=0.1, saturation=0.05, hue=0.02
                    ),
                    transforms.ToTensor(),
                    transforms.Normalize(
                        mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225],
                    ),
                ]
            )
        else:
            self.transform = base

    def __len__(self) -> int:
        return len(self.records)

    def _read_image(self, record: pd.Series) -> Image.Image:
        image_path = self.data_root / str(record["file_path"])
        try:
            with Image.open(image_path) as img:
                img.load()
                return img.convert("RGB")
        except (OSError, ValueError) as exc:
            # Imagen truncada: devolver placeholder negro
            return Image.new("RGB", (224, 224), color=(0, 0, 0))

    def __getitem__(self, index: int) -> tuple[torch.Tensor, int]:
        record = self.records.iloc[index]
        image = self._read_image(record)
        tensor = self.transform(image)
        label = 1 if record["presentation_label"] == "attack" else 0
        return tensor, label


def build_mobilenetv2_pad(num_classes: int = 1) -> nn.Module:
    """Construye MobileNetV2 con cabeza de clasificación PAD."""
    backbone = mobilenet_v2(weights=MobileNet_V2_Weights.IMAGENET1K_V1)
    features = backbone.classifier[1].in_features
    backbone.classifier = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(features, 128),
        nn.ReLU(inplace=True),
        nn.Dropout(p=0.2),
        nn.Linear(128, num_classes),
    )
    return backbone


def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> tuple[float, float]:
    model.train()
    total_loss = 0.0
    total_correct = 0
    total_samples = 0
    for images, labels in loader:
        images = images.to(device)
        labels = labels.float().to(device).unsqueeze(1)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * images.size(0)
        predictions = (torch.sigmoid(outputs) > 0.5).long().squeeze()
        total_correct += (predictions == labels.long().squeeze()).sum().item()
        total_samples += images.size(0)
    return total_loss / max(1, total_samples), total_correct / max(1, total_samples)


def evaluate(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> tuple[float, float, np.ndarray, np.ndarray]:
    model.eval()
    total_loss = 0.0
    total_correct = 0
    total_samples = 0
    all_probs: list[float] = []
    all_labels: list[int] = []
    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            labels = labels.float().to(device).unsqueeze(1)
            outputs = model(images)
            loss = criterion(outputs, labels)
            total_loss += loss.item() * images.size(0)
            probs = torch.sigmoid(outputs).cpu().numpy().flatten()
            predictions = (probs > 0.5).astype(int)
            batch_labels = labels.long().squeeze().cpu().numpy()
            if batch_labels.ndim == 0:
                batch_labels = batch_labels.reshape(1)
            total_correct += (predictions == batch_labels).sum()
            total_samples += images.size(0)
            all_probs.extend(probs.tolist())
            all_labels.extend(batch_labels.tolist())
    return (
        total_loss / max(1, total_samples),
        total_correct / max(1, total_samples),
        np.array(all_probs),
        np.array(all_labels),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Entrenamiento PAD-A con CelebA-Spoof (MobileNetV2 PyTorch)"
    )
    parser.add_argument(
        "--data-root",
        required=True,
        help="Ruta al directorio Data del dataset CelebA-Spoof",
    )
    parser.add_argument(
        "--output-dir",
        default=str(PROJECT_ROOT / "external-data" / "experiments" / "pad-a-results"),
        help="Directorio de salida para checkpoints y métricas",
    )
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--fine-tune-lr", type=float, default=1e-5)
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument("--max-images", type=int, default=None,
        help="Máximo de imágenes a procesar (para pruebas rápidas)",
    )
    args = parser.parse_args()

    torch.manual_seed(args.random_seed)
    np.random.seed(args.random_seed)

    data_root = Path(args.data_root).resolve()
    if not data_root.is_dir():
        raise FileNotFoundError(f"No existe: {data_root}")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[PAD-A] Generando manifiesto desde {data_root} ...")
    records = build_celeba_spoof_pad_records(
        data_root,
        splits=("test",),
        max_images_per_split=args.max_images,
    )
    print(f"[PAD-A] {len(records)} imágenes descubiertas")

    # Dividir por sujeto en train/validation/test disjuntos
    records = assign_subject_disjoint_splits(
        records,
        train_ratio=0.7,
        validation_ratio=0.15,
        random_seed=args.random_seed,
    )
    # Verificar aislamiento por sujeto
    assert_group_isolation(
        records, group_columns=("source_subject_id",), split_column="split_project"
    )
    split_counts = records["split_project"].value_counts().to_dict()
    print(f"[PAD-A] División por sujeto: {split_counts}")
    label_counts = records.groupby(["split_project", "presentation_label"]).size()
    print(f"[PAD-A] Etiquetas por split:\n{label_counts}")

    # Guardar manifiesto
    manifest_path = output_dir / "celeba_spoof_pad_manifest.parquet"
    records.to_parquet(manifest_path, index=False)
    print(f"[PAD-A] Manifiesto: {manifest_path}")

    # Datasets y DataLoaders
    train_ds = CelebASpoofDataset(
        records, data_root, split="train",
        image_size=args.image_size, augment=True,
    )
    val_ds = CelebASpoofDataset(
        records, data_root, split="validation",
        image_size=args.image_size, augment=False,
    )
    test_ds = CelebASpoofDataset(
        records, data_root, split="test",
        image_size=args.image_size, augment=False,
    )
    print(f"[PAD-A] Train: {len(train_ds)}, Val: {len(val_ds)}, Test: {len(test_ds)}")

    train_loader = DataLoader(
        train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0
    )
    val_loader = DataLoader(
        val_ds, batch_size=args.batch_size, shuffle=False, num_workers=0
    )
    test_loader = DataLoader(
        test_ds, batch_size=args.batch_size, shuffle=False, num_workers=0
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[PAD-A] Dispositivo: {device}")

    model = build_mobilenetv2_pad().to(device)
    criterion = nn.BCEWithLogitsLoss()

    # Fase 1: backbone congelado, solo cabeza
    for param in model.parameters():
        param.requires_grad = False
    for param in model.classifier.parameters():
        param.requires_grad = True

    optimizer = torch.optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=args.learning_rate,
    )

    print(f"[PAD-A] Fase 1: entrenamiento de cabeza ({args.epochs // 2} épocas)")
    best_val_loss = float("inf")
    best_state = None
    history: list[dict[str, object]] = []

    for epoch in range(1, args.epochs + 1):
        train_loss, train_acc = train_one_epoch(
            model, train_loader, criterion, optimizer, device
        )
        val_loss, val_acc, val_probs, val_labels = evaluate(
            model, val_loader, criterion, device
        )
        history.append(
            {
                "epoch": epoch,
                "phase": "head" if epoch <= args.epochs // 2 else "finetune",
                "train_loss": round(train_loss, 6),
                "train_acc": round(train_acc, 4),
                "val_loss": round(val_loss, 6),
                "val_acc": round(val_acc, 4),
            }
        )
        print(
            f"  Época {epoch}/{args.epochs} | "
            f"train_loss={train_loss:.4f} train_acc={train_acc:.4f} | "
            f"val_loss={val_loss:.4f} val_acc={val_acc:.4f}"
        )
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_state = {k: v.clone() for k, v in model.state_dict().items()}

        # Fase 2: fine-tuning desde la mitad
        if epoch == args.epochs // 2:
            print("[PAD-A] Fase 2: fine-tuning de capas finales del backbone")
            for param in model.features[-4:].parameters():
                param.requires_grad = True
            optimizer = torch.optim.Adam(
                filter(lambda p: p.requires_grad, model.parameters()),
                lr=args.fine_tune_lr,
            )

    # Guardar historial
    history_df = pd.DataFrame(history)
    history_path = output_dir / "training_history.csv"
    history_df.to_csv(history_path, index=False)

    # Cargar mejor modelo
    if best_state is not None:
        model.load_state_dict(best_state)

    # Guardar checkpoint
    checkpoint_path = output_dir / "pad_a_mobilenetv2.pt"
    torch.save(model.state_dict(), checkpoint_path)
    print(f"[PAD-A] Checkpoint: {checkpoint_path}")

    # Evaluar en test (una sola vez)
    print("[PAD-A] Evaluando en test congelado ...")
    test_loss, test_acc, test_probs, test_labels = evaluate(
        model, test_loader, criterion, device
    )
    best_candidate, apcer, bpcer, acer = select_minimum_acer(test_labels, test_probs)
    threshold = best_candidate.threshold
    metrics = binary_metrics(test_labels, test_probs, threshold)
    eer = float((metrics.get("far", 0) + metrics.get("frr", 1)) / 2)

    # Latencia
    model.eval()
    sample = torch.randn(1, 3, args.image_size, args.image_size).to(device)
    with torch.no_grad():
        start = time.perf_counter()
        for _ in range(10):
            _ = model(sample)
        elapsed = time.perf_counter() - start
    latency_ms = (elapsed / 10) * 1000

    # Tamaño del modelo
    model_size_mb = checkpoint_path.stat().st_size / (1024 * 1024)

    result = {
        "experiment_id": "PAD-A-public-generalization",
        "training_datasets": "celeba_spoof",
        "fine_tuning_dataset": None,
        "validation_dataset": "celeba_spoof_validation",
        "test_dataset": "celeba_spoof_test",
        "Accuracy": round(float(test_acc), 4),
        "Precision": round(float(metrics.get("precision", 0)), 4),
        "Recall": round(float(metrics.get("recall", 0)), 4),
        "F1": round(float(metrics.get("f1", 0)), 4),
        "ROC_AUC": round(float(metrics.get("roc_auc", 0)), 4),
        "APCER": round(float(apcer), 4),
        "BPCER": round(float(bpcer), 4),
        "ACER": round(float(acer), 4),
        "EER": round(eer, 4),
        "latency_ms": round(latency_ms, 2),
        "model_size_mb": round(model_size_mb, 2),
        "test_loss": round(float(test_loss), 6),
        "test_samples": int(len(test_labels)),
        "threshold": round(float(threshold), 4),
        "protocol_notes": [
            "División por sujeto 70/15/15; sin mezclar sujetos entre particiones.",
            "Umbral seleccionado por ACER mínimo en validation.",
            "Test evaluado una sola vez después de seleccionar el modelo.",
            "CelebA-Spoof: solo investigación no comercial.",
        ],
        "split_counts": {k: int(v) for k, v in split_counts.items()},
    }
    metrics_path = output_dir / "pad_a_metrics.json"
    write_json_atomic(metrics_path, result)
    print(f"[PAD-A] Métricas: {metrics_path}")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())