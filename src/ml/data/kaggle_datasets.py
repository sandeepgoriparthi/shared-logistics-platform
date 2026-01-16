"""
Kaggle Dataset Downloader and Preprocessor

Downloads and processes the best datasets for training ML models:

1. Transportation and Logistics Tracking Dataset
2. Supply Chain Shipment Pricing Dataset
3. Brazilian E-Commerce (Olist) - Logistics data
4. US Domestic Flights - For transportation patterns
5. NYC Taxi Data - For demand forecasting patterns

Setup:
    pip install kaggle
    # Create ~/.kaggle/kaggle.json with your API credentials
    # Get credentials from: https://www.kaggle.com/settings/account
"""
import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import structlog
import zipfile
import json

logger = structlog.get_logger()


# Best datasets for freight/logistics ML
RECOMMENDED_DATASETS = {
    "supply_chain_shipment": {
        "kaggle_id": "datasetengineer/logistics-and-supply-chain-dataset",
        "description": "Supply chain logistics with shipment details, costs, and delivery times",
        "use_cases": ["pricing", "demand_forecasting", "delivery_prediction"],
        "size_mb": 50
    },
    "transportation_tracking": {
        "kaggle_id": "nicolemachado/transportation-and-logistics-tracking-dataset",
        "description": "Transportation tracking with routes, delays, and performance metrics",
        "use_cases": ["route_optimization", "delay_prediction", "carrier_performance"],
        "size_mb": 30
    },
    "brazilian_ecommerce": {
        "kaggle_id": "olistbr/brazilian-ecommerce",
        "description": "100K orders with delivery data, locations, and freight values",
        "use_cases": ["demand_forecasting", "pricing", "geographic_patterns"],
        "size_mb": 45
    },
    "smart_logistics": {
        "kaggle_id": "ziya07/smart-logistics-supply-chain-dataset",
        "description": "Smart logistics with IoT-style tracking data",
        "use_cases": ["real_time_optimization", "inventory_management"],
        "size_mb": 25
    },
    "shipping_data": {
        "kaggle_id": "nayanack/shipping",
        "description": "Global shipping dynamics and port-to-port data",
        "use_cases": ["pricing", "route_planning", "market_analysis"],
        "size_mb": 40
    },
    "cargo_2000": {
        "kaggle_id": "crawford/cargo-2000-dataset",
        "description": "Air cargo shipment tracking with detailed milestones",
        "use_cases": ["delay_prediction", "performance_monitoring"],
        "size_mb": 100
    }
}


class KaggleDatasetManager:
    """
    Manages downloading and preprocessing of Kaggle datasets
    """

    def __init__(self, data_dir: str = "data/kaggle"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir = self.data_dir / "processed"
        self.processed_dir.mkdir(exist_ok=True)

        # Check Kaggle credentials
        self._check_kaggle_credentials()

    def _check_kaggle_credentials(self):
        """Check if Kaggle credentials are configured"""
        kaggle_json = Path.home() / ".kaggle" / "kaggle.json"

        if not kaggle_json.exists():
            logger.warning(
                "kaggle_credentials_missing",
                message="Create ~/.kaggle/kaggle.json with your API credentials"
            )
            print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                    KAGGLE SETUP INSTRUCTIONS                          ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  1. Go to https://www.kaggle.com/settings/account                    ║
║  2. Click "Create New Token" under API section                        ║
║  3. Save the downloaded kaggle.json to:                               ║
║     - Linux/Mac: ~/.kaggle/kaggle.json                               ║
║     - Windows: C:\\Users\\<username>\\.kaggle\\kaggle.json              ║
║  4. Run: chmod 600 ~/.kaggle/kaggle.json (Linux/Mac)                 ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
            """)

    def download_dataset(self, dataset_key: str) -> Optional[Path]:
        """
        Download a dataset from Kaggle

        Args:
            dataset_key: Key from RECOMMENDED_DATASETS

        Returns:
            Path to downloaded data directory
        """
        if dataset_key not in RECOMMENDED_DATASETS:
            logger.error("unknown_dataset", key=dataset_key)
            return None

        dataset_info = RECOMMENDED_DATASETS[dataset_key]
        kaggle_id = dataset_info["kaggle_id"]
        output_dir = self.data_dir / dataset_key

        try:
            import kaggle

            logger.info("downloading_dataset", dataset=kaggle_id)

            kaggle.api.dataset_download_files(
                kaggle_id,
                path=str(output_dir),
                unzip=True
            )

            logger.info("dataset_downloaded", path=str(output_dir))
            return output_dir

        except ImportError:
            logger.error("kaggle_not_installed", message="Run: pip install kaggle")
            return None
        except Exception as e:
            logger.error("download_failed", dataset=kaggle_id, error=str(e))
            return None

    def download_all_datasets(self) -> Dict[str, Path]:
        """Download all recommended datasets"""
        results = {}

        for key in RECOMMENDED_DATASETS:
            path = self.download_dataset(key)
            if path:
                results[key] = path

        return results

    def get_dataset_info(self) -> List[Dict]:
        """Get information about recommended datasets"""
        return [
            {"key": k, **v}
            for k, v in RECOMMENDED_DATASETS.items()
        ]


class FreightDataPreprocessor:
    """
    Preprocesses freight/logistics data for ML model training
    """

    def __init__(self, data_dir: str = "data/kaggle"):
        self.data_dir = Path(data_dir)
        self.processed_dir = self.data_dir / "processed"
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def preprocess_supply_chain(self, input_path: Path) -> pd.DataFrame:
        """
        Preprocess supply chain dataset for pricing and demand models

        Expected columns: origin, destination, weight, cost, delivery_time, etc.
        """
        # Find CSV files in directory
        csv_files = list(input_path.glob("*.csv"))
        if not csv_files:
            logger.warning("no_csv_files", path=str(input_path))
            return pd.DataFrame()

        df = pd.read_csv(csv_files[0])

        # Standardize column names
        df.columns = df.columns.str.lower().str.replace(" ", "_")

        # Common preprocessing
        df = self._clean_dataframe(df)

        # Feature engineering for freight
        if "weight" in df.columns:
            df["weight_category"] = pd.cut(
                df["weight"],
                bins=[0, 500, 2000, 10000, 45000],
                labels=["LTL_small", "LTL_large", "partial", "FTL"]
            )

        if "delivery_time" in df.columns or "delivery_days" in df.columns:
            time_col = "delivery_time" if "delivery_time" in df.columns else "delivery_days"
            df["on_time"] = df[time_col] <= df[time_col].median()

        # Save processed
        output_path = self.processed_dir / "supply_chain_processed.parquet"
        df.to_parquet(output_path, index=False)

        logger.info("preprocessed_supply_chain", rows=len(df), path=str(output_path))
        return df

    def preprocess_brazilian_ecommerce(self, input_path: Path) -> pd.DataFrame:
        """
        Preprocess Brazilian E-commerce (Olist) dataset

        Great for demand forecasting and geographic patterns
        """
        # Load relevant tables
        orders_path = input_path / "olist_orders_dataset.csv"
        items_path = input_path / "olist_order_items_dataset.csv"
        geo_path = input_path / "olist_geolocation_dataset.csv"

        if not orders_path.exists():
            logger.warning("olist_data_not_found", path=str(input_path))
            return pd.DataFrame()

        orders = pd.read_csv(orders_path)
        items = pd.read_csv(items_path)

        # Merge orders with items
        df = orders.merge(items, on="order_id", how="left")

        # Parse dates
        date_cols = [col for col in df.columns if "date" in col or "timestamp" in col]
        for col in date_cols:
            df[col] = pd.to_datetime(df[col], errors="coerce")

        # Calculate delivery metrics
        if "order_delivered_customer_date" in df.columns and "order_purchase_timestamp" in df.columns:
            df["delivery_days"] = (
                df["order_delivered_customer_date"] - df["order_purchase_timestamp"]
            ).dt.days

        # Feature engineering
        if "order_purchase_timestamp" in df.columns:
            df["day_of_week"] = df["order_purchase_timestamp"].dt.dayofweek
            df["month"] = df["order_purchase_timestamp"].dt.month
            df["hour"] = df["order_purchase_timestamp"].dt.hour

        # Clean and save
        df = self._clean_dataframe(df)
        output_path = self.processed_dir / "brazilian_ecommerce_processed.parquet"
        df.to_parquet(output_path, index=False)

        logger.info("preprocessed_brazilian_ecommerce", rows=len(df))
        return df

    def preprocess_transportation_tracking(self, input_path: Path) -> pd.DataFrame:
        """
        Preprocess transportation tracking dataset

        Good for route optimization and delay prediction
        """
        csv_files = list(input_path.glob("*.csv"))
        if not csv_files:
            return pd.DataFrame()

        df = pd.read_csv(csv_files[0])
        df.columns = df.columns.str.lower().str.replace(" ", "_")

        # Standardize location columns
        location_cols = [col for col in df.columns if any(
            x in col for x in ["origin", "destination", "from", "to", "pickup", "delivery"]
        )]

        # Parse timestamps
        time_cols = [col for col in df.columns if any(
            x in col for x in ["time", "date", "timestamp", "eta", "actual"]
        )]
        for col in time_cols:
            df[col] = pd.to_datetime(df[col], errors="coerce")

        # Calculate delays if possible
        if "scheduled_delivery" in df.columns and "actual_delivery" in df.columns:
            df["delay_hours"] = (
                df["actual_delivery"] - df["scheduled_delivery"]
            ).dt.total_seconds() / 3600
            df["is_delayed"] = df["delay_hours"] > 0

        df = self._clean_dataframe(df)
        output_path = self.processed_dir / "transportation_tracking_processed.parquet"
        df.to_parquet(output_path, index=False)

        logger.info("preprocessed_transportation_tracking", rows=len(df))
        return df

    def create_training_datasets(self) -> Dict[str, pd.DataFrame]:
        """
        Create unified training datasets for each ML model

        Returns:
            Dictionary with datasets for each model type
        """
        datasets = {}

        # Load all processed data
        processed_files = list(self.processed_dir.glob("*.parquet"))

        if not processed_files:
            logger.warning("no_processed_data", message="Run preprocessing first")
            return datasets

        all_data = []
        for f in processed_files:
            try:
                df = pd.read_parquet(f)
                df["source"] = f.stem
                all_data.append(df)
            except Exception as e:
                logger.error("load_failed", file=str(f), error=str(e))

        if not all_data:
            return datasets

        # Combine all data
        combined = pd.concat(all_data, ignore_index=True)

        # Create model-specific datasets
        # 1. Pricing Model Dataset
        pricing_cols = [col for col in combined.columns if any(
            x in col.lower() for x in ["price", "cost", "rate", "freight", "distance", "weight"]
        )]
        if pricing_cols:
            datasets["pricing"] = combined[pricing_cols].dropna()

        # 2. Demand Forecasting Dataset
        demand_cols = [col for col in combined.columns if any(
            x in col.lower() for x in ["date", "time", "volume", "count", "quantity", "order"]
        )]
        if demand_cols:
            datasets["demand"] = combined[demand_cols].dropna()

        # 3. Delay Prediction Dataset
        delay_cols = [col for col in combined.columns if any(
            x in col.lower() for x in ["delay", "late", "time", "scheduled", "actual", "eta"]
        )]
        if delay_cols:
            datasets["delay"] = combined[delay_cols].dropna()

        # Save training datasets
        for name, df in datasets.items():
            output_path = self.processed_dir / f"training_{name}.parquet"
            df.to_parquet(output_path, index=False)
            logger.info("created_training_dataset", name=name, rows=len(df))

        return datasets

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize a dataframe"""
        # Remove duplicates
        df = df.drop_duplicates()

        # Handle missing values
        # For numeric columns, fill with median
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            df[col] = df[col].fillna(df[col].median())

        # For categorical columns, fill with mode
        cat_cols = df.select_dtypes(include=["object", "category"]).columns
        for col in cat_cols:
            if df[col].mode().any():
                df[col] = df[col].fillna(df[col].mode()[0])

        # Remove outliers (values beyond 3 standard deviations)
        for col in numeric_cols:
            mean = df[col].mean()
            std = df[col].std()
            df = df[(df[col] >= mean - 3*std) & (df[col] <= mean + 3*std)]

        return df

    def generate_synthetic_freight_data(
        self,
        num_samples: int = 100000
    ) -> pd.DataFrame:
        """
        Generate synthetic freight data for training when real data is limited

        Creates realistic freight shipment data based on industry patterns
        """
        np.random.seed(42)

        # US major freight corridors
        corridors = [
            ("Los Angeles", "CA", "Chicago", "IL", 2015),
            ("Los Angeles", "CA", "Dallas", "TX", 1435),
            ("Chicago", "IL", "Atlanta", "GA", 720),
            ("Dallas", "TX", "Atlanta", "GA", 780),
            ("Seattle", "WA", "Los Angeles", "CA", 1135),
            ("Houston", "TX", "Atlanta", "GA", 790),
            ("New York", "NY", "Chicago", "IL", 790),
            ("Phoenix", "AZ", "Denver", "CO", 600),
            ("Memphis", "TN", "Chicago", "IL", 530),
            ("Nashville", "TN", "Atlanta", "GA", 250),
        ]

        data = []

        for _ in range(num_samples):
            # Select corridor
            corridor = corridors[np.random.randint(0, len(corridors))]
            origin_city, origin_state, dest_city, dest_state, base_distance = corridor

            # Add variation to distance
            distance = base_distance * np.random.uniform(0.9, 1.1)

            # Weight distribution (bimodal: LTL and FTL)
            if np.random.random() < 0.6:
                weight = np.random.uniform(500, 15000)  # LTL
                linear_feet = weight / 700  # Rough estimate
            else:
                weight = np.random.uniform(20000, 45000)  # FTL
                linear_feet = np.random.uniform(40, 53)

            # Base rate varies by market
            base_rate = np.random.uniform(2.00, 3.50)

            # Adjustments
            fuel_surcharge = base_rate * 0.15
            demand_multiplier = 1 + np.random.uniform(-0.2, 0.3)

            # Calculate price
            rate_per_mile = base_rate * demand_multiplier
            total_cost = distance * rate_per_mile + fuel_surcharge * distance

            # Time features
            day_of_week = np.random.randint(0, 7)
            month = np.random.randint(1, 13)
            hour = np.random.randint(6, 20)

            # Delivery time (based on distance + handling)
            transit_hours = distance / 50 + np.random.uniform(4, 12)
            is_delayed = np.random.random() < 0.08  # 8% delay rate

            if is_delayed:
                actual_transit = transit_hours * np.random.uniform(1.1, 1.5)
            else:
                actual_transit = transit_hours * np.random.uniform(0.9, 1.05)

            # Pooling potential
            pooling_probability = 0.3 + 0.4 * (linear_feet / 53)  # Higher for partial loads

            data.append({
                "origin_city": origin_city,
                "origin_state": origin_state,
                "destination_city": dest_city,
                "destination_state": dest_state,
                "distance_miles": distance,
                "weight_lbs": weight,
                "linear_feet": linear_feet,
                "base_rate_per_mile": base_rate,
                "fuel_surcharge": fuel_surcharge,
                "total_cost": total_cost,
                "rate_per_mile": rate_per_mile,
                "day_of_week": day_of_week,
                "month": month,
                "hour": hour,
                "scheduled_transit_hours": transit_hours,
                "actual_transit_hours": actual_transit,
                "is_delayed": is_delayed,
                "pooling_probability": pooling_probability,
                "equipment_type": np.random.choice(["dry_van", "reefer", "flatbed"], p=[0.75, 0.20, 0.05])
            })

        df = pd.DataFrame(data)

        # Save
        output_path = self.processed_dir / "synthetic_freight_data.parquet"
        df.to_parquet(output_path, index=False)

        logger.info("generated_synthetic_data", rows=len(df), path=str(output_path))
        return df


def download_and_prepare_all_data():
    """Download and prepare all datasets for ML training"""
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                KAGGLE DATASET DOWNLOAD & PREPARATION                  ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  Recommended Datasets:                                                ║
║  1. Supply Chain Shipment Data - Pricing & demand                     ║
║  2. Transportation Tracking - Route optimization                      ║
║  3. Brazilian E-commerce (Olist) - Geographic patterns                ║
║  4. Cargo 2000 - Delay prediction                                     ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
    """)

    manager = KaggleDatasetManager()
    preprocessor = FreightDataPreprocessor()

    # Show available datasets
    print("\nAvailable Datasets:")
    for info in manager.get_dataset_info():
        print(f"  - {info['key']}: {info['description']}")
        print(f"    Kaggle: {info['kaggle_id']}")
        print(f"    Use cases: {', '.join(info['use_cases'])}")
        print()

    # Generate synthetic data as baseline
    print("\nGenerating synthetic freight data as baseline...")
    synthetic_df = preprocessor.generate_synthetic_freight_data(100000)
    print(f"Generated {len(synthetic_df)} synthetic samples")

    return {
        "synthetic": synthetic_df,
        "manager": manager,
        "preprocessor": preprocessor
    }


if __name__ == "__main__":
    download_and_prepare_all_data()
