"""Driver race performance metrics."""

import pandas as pd
import numpy as np
from typing import Optional, List, Union
from backend.metrics.base import DriverMetric, MetricResult
from backend.data.loader import data_loader
from backend.data.cache import metric_cache
import logging

logger = logging.getLogger(__name__)


class AverageFinishPosition(DriverMetric):
    """Calculate driver's average finish position."""

    def __init__(self):
        super().__init__(
            name="average_finish_position",
            description="Average race finish position (DNFs excluded from position calculation)"
        )

    def get_required_data(self) -> List[str]:
        return ["results.csv", "races.csv", "drivers.csv"]

    def calculate(
        self,
        driver_id: Optional[int] = None,
        constructor_id: Optional[int] = None,
        season: Optional[int] = None,
        race_ids: Optional[List[int]] = None,
        **kwargs
    ) -> Union[MetricResult, List[MetricResult]]:
        """Calculate average finish position."""
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
            results = data_loader.get_results(race_ids_filtered)

            if driver_id:
                results = results[results["driverId"] == driver_id]

            if constructor_id:
                results = results[results["constructorId"] == constructor_id]

            if results.empty:
                result = MetricResult(
                    metric_name=self.name,
                    value=None,
                    driver_id=driver_id,
                    constructor_id=constructor_id,
                    season=season,
                    metadata={"message": "No race results found"}
                )
            else:
                # Calculate average finish position (only classified finishes)
                finished_results = results[results["positionOrder"].notna() & (results["positionOrder"] > 0)]
                avg_position = finished_results["positionOrder"].mean()

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
                        "total_races": len(results),
                        "finished_races": len(finished_results),
                        "dnf_count": len(results) - len(finished_results),
                        "best_finish": int(finished_results["positionOrder"].min()) if not finished_results.empty else None,
                        "worst_finish": int(finished_results["positionOrder"].max()) if not finished_results.empty else None
                    }
                )

            metric_cache.set(self.name, result, **cache_key)
            return result

        except Exception as e:
            logger.error(f"Error calculating {self.name}: {e}")
            raise


class PointsPerRace(DriverMetric):
    """Calculate driver's average points per race."""

    def __init__(self):
        super().__init__(
            name="points_per_race",
            description="Average championship points scored per race"
        )

    def get_required_data(self) -> List[str]:
        return ["results.csv", "races.csv", "drivers.csv"]

    def calculate(
        self,
        driver_id: Optional[int] = None,
        constructor_id: Optional[int] = None,
        season: Optional[int] = None,
        race_ids: Optional[List[int]] = None,
        **kwargs
    ) -> Union[MetricResult, List[MetricResult]]:
        """Calculate average points per race."""
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
            results = data_loader.get_results(race_ids_filtered)

            if driver_id:
                results = results[results["driverId"] == driver_id]

            if constructor_id:
                results = results[results["constructorId"] == constructor_id]

            if results.empty:
                result = MetricResult(
                    metric_name=self.name,
                    value=None,
                    driver_id=driver_id,
                    constructor_id=constructor_id,
                    season=season,
                    metadata={"message": "No race results found"}
                )
            else:
                avg_points = results["points"].mean()
                total_points = results["points"].sum()

                # Get driver name if single driver
                driver_name = None
                if driver_id:
                    drivers = data_loader.get_drivers()
                    driver_row = drivers[drivers["driverId"] == driver_id]
                    if not driver_row.empty:
                        driver_name = f"{driver_row.iloc[0]['forename']} {driver_row.iloc[0]['surname']}"

                result = MetricResult(
                    metric_name=self.name,
                    value=round(avg_points, 2),
                    driver_id=driver_id,
                    driver_name=driver_name,
                    constructor_id=constructor_id,
                    season=season,
                    metadata={
                        "total_races": len(results),
                        "total_points": float(total_points),
                        "points_scoring_races": len(results[results["points"] > 0]),
                        "best_points_haul": float(results["points"].max())
                    }
                )

            metric_cache.set(self.name, result, **cache_key)
            return result

        except Exception as e:
            logger.error(f"Error calculating {self.name}: {e}")
            raise


class DNFRate(DriverMetric):
    """Calculate driver's Did Not Finish rate."""

    def __init__(self):
        super().__init__(
            name="dnf_rate",
            description="Percentage of races that ended in DNF (Did Not Finish)"
        )

    def get_required_data(self) -> List[str]:
        return ["results.csv", "races.csv", "drivers.csv"]

    def calculate(
        self,
        driver_id: Optional[int] = None,
        constructor_id: Optional[int] = None,
        season: Optional[int] = None,
        race_ids: Optional[List[int]] = None,
        **kwargs
    ) -> Union[MetricResult, List[MetricResult]]:
        """Calculate DNF rate."""
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
            results = data_loader.get_results(race_ids_filtered)

            if driver_id:
                results = results[results["driverId"] == driver_id]

            if constructor_id:
                results = results[results["constructorId"] == constructor_id]

            if results.empty:
                result = MetricResult(
                    metric_name=self.name,
                    value=None,
                    driver_id=driver_id,
                    constructor_id=constructor_id,
                    season=season,
                    metadata={"message": "No race results found"}
                )
            else:
                # DNF is when positionText is not a number (like "Ret", "DNF", etc.)
                dnfs = results[results["positionText"].str.contains(r'^[^\d]', na=False)]
                dnf_rate = (len(dnfs) / len(results) * 100) if len(results) > 0 else 0

                # Get driver name if single driver
                driver_name = None
                if driver_id:
                    drivers = data_loader.get_drivers()
                    driver_row = drivers[drivers["driverId"] == driver_id]
                    if not driver_row.empty:
                        driver_name = f"{driver_row.iloc[0]['forename']} {driver_row.iloc[0]['surname']}"

                result = MetricResult(
                    metric_name=self.name,
                    value=round(dnf_rate, 2),
                    driver_id=driver_id,
                    driver_name=driver_name,
                    constructor_id=constructor_id,
                    season=season,
                    metadata={
                        "total_races": len(results),
                        "dnf_count": len(dnfs),
                        "finish_rate": round(100 - dnf_rate, 2)
                    }
                )

            metric_cache.set(self.name, result, **cache_key)
            return result

        except Exception as e:
            logger.error(f"Error calculating {self.name}: {e}")
            raise


class PodiumRate(DriverMetric):
    """Calculate driver's podium rate (top 3 finishes)."""

    def __init__(self):
        super().__init__(
            name="podium_rate",
            description="Percentage of races resulting in podium finish (top 3)"
        )

    def get_required_data(self) -> List[str]:
        return ["results.csv", "races.csv", "drivers.csv"]

    def calculate(
        self,
        driver_id: Optional[int] = None,
        constructor_id: Optional[int] = None,
        season: Optional[int] = None,
        race_ids: Optional[List[int]] = None,
        **kwargs
    ) -> Union[MetricResult, List[MetricResult]]:
        """Calculate podium rate."""
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
            results = data_loader.get_results(race_ids_filtered)

            if driver_id:
                results = results[results["driverId"] == driver_id]

            if constructor_id:
                results = results[results["constructorId"] == constructor_id]

            if results.empty:
                result = MetricResult(
                    metric_name=self.name,
                    value=None,
                    driver_id=driver_id,
                    constructor_id=constructor_id,
                    season=season,
                    metadata={"message": "No race results found"}
                )
            else:
                podiums = results[results["positionOrder"] <= 3]
                podium_rate = (len(podiums) / len(results) * 100) if len(results) > 0 else 0

                # Get driver name if single driver
                driver_name = None
                if driver_id:
                    drivers = data_loader.get_drivers()
                    driver_row = drivers[drivers["driverId"] == driver_id]
                    if not driver_row.empty:
                        driver_name = f"{driver_row.iloc[0]['forename']} {driver_row.iloc[0]['surname']}"

                # Count wins, second places, third places
                wins = len(results[results["positionOrder"] == 1])
                seconds = len(results[results["positionOrder"] == 2])
                thirds = len(results[results["positionOrder"] == 3])

                result = MetricResult(
                    metric_name=self.name,
                    value=round(podium_rate, 2),
                    driver_id=driver_id,
                    driver_name=driver_name,
                    constructor_id=constructor_id,
                    season=season,
                    metadata={
                        "total_races": len(results),
                        "podium_count": len(podiums),
                        "wins": wins,
                        "second_places": seconds,
                        "third_places": thirds,
                        "win_rate": round((wins / len(results) * 100), 2) if len(results) > 0 else 0
                    }
                )

            metric_cache.set(self.name, result, **cache_key)
            return result

        except Exception as e:
            logger.error(f"Error calculating {self.name}: {e}")
            raise