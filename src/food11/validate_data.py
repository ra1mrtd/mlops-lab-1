import argparse
import hashlib
import sys
from pathlib import Path

from PIL import Image

EXPECTED_CLASSES = {
    "Bread",
    "Dairy product",
    "Dessert",
    "Egg",
    "Fried food",
    "Meat",
    "Noodles-Pasta",
    "Rice",
    "Seafood",
    "Soup",
    "Vegetable-Fruit",
}

SPLITS = ["training", "validation", "evaluation"]


def md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def validate_dataset(dataset_dir: Path, min_per_class: int, tau: float) -> bool:
    checks = []
    split_counts = {}
    # 1. Check class folders
    class_folders_ok = True

    for split in SPLITS:
        split_dir = dataset_dir / split

        if not split_dir.exists():
            class_folders_ok = False
            continue

        found = {
            p.name
            for p in split_dir.iterdir()
            if p.is_dir()
        }

        if found != EXPECTED_CLASSES:
            class_folders_ok = False

    checks.append(("class folders", class_folders_ok))

    # 2. Check image validity, mode and size
    image_check_ok = True

    for split in SPLITS:
        split_dir = dataset_dir / split

        if not split_dir.exists():
            image_check_ok = False
            continue

        for path in split_dir.rglob("*"):
            if not path.is_file():
                continue

            try:
                with Image.open(path) as img:
                    if img.mode != "RGB":
                        image_check_ok = False

                    if img.size != (128, 128):
                        image_check_ok = False

            except (OSError, ValueError):
                image_check_ok = False

    checks.append(("images valid RGB 128x128", image_check_ok))

    # 3. Minimum samples per class
    min_count_ok = True

    for split in SPLITS:
        split_counts[split] = {}

        for class_name in EXPECTED_CLASSES:
            class_dir = dataset_dir / split / class_name

            count = (
                len([p for p in class_dir.iterdir() if p.is_file()])
                if class_dir.exists()
                else 0
            )

            split_counts[split][class_name] = count

            if count < min_per_class:
                min_count_ok = False

    checks.append(
        (
            f"at least {min_per_class} images per class",
            min_count_ok,
        )
    )

    # 4. Check duplicates across splits
    duplicate_ok = True
    hash_locations = {}

    for split in SPLITS:
        split_dir = dataset_dir / split

        for path in split_dir.rglob("*"):
            if not path.is_file():
                continue

            digest = md5(path)

            hash_locations.setdefault(digest, []).append(
                (split, path)
            )

    duplicate_groups = []

    for locations in hash_locations.values():
        splits_present = {split for split, _ in locations}

        if len(splits_present) > 1:
            duplicate_ok = False
            duplicate_groups.append(locations)

    checks.append(("no cross-split duplicates", duplicate_ok))

    if duplicate_groups:
        print("\nCross-split duplicates found:")

        for group in duplicate_groups:
            print("-" * 50)

            for split, path in group:
                print(f"{split:10} | {path}")

    # 5. Check class distribution similarity
    distribution_ok = True

    train_total = sum(split_counts["training"].values())
    val_total = sum(split_counts["validation"].values())

    for class_name in EXPECTED_CLASSES:
        train_share = (
            split_counts["training"][class_name] / train_total
            if train_total
            else 0
        )

        val_share = (
            split_counts["validation"][class_name] / val_total
            if val_total
            else 0
        )

        if abs(train_share - val_share) > tau:
            distribution_ok = False

    checks.append(
        (
            f"training/validation distribution within tau={tau}",
            distribution_ok,
        )
    )

    print("\nDATA VALIDATION REPORT")
    print("-" * 50)

    all_passed = True

    for name, passed in checks:
        status = "PASS" if passed else "FAIL"
        print(f"{status:4} | {name}")

        if not passed:
            all_passed = False

    return all_passed


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "dataset_dir",
        type=Path,
    )

    parser.add_argument(
        "--min-per-class",
        type=int,
        default=50,
    )

    parser.add_argument(
        "--tau",
        type=float,
        default=0.05,
    )

    args = parser.parse_args()

    passed = validate_dataset(
        args.dataset_dir,
        args.min_per_class,
        args.tau,
    )

    if not passed:
        sys.exit(1)


if __name__ == "__main__":
    main()