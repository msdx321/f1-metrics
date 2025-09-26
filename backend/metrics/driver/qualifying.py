"""Driver qualifying performance metrics."""

import pandas as pd
import numpy as np
from typing import Optional, List, Union
from backend.metrics.base import DriverMetric, MetricResult
from backend.data.loader import data_loader
from backend.data.cache import metric_cache
import logging

logger = logging.getLogger(__name__)


class QualifyingPositionAverage(DriverMetric):
    """Calculate driver's average qualifying position."""

    def __init__(self):
        super().__init__(
            name="qualifying_position_average",
            description="Average qualifying position across selected races"
        )

    def get_required_data(self) -> List[str]:
        return ["qualifying.csv", "races.csv", "drivers.csv"]

    def calculate(
        self,
        driver_id: Optional[int] = None,
        constructor_id: Optional[int] = None,
        season: Optional[int] = None,
        race_ids: Optional[List[int]] = None,
        **kwargs
    ) -> Union[MetricResult, List[MetricResult]]:
        """Calculate average qualifying position."""
        # Check cache first
        cache_key = {
            'driver_id': driver_id,
            'constructor_id': constructor_id,
            'season': season,
            'race_ids': race_ids
        }
        cached_result = metric_cache.get(self.name, **cache_key)
        if cached_result is not None:
            return cached_result

        try:
            # Get qualifying data
            races = data_loader.get_races(season)
            race_ids_filtered = race_ids or races["raceId"].tolist()
            qualifying = data_loader.get_qualifying(race_ids_filtered)

            if driver_id:
                qualifying = qualifying[qualifying["driverId"] == driver_id]

            if constructor_id:
                qualifying = qualifying[qualifying["constructorId"] == constructor_id]

            if qualifying.empty:
                result = MetricResult(
                    metric_name=self.name,
                    value=None,
                    driver_id=driver_id,
                    constructor_id=constructor_id,
                    season=season,
                    metadata={"message": "No qualifying data found"}
                )
            else:
                # Calculate average position (excluding non-qualified)
                valid_positions = qualifying[qualifying["position"].notna()]
                avg_position = valid_positions["position"].mean()

                # Get driver name if single driver
                driver_name = None
                if driver_id:
                    drivers = data_loader.get_drivers()
                    driver_row = drivers[drivers["driverId"] == driver_id]
                    if not driver_row.empty:
                        driver_name = f"{driver_row.iloc[0]['forename']} {driver_row.iloc[0]['surname']}"

                result = MetricResult(
                    metric_name=self.name,
                    value=round(avg_position, 2) if not pd.isna(avg_position) else None,
                    driver_id=driver_id,
                    driver_name=driver_name,
                    constructor_id=constructor_id,
                    season=season,
                    metadata={
                        "total_qualifyings": len(qualifying),
                        "valid_positions": len(valid_positions),
                        "best_position": int(valid_positions["position"].min()) if not valid_positions.empty else None,
                        "worst_position": int(valid_positions["position"].max()) if not valid_positions.empty else None
                    }
                )

            # Cache result
            metric_cache.set(self.name, result, **cache_key)
            return result

        except Exception as e:
            logger.error(f"Error calculating {self.name}: {e}")
            raise


class QualifyingConsistency(DriverMetric):
    """Calculate driver's qualifying consistency (standard deviation of positions)."""

    def __init__(self):
        super().__init__(
            name="qualifying_consistency",
            description="Standard deviation of qualifying positions (lower is more consistent)"
        )

    def get_required_data(self) -> List[str]:
        return ["qualifying.csv", "races.csv", "drivers.csv"]

    def calculate(
        self,
        driver_id: Optional[int] = None,
        constructor_id: Optional[int] = None,
        season: Optional[int] = None,
        race_ids: Optional[List[int]] = None,
        **kwargs
    ) -> Union[MetricResult, List[MetricResult]]:
        """Calculate qualifying consistency."""
        cache_key = {
            'driver_id': driver_id,
            'constructor_id': constructor_id,
            'season': season,
            'race_ids': race_ids
        }
        cached_result = metric_cache.get(self.name, **cache_key)
        if cached_result is not None:
            return cached_result

        try:
            races = data_loader.get_races(season)
            race_ids_filtered = race_ids or races["raceId"].tolist()
            qualifying = data_loader.get_qualifying(race_ids_filtered)

            if driver_id:
                qualifying = qualifying[qualifying["driverId"] == driver_id]

            if constructor_id:
                qualifying = qualifying[qualifying["constructorId"] == constructor_id]

            if qualifying.empty:
                result = MetricResult(
                    metric_name=self.name,
                    value=None,
                    driver_id=driver_id,
                    constructor_id=constructor_id,
                    season=season,
                    metadata={"message": "No qualifying data found"}
                )
            else:
                # Calculate consistency (std dev of positions)
                valid_positions = qualifying[qualifying["position"].notna()]
                consistency = valid_positions["position"].std()

                # Get driver name if single driver
                driver_name = None
                if driver_id:
                    drivers = data_loader.get_drivers()
                    driver_row = drivers[drivers["driverId"] == driver_id]
                    if not driver_row.empty:
                        driver_name = f"{driver_row.iloc[0]['forename']} {driver_row.iloc[0]['surname']}"

                result = MetricResult(
                    metric_name=self.name,
                    value=round(consistency, 2) if not pd.isna(consistency) else None,
                    driver_id=driver_id,
                    driver_name=driver_name,
                    constructor_id=constructor_id,
                    season=season,
                    metadata={
                        "total_qualifyings": len(qualifying),
                        "valid_positions": len(valid_positions),
                        "position_range": int(valid_positions["position"].max() - valid_positions["position"].min()) if len(valid_positions) > 0 else None
                    }
                )

            metric_cache.set(self.name, result, **cache_key)
            return result

        except Exception as e:
            logger.error(f"Error calculating {self.name}: {e}")
            raise


class PolePositionRate(DriverMetric):
    """Calculate driver's pole position rate."""

    def __init__(self):
        super().__init__(
            name="pole_position_rate",
            description="Percentage of qualifying sessions resulting in pole position"
        )

    def get_required_data(self) -> List[str]:
        return ["qualifying.csv", "races.csv", "drivers.csv"]

    def calculate(
        self,
        driver_id: Optional[int] = None,
        constructor_id: Optional[int] = None,
        season: Optional[int] = None,
        race_ids: Optional[List[int]] = None,
        **kwargs
    ) -> Union[MetricResult, List[MetricResult]]:
        """Calculate pole position rate."""
        cache_key = {
            'driver_id': driver_id,
            'constructor_id': constructor_id,
            'season': season,
            'race_ids': race_ids
        }
        cached_result = metric_cache.get(self.name, **cache_key)
        if cached_result is not None:
            return cached_result

        try:
            races = data_loader.get_races(season)
            race_ids_filtered = race_ids or races["raceId"].tolist()
            qualifying = data_loader.get_qualifying(race_ids_filtered)

            if driver_id:
                qualifying = qualifying[qualifying["driverId"] == driver_id]

            if constructor_id:
                qualifying = qualifying[qualifying["constructorId"] == constructor_id]

            if qualifying.empty:
                result = MetricResult(
                    metric_name=self.name,
                    value=None,
                    driver_id=driver_id,
                    constructor_id=constructor_id,
                    season=season,
                    metadata={"message": "No qualifying data found"}
                )
            else:
                # Calculate pole position rate
                valid_qualifying = qualifying[qualifying["position"].notna()]
                poles = valid_qualifying[valid_qualifying["position"] == 1]
                pole_rate = (len(poles) / len(valid_qualifying) * 100) if len(valid_qualifying) > 0 else 0

                # Get driver name if single driver
                driver_name = None
                if driver_id:
                    drivers = data_loader.get_drivers()
                    driver_row = drivers[drivers["driverId"] == driver_id]
                    if not driver_row.empty:
                        driver_name = f"{driver_row.iloc[0]['forename']} {driver_row.iloc[0]['surname']}"

                result = MetricResult(
                    metric_name=self.name,
                    value=round(pole_rate, 2),
                    driver_id=driver_id,
                    driver_name=driver_name,
                    constructor_id=constructor_id,
                    season=season,
                    metadata={
                        "total_qualifyings": len(valid_qualifying),
                        "pole_positions": len(poles),
                        "pole_count": int(len(poles))
                    }
                )

            metric_cache.set(self.name, result, **cache_key)
            return result

        except Exception as e:
            logger.error(f"Error calculating {self.name}: {e}")
            raise