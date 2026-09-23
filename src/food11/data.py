from pathlib import Path
from PIL import Image
import shutil

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = ROOT / "data" / "food11_raw"
PROCESSED_DIR = ROOT / "data" / "food11_processed"
MINI_DIR = ROOT / "data" / "food11_processed_mini"

IMAGE_SIZE = (128, 128)
MINI_LIMIT = 100

CLASS_NAMES = {
    "0": "Bread",
    "1": "Dairy product",
    "2": "Dessert",
    "3": "Egg",
    "4": "Fried food",
    "5": "Meat",
    "6": "Noodles-Pasta",
    "7": "Rice",
    "8": "Seafood",
    "9": "Soup",
    "10": "Vegetable-Fruit",
}

SPLITS = ["training", "evaluation", "validation"]


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def get_class_name(filename: str) -> str:
    """
    Food-11 filenames start with the class number.
    Example:
        0_123.jpg -> Bread
        10_45.jpg -> Vegetable-Fruit
    """
    class_id = filename.split("_")[0]

    if class_id not in CLASS_NAMES:
        raise ValueError(f"Unknown class ID {class_id} in file {filename}")

    return CLASS_NAMES[class_id]


def process_image(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)

    try:
        with Image.open(src) as img:
            img = img.convert("RGB")
            img = img.resize(IMAGE_SIZE)
            img.save(dst, quality=90)

    except Exception as e:
        print(f"Skipping {src}: {e}")


# --------------------------------------------------
# FULL PROCESSED DATASET
# --------------------------------------------------

def create_processed_dataset():
    print("\nCreating food11_processed...")

    if PROCESSED_DIR.exists():
        shutil.rmtree(PROCESSED_DIR)

    for split in SPLITS:
        source_split = RAW_DIR / split

        if not source_split.exists():
            raise FileNotFoundError(
                f"Missing folder: {source_split}"
            )

        files = [
            p for p in source_split.iterdir()
            if p.is_file()
        ]

        print(f"{split}: {len(files)} images")

        for i, src in enumerate(files, start=1):
            class_name = get_class_name(src.name)

            dst = (
                PROCESSED_DIR
                / split
                / class_name
                / src.name
            )

            process_image(src, dst)

            if i % 500 == 0:
                print(f"  processed {i}/{len(files)}")


# --------------------------------------------------
# MINI DATASET
# --------------------------------------------------

def create_mini_dataset():
    print("\nCreating food11_processed_mini...")

    if MINI_DIR.exists():
        shutil.rmtree(MINI_DIR)

    for split in SPLITS:

        for class_name in CLASS_NAMES.values():
            source_class = (
                PROCESSED_DIR
                / split
                / class_name
            )

            destination_class = (
                MINI_DIR
                / split
                / class_name
            )

            destination_class.mkdir(
                parents=True,
                exist_ok=True
            )

            files = sorted(
                [
                    p for p in source_class.iterdir()
                    if p.is_file()
                ]
            )

            selected = files[:MINI_LIMIT]

            for src in selected:
                shutil.copy2(
                    src,
                    destination_class / src.name
                )

            print(
                f"{split:12} | "
                f"{class_name:20} | "
                f"{len(selected)} images"
            )


# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":

    print("=" * 60)
    print("FOOD-11 DATA PREPARATION")
    print("=" * 60)

    create_processed_dataset()
    create_mini_dataset()

    print("\nDone.")
    print(f"Processed dataset: {PROCESSED_DIR}")
    print(f"Mini dataset:      {MINI_DIR}")