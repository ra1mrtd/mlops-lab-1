import argparse
from pathlib import Path

import mlflow
import mlflow.pytorch
import torch
from torch import nn, optim
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms


ROOT = Path(__file__).resolve().parents[2]

mlflow.set_tracking_uri("http://127.0.0.1:5000")
mlflow.set_experiment("food11")


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dataset",
        choices=["processed", "mini"],
        default="mini",
    )
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--batch-size", type=int, default=32)

    return parser.parse_args()


def get_data_loaders(dataset_name, batch_size):
    if dataset_name == "mini":
        data_root = ROOT / "data" / "food11_processed_mini"
    else:
        data_root = ROOT / "data" / "food11_processed"

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])

    train_dataset = datasets.ImageFolder(
        data_root / "training",
        transform=transform,
    )

    val_dataset = datasets.ImageFolder(
        data_root / "validation",
        transform=transform,
    )

    test_dataset = datasets.ImageFolder(
        data_root / "evaluation",
        transform=transform,
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
    )

    return train_loader, val_loader, test_loader


def evaluate(model, loader, criterion, device):
    model.eval()

    total_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)

            total_loss += loss.item() * images.size(0)

            predictions = outputs.argmax(dim=1)
            correct += (predictions == labels).sum().item()
            total += labels.size(0)

    avg_loss = total_loss / total
    accuracy = correct / total

    return avg_loss, accuracy


def main():
    args = parse_args()

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print(f"Using device: {device}")

    train_loader, val_loader, test_loader = get_data_loaders(
        args.dataset,
        args.batch_size,
    )

    model = models.resnet18(
        weights=models.ResNet18_Weights.DEFAULT
    )

    model.fc = nn.Linear(
        model.fc.in_features,
        11,
    )

    model = model.to(device)

    criterion = nn.CrossEntropyLoss()

    optimizer = optim.Adam(
        model.parameters(),
        lr=args.lr,
    )

    with mlflow.start_run():

        mlflow.log_params({
            "dataset": args.dataset,
            "epochs": args.epochs,
            "lr": args.lr,
            "batch_size": args.batch_size,
            "model": "resnet18",
        })

        for epoch in range(args.epochs):
            model.train()

            running_loss = 0.0
            total_train = 0

            for images, labels in train_loader:
                images = images.to(device)
                labels = labels.to(device)

                optimizer.zero_grad()

                outputs = model(images)

                loss = criterion(outputs, labels)

                loss.backward()
                optimizer.step()

                running_loss += loss.item() * images.size(0)
                total_train += labels.size(0)

            train_loss = running_loss / total_train

            val_loss, val_accuracy = evaluate(
                model,
                val_loader,
                criterion,
                device,
            )

            mlflow.log_metric(
                "train_loss",
                train_loss,
                step=epoch,
            )

            mlflow.log_metric(
                "val_loss",
                val_loss,
                step=epoch,
            )

            mlflow.log_metric(
                "val_accuracy",
                val_accuracy,
                step=epoch,
            )

            print(
                f"Epoch {epoch + 1}/{args.epochs} | "
                f"train_loss={train_loss:.4f} | "
                f"val_loss={val_loss:.4f} | "
                f"val_accuracy={val_accuracy:.4f}"
            )

        _, test_accuracy = evaluate(
            model,
            test_loader,
            criterion,
            device,
        )

        mlflow.log_metric(
            "test_accuracy",
            test_accuracy,
        )

        mlflow.pytorch.log_model(
            model,
            name="model",
            serialization_format="pickle",
        )

        print(f"Test accuracy: {test_accuracy:.4f}")


if __name__ == "__main__":
    main()