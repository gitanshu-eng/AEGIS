import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

from configuration.dataset_config import (
    PROCESSED_DATA_DIR,
    CLEANED_FILE,
)


INPUT_FILE = CLEANED_FILE.replace(
    "_cleaned.csv",
    "_forecasting.csv"
)

INPUT_PATH = f"{PROCESSED_DATA_DIR}/{INPUT_FILE}"

OUTPUT_FILE = CLEANED_FILE.replace(
    "_cleaned.csv",
    "_predictions.csv"
)

OUTPUT_PATH = f"{PROCESSED_DATA_DIR}/{OUTPUT_FILE}"


def train_forecasting_model():

    print("--- AEGIS RANDOM FOREST FORECASTING ---")

    # 1. LOAD DATA
    df = pd.read_csv(INPUT_PATH)

    df["time_window"] = pd.to_datetime(
        df["time_window"]
    )

    # 2. KEEP CHRONOLOGICAL ORDER
    df = df.sort_values(
        "time_window"
    ).reset_index(drop=True)

    # 3. DEFINE FEATURES AND TARGET
    feature_columns = [
        "attack_rate_lag_1",
        "attack_rate_lag_2",
        "attack_rate_lag_3",
        "attack_rate_lag_5",
    ]

    target_column = "attack_rate"

    X = df[feature_columns]
    y = df[target_column]

    # 4. CHRONOLOGICAL SPLIT
    total_rows = len(df)

    train_end = int(total_rows * 0.70)
    validation_end = int(total_rows * 0.85)

    X_train = X.iloc[:train_end]
    y_train = y.iloc[:train_end]

    X_validation = X.iloc[train_end:validation_end]
    y_validation = y.iloc[train_end:validation_end]

    X_test = X.iloc[validation_end:]
    y_test = y.iloc[validation_end:]

    print(f"Total rows: {total_rows}")
    print(f"Training rows: {len(X_train)}")
    print(f"Validation rows: {len(X_validation)}")
    print(f"Test rows: {len(X_test)}")

    # 5. CREATE MODEL
    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42,
        n_jobs=-1
    )

    # 6. TRAIN
    print("\nTraining Random Forest...")

    model.fit(
        X_train,
        y_train
    )

    print("Training complete.")

    # 7. VALIDATION PREDICTION
    validation_prediction = model.predict(
        X_validation
    )

    validation_mae = mean_absolute_error(
        y_validation,
        validation_prediction
    )

    validation_rmse = mean_squared_error(
        y_validation,
        validation_prediction
    ) ** 0.5

    # 8. TEST PREDICTION
    test_prediction = model.predict(
        X_test
    )

    test_mae = mean_absolute_error(
        y_test,
        test_prediction
    )

    test_rmse = mean_squared_error(
        y_test,
        test_prediction
    ) ** 0.5

    # 9. SAVE TEST PREDICTIONS
    predictions = df.iloc[
        validation_end:
    ].copy()

    predictions["predicted_attack_rate"] = test_prediction

    predictions["prediction_error"] = (
        predictions["attack_rate"]
        - predictions["predicted_attack_rate"]
    )

    predictions[
        [
            "time_window",
            "attack_rate",
            "predicted_attack_rate",
            "prediction_error",
            "segment_id",
        ]
    ].to_csv(
        OUTPUT_PATH,
        index=False
    )

    # 10. RESULTS
    print("\n--- RANDOM FOREST RESULTS ---")

    print("\nValidation:")
    print(f"MAE:  {validation_mae:.6f}")
    print(f"RMSE: {validation_rmse:.6f}")

    print("\nTest:")
    print(f"MAE:  {test_mae:.6f}")
    print(f"RMSE: {test_rmse:.6f}")

    print("\nPredictions saved to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    train_forecasting_model()