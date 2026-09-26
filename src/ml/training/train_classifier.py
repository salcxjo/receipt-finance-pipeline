"""Training pipeline for the line-item category classifier (NFR-4: >=85% held-out accuracy).

Usage (once implemented):
    python -m src.ml.training.train_classifier --data data/processed/labeled_items.csv

Pipeline stages, kept as separate functions so each is unit-testable without
a GPU or real dataset:
  1. load_dataset      - read labeled examples (description -> category)
  2. build_features    - text -> vector (start with TF-IDF; swap for a small
                          transformer embedding once there's enough data)
  3. train              - fit a classifier (start with scikit-learn
                          LogisticRegression/SVM as a strong simple baseline
                          before reaching for a neural net)
  4. evaluate           - held-out accuracy/F1, confusion matrix
  5. export             - save the model + a model_versions DB row (see
                          db/models.py) so every prediction is traceable to
                          the model that made it
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


@dataclass
class TrainingResult:
    pipeline: Pipeline
    report: str
    accuracy: float


def load_dataset(csv_path: Path) -> pd.DataFrame:
    """Expects columns: description, category."""
    df = pd.read_csv(csv_path)
    missing = {"description", "category"} - set(df.columns)
    if missing:
        raise ValueError(f"dataset missing required columns: {missing}")
    return df


def train(df: pd.DataFrame, random_state: int = 42) -> TrainingResult:
    X_train, X_test, y_train, y_test = train_test_split(
        df["description"], df["category"], test_size=0.2, random_state=random_state, stratify=df["category"]
    )

    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2)),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    report = classification_report(y_test, y_pred)
    accuracy = (y_pred == y_test).mean()

    return TrainingResult(pipeline=pipeline, report=report, accuracy=accuracy)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("data/models/classifier.joblib"))
    args = parser.parse_args()

    df = load_dataset(args.data)
    result = train(df)

    print(result.report)
    print(f"Held-out accuracy: {result.accuracy:.3f}")

    if result.accuracy < 0.85:
        print("WARNING: accuracy below NFR-4 target (0.85) — do not deploy this model.")

    import joblib

    args.out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(result.pipeline, args.out)
    print(f"Saved model to {args.out}")


if __name__ == "__main__":
    main()
