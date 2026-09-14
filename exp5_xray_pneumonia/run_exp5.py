from pathlib import Path
import argparse
import random
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from torch import nn
from torch.utils.data import DataLoader, random_split


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUT_DIR = BASE_DIR / "outputs"
CLASSES = ["NORMAL", "PNEUMONIA"]


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def make_model(name, pretrained):
    try:
        from torchvision import models
    except Exception as exc:
        raise SystemExit("torchvision 无法导入，请安装与 torch 匹配的 torchvision 版本。") from exc

    if name == "convnext_tiny":
        weights = models.ConvNeXt_Tiny_Weights.DEFAULT if pretrained else None
        model = models.convnext_tiny(weights=weights)
        model.classifier[2] = nn.Linear(model.classifier[2].in_features, 2)
    elif name == "efficientnet_b0":
        weights = models.EfficientNet_B0_Weights.DEFAULT if pretrained else None
        model = models.efficientnet_b0(weights=weights)
        model.classifier[1] = nn.Linear(model.classifier[1].in_features, 2)
    elif name == "resnet50":
        weights = models.ResNet50_Weights.DEFAULT if pretrained else None
        model = models.resnet50(weights=weights)
        model.fc = nn.Linear(model.fc.in_features, 2)
    else:
        raise ValueError(f"不支持的模型: {name}")
    return model


def loaders(batch_size, image_size, val_ratio, seed):
    train_dir = DATA_DIR / "train"
    val_dir = DATA_DIR / "val"
    test_dir = DATA_DIR / "test"
    if not train_dir.exists() or not test_dir.exists():
        raise SystemExit(
            "请先放入教学数据，目录应包含 train/NORMAL、train/PNEUMONIA、test/NORMAL、test/PNEUMONIA。"
        )
    try:
        from torchvision import datasets, transforms
    except Exception as exc:
        raise SystemExit("torchvision 无法导入，请安装与 torch 匹配的 torchvision 版本。") from exc

    normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    train_tf = transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(8),
            transforms.ToTensor(),
            normalize,
        ]
    )
    eval_tf = transforms.Compose([transforms.Resize((image_size, image_size)), transforms.ToTensor(), normalize])

    train_data = datasets.ImageFolder(train_dir, transform=train_tf)
    if train_data.classes != CLASSES:
        print("检测到类别:", train_data.classes)

    if val_dir.exists():
        val_data = datasets.ImageFolder(val_dir, transform=eval_tf)
    else:
        eval_data = datasets.ImageFolder(train_dir, transform=eval_tf)
        n_val = max(1, int(len(train_data) * val_ratio))
        n_train = len(train_data) - n_val
        indices = torch.randperm(len(train_data), generator=torch.Generator().manual_seed(seed)).tolist()
        train_data = torch.utils.data.Subset(train_data, indices[:n_train])
        val_data = torch.utils.data.Subset(eval_data, indices[n_train:])

    test_data = datasets.ImageFolder(test_dir, transform=eval_tf)
    return (
        DataLoader(train_data, batch_size=batch_size, shuffle=True, num_workers=0),
        DataLoader(val_data, batch_size=batch_size, shuffle=False, num_workers=0),
        DataLoader(test_data, batch_size=batch_size, shuffle=False, num_workers=0),
    )


def run_epoch(model, loader, loss_fn, optimizer, device):
    model.train()
    total = 0.0
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        optimizer.zero_grad()
        loss = loss_fn(model(x), y)
        loss.backward()
        optimizer.step()
        total += loss.item() * len(y)
    return total / len(loader.dataset)


@torch.no_grad()
def evaluate(model, loader, loss_fn, device):
    model.eval()
    total = 0.0
    ys, preds = [], []
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        logits = model(x)
        total += loss_fn(logits, y).item() * len(y)
        pred = torch.argmax(logits, dim=1)
        ys.extend(y.cpu().numpy().tolist())
        preds.extend(pred.cpu().numpy().tolist())
    return {
        "loss": total / len(loader.dataset),
        "Accuracy": accuracy_score(ys, preds),
        "Precision": precision_score(ys, preds, zero_division=0),
        "Recall": recall_score(ys, preds, zero_division=0),
        "F1": f1_score(ys, preds, zero_division=0),
        "cm": confusion_matrix(ys, preds),
        "y_true": ys,
        "y_pred": preds,
    }


def save_history(history):
    pd.DataFrame(history).to_csv(OUT_DIR / "训练过程.csv", index=False, encoding="utf-8-sig")
    plt.figure(figsize=(7, 4))
    plt.plot([x["epoch"] for x in history], [x["train_loss"] for x in history], label="train")
    plt.plot([x["epoch"] for x in history], [x["val_loss"] for x in history], label="val")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.title("Training Curve")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUT_DIR / "训练验证损失曲线.png", dpi=180)
    plt.close()


def save_predictions(model, loader, device):
    rows = []
    model.eval()
    dataset = loader.dataset.dataset if hasattr(loader.dataset, "dataset") else loader.dataset
    samples = dataset.samples
    offset = 0
    with torch.no_grad():
        for x, _ in loader:
            x = x.to(device)
            prob = torch.softmax(model(x), dim=1)[:, 1].cpu().numpy()
            pred = (prob >= 0.5).astype(int)
            for p, c in zip(prob, pred):
                path = Path(samples[offset][0]).name if offset < len(samples) else str(offset)
                rows.append({"文件名": path, "肺炎概率": round(float(p), 6), "类别预测": int(c)})
                offset += 1
    pd.DataFrame(rows).to_csv(OUT_DIR / "测试集逐样本预测.csv", index=False, encoding="utf-8-sig")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="convnext_tiny", choices=["convnext_tiny", "efficientnet_b0", "resnet50"])
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--val-ratio", type=float, default=0.2)
    parser.add_argument("--no-pretrained", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    OUT_DIR.mkdir(exist_ok=True)
    set_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    train_loader, val_loader, test_loader = loaders(args.batch_size, args.image_size, args.val_ratio, args.seed)

    model = make_model(args.model, not args.no_pretrained).to(device)
    loss_fn = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)

    history = []
    best_f1 = -1.0
    start = time.time()
    for epoch in range(1, args.epochs + 1):
        train_loss = run_epoch(model, train_loader, loss_fn, optimizer, device)
        val = evaluate(model, val_loader, loss_fn, device)
        history.append({"epoch": epoch, "train_loss": train_loss, "val_loss": val["loss"], "val_f1": val["F1"]})
        print(f"epoch {epoch}/{args.epochs} train_loss={train_loss:.4f} val_loss={val['loss']:.4f} val_f1={val['F1']:.4f}")
        if val["F1"] > best_f1:
            best_f1 = val["F1"]
            torch.save(model.state_dict(), OUT_DIR / "最佳模型权重.pt")

    model.load_state_dict(torch.load(OUT_DIR / "最佳模型权重.pt", map_location=device))
    test = evaluate(model, test_loader, loss_fn, device)
    save_history(history)
    save_predictions(model, test_loader, device)

    pd.DataFrame(
        [
            {
                "模型": args.model,
                "训练轮数": args.epochs,
                "批量大小": args.batch_size,
                "学习率": args.learning_rate,
                "设备": str(device),
                "运行秒数": round(time.time() - start, 2),
                "Accuracy": round(test["Accuracy"], 4),
                "Precision": round(test["Precision"], 4),
                "Recall": round(test["Recall"], 4),
                "F1": round(test["F1"], 4),
            }
        ]
    ).to_csv(OUT_DIR / "模型评价指标.csv", index=False, encoding="utf-8-sig")

    plt.figure(figsize=(4, 4))
    plt.imshow(test["cm"], cmap="Blues")
    plt.xticks([0, 1], CLASSES, rotation=20)
    plt.yticks([0, 1], CLASSES)
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.title("Confusion Matrix")
    for i in range(2):
        for j in range(2):
            plt.text(j, i, str(test["cm"][i, j]), ha="center", va="center")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "混淆矩阵.png", dpi=180)
    plt.close()

    print("实验五完成，结果已保存到:", OUT_DIR)


if __name__ == "__main__":
    main()
