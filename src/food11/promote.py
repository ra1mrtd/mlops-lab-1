import argparse
import math
import os

import mlflow
from mlflow import MlflowClient

MODEL_NAME = "food11"


def get_test_size() -> int:
    test_dir = "data/food11_processed_mini/evaluation"

    count = 0

    for root, _, files in os.walk(test_dir):
        count += len(
            [
                name
                for name in files
                if name.lower().endswith(
                    (".jpg", ".jpeg", ".png")
                )
            ]
        )

    if count == 0:
        raise RuntimeError(
            "Could not determine evaluation split size."
        )

    return count


def get_accuracy(client: MlflowClient, run_id: str) -> float:
    run = client.get_run(run_id)

    metrics = run.data.metrics

    if "test_accuracy" not in metrics:
        raise RuntimeError(
            f"Run {run_id} has no test_accuracy metric."
        )

    return metrics["test_accuracy"]


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--version",
        type=int,
        required=True,
        help="Candidate model version",
    )

    args = parser.parse_args()

    tracking_uri = os.getenv(
        "MLFLOW_TRACKING_URI",
        "http://127.0.0.1:5000",
    )

    mlflow.set_tracking_uri(tracking_uri)

    client = MlflowClient()

    candidate = client.get_model_version(
        MODEL_NAME,
        str(args.version),
    )

    candidate_accuracy = get_accuracy(
        client,
        candidate.run_id,
    )

    champion = client.get_model_version_by_alias(
        MODEL_NAME,
        "champion",
    )

    champion_accuracy = get_accuracy(
        client,
        champion.run_id,
    )

    n = get_test_size()

    se = math.sqrt(
        champion_accuracy
        * (1 - champion_accuracy)
        / n
    )

    threshold = champion_accuracy + 2 * se

    print(f"Candidate version: {args.version}")
    print(f"Candidate accuracy: {candidate_accuracy:.4f}")
    print(f"Champion version: {champion.version}")
    print(f"Champion accuracy: {champion_accuracy:.4f}")
    print(f"Test size: {n}")
    print(f"2 * SE: {2 * se:.4f}")
    print(f"Promotion threshold: {threshold:.4f}")

    if candidate_accuracy >= threshold:
        decision = "promoted_to_champion"

        client.set_registered_model_alias(
            MODEL_NAME,
            "champion",
            args.version,
        )

        print("Decision: PROMOTE -> champion")

    else:
        decision = "assigned_as_challenger"

        client.set_registered_model_alias(
            MODEL_NAME,
            "challenger",
            args.version,
        )

        print("Decision: KEEP champion; candidate -> challenger")

    client.set_model_version_tag(
        MODEL_NAME,
        str(args.version),
        "promotion_decision",
        decision,
    )

    client.set_model_version_tag(
        MODEL_NAME,
        str(args.version),
        "candidate_accuracy",
        f"{candidate_accuracy:.6f}",
    )

    client.set_model_version_tag(
        MODEL_NAME,
        str(args.version),
        "champion_accuracy",
        f"{champion_accuracy:.6f}",
    )

    client.set_model_version_tag(
        MODEL_NAME,
        str(args.version),
        "promotion_threshold",
        f"{threshold:.6f}",
    )

    client.set_model_version_tag(
        MODEL_NAME,
        str(args.version),
        "test_size",
        str(n),
    )


if __name__ == "__main__":
    main()