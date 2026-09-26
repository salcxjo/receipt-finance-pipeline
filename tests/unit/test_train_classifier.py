import pandas as pd

from src.ml.training.train_classifier import load_dataset, train


def _synthetic_df() -> pd.DataFrame:
    rows = []
    groceries = ["milk 2%", "bread white", "bananas", "eggs dozen", "cheddar cheese"]
    dining = ["latte grande", "burger combo", "sushi roll", "pizza slice", "iced tea"]
    for item in groceries * 4:
        rows.append({"description": item, "category": "groceries"})
    for item in dining * 4:
        rows.append({"description": item, "category": "dining"})
    return pd.DataFrame(rows)


def test_train_produces_reasonable_accuracy_on_separable_data() -> None:
    df = _synthetic_df()
    result = train(df)

    # groceries vs. dining vocab barely overlaps, so this should be easy
    assert result.accuracy > 0.8


def test_load_dataset_rejects_missing_columns(tmp_path) -> None:
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("foo,bar\n1,2\n")

    try:
        load_dataset(bad_csv)
        raised = False
    except ValueError:
        raised = True

    assert raised
