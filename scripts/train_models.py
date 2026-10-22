"""Script to train, evaluate, and save HeatSense ML model artifacts."""

import logging
from pathlib import Path

from heatsense_ml.training.trainer import run_training_and_evaluation

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train_script")


def main():
    logger.info("Starting HeatSense Model Training Pipeline (Stage 3)...")
    weather_path = Path("data/processed/pilot_weather.parquet")
    artifacts_dir = Path("artifacts/models/v1")

    if not weather_path.exists():
        raise FileNotFoundError(
            f"Missing processed dataset: {weather_path}. Run generate_pilot_data.py first."
        )

    # Using sample_stride=3 (182 grid cells across Mumbai, Pune, Western Ghats, ~800k rows)
    # for rapid, bounded, high-quality training and held-out evaluation
    run_training_and_evaluation(
        weather_parquet_path=weather_path,
        artifacts_dir=artifacts_dir,
        sample_stride=3,
    )
    logger.info("Training complete! Model artifacts saved to %s", artifacts_dir)


if __name__ == "__main__":
    main()
