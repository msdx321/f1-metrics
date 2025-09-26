"""Teammate comparison metrics."""

import pandas as pd
import numpy as np
from typing import Optional, List, Union
from backend.metrics.base import DriverMetric, MetricResult
from backend.data.loader import data_loader
from backend.data.cache import metric_cache
import logging

logger = logging.getLogger(__name__)


class TeammateQualifyingComparison(DriverMetric):
    """Compare driver's qualifying performance against teammates."""

    def __init__(self):
        super().__init__(
            name="teammate_qualifying_comparison",
            description="Head-to-head qualifying record against teammates"
        )

    def get_required_data(self) -> List[str]:
        return ["qualifying.csv", "results.csv", "races.csv", "drivers.csv"]

    def calculate(
        self,
        driver_id: Optional[int] = None,
        constructor_id: Optional[int] = None,
        season: Optional[int] = None,
        race_ids: Optional[List[int]] = None,
        **kwargs
    ) -> Union[MetricResult, List[MetricResult]]:
        """Calculate teammate qualifying comparison."""
        if not driver_id:
            raise ValueError("driver_id is required for teammate comparison")

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
            results = data_loader.get_results(race_ids_filtered)

            # Get driver's qualifying results
            driver_qualifying = qualifying[qualifying["driverId"] == driver_id]

            if driver_qualifying.empty:
                result = MetricResult(
                    metric_name=self.name,
                    value=None,
                    driver_id=driver_id,
                    season=season,
                    metadata={"message": "No qualifying data found for driver"}
                )
            else:
                # Find teammate comparisons
                comparisons = []
                for _, driver_qual in driver_qualifying.iterrows():
                    race_id = driver_qual["raceId"]
                    constructor_id_race = driver_qual["constructorId"]

                    # Find teammate in same race and constructor
                    race_qualifying = qualifying[qualifying["raceId"] == race_id]
                    teammate_qualifying = race_qualifying[
                        (race_qualifying["constructorId"] == constructor_id_race) &
                        (race_qualifying["driverId"] != driver_id)
                    ]

                    if not teammate_qualifying.empty and not pd.isna(driver_qual["position"]):
                        teammate_qual = teammate_qualifying.iloc[0]
                        if not pd.isna(teammate_qual["position"]):
                            driver_pos = driver_qual["position"]
                            teammate_pos = teammate_qual["position"]

                            comparisons.append({
                                "race_id": race_id,
                                "driver_position": driver_pos,
                                "teammate_id": teammate_qual["driverId"],
                                "teammate_position": teammate_pos,
                                "driver_better": driver_pos < teammate_pos
                            })

                if not comparisons:
                    result = MetricResult(
                        metric_name=self.name,
                        value=None,
                        driver_id=driver_id,
                        season=season,
                        metadata={"message": "No valid teammate comparisons found"}
                    )
                else:
                    comp_df = pd.DataFrame(comparisons)
                    wins = comp_df["driver_better"].sum()
                    total = len(comp_df)
                    win_rate = (wins / total * 100) if total > 0 else 0

                    # Get driver name
                    drivers = data_loader.get_drivers()
                    driver_row = drivers[drivers["driverId"] == driver_id]
                    driver_name = None
                    if not driver_row.empty:
                        driver_name = f"{driver_row.iloc[0]['forename']} {driver_row.iloc[0]['surname']}"

                    # Get teammate names
                    teammate_stats = {}
                    for teammate_id in comp_df["teammate_id"].unique():
                        teammate_comparisons = comp_df[comp_df["teammate_id"] == teammate_id]
                        teammate_row = drivers[drivers["driverId"] == teammate_id]
                        teammate_name = "Unknown"
                        if not teammate_row.empty:
                            teammate_name = f"{teammate_row.iloc[0]['forename']} {teammate_row.iloc[0]['surname']}"

                        teammate_wins = teammate_comparisons["driver_better"].sum()
                        teammate_total = len(teammate_comparisons)
                        teammate_stats[teammate_name] = {
                            "wins": int(teammate_wins),
                            "total": int(teammate_total),
                            "win_rate": round((teammate_wins / teammate_total * 100), 2) if teammate_total > 0 else 0
                        }

                    result = MetricResult(
                        metric_name=self.name,
                        value={
                            "overall_win_rate": round(win_rate, 2),
                            "wins": int(wins),
                            "total": int(total),
                            "losses": int(total - wins),
                            "record": f"{wins}-{total - wins}",
                            "teammate_breakdown": teammate_stats
                        },
                        driver_id=driver_id,
                        driver_name=driver_name,
                        season=season,
                        metadata={
                            "total_comparisons": int(total),
                            "unique_teammates": len(comp_df["teammate_id"].unique())
                        }
                    )

            metric_cache.set(self.name, result, **cache_key)
            return result

        except Exception as e:
            logger.error(f"Error calculating {self.name}: {e}")
            raise


class TeammateRaceComparison(DriverMetric):
    """Compare driver's race performance against teammates."""

    def __init__(self):
        super().__init__(
            name="teammate_race_comparison",
            description="Head-to-head race finishing record against teammates"
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
        """Calculate teammate race comparison."""
        if not driver_id:
            raise ValueError("driver_id is required for teammate comparison")

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

            # Get driver's race results
            driver_results = results[results["driverId"] == driver_id]

            if driver_results.empty:
                result = MetricResult(
                    metric_name=self.name,
                    value=None,
                    driver_id=driver_id,
                    season=season,
                    metadata={"message": "No race results found for driver"}
                )
            else:
                # Find teammate comparisons
                comparisons = []
                for _, driver_result in driver_results.iterrows():
                    race_id = driver_result["raceId"]
                    constructor_id_race = driver_result["constructorId"]

                    # Find teammate in same race and constructor
                    race_results = results[results["raceId"] == race_id]
                    teammate_results = race_results[
                        (race_results["constructorId"] == constructor_id_race) &
                        (race_results["driverId"] != driver_id)
                    ]

                    if not teammate_results.empty:
                        teammate_result = teammate_results.iloc[0]

                        # Handle DNFs - if both DNF, compare by laps completed
                        driver_pos = driver_result["positionOrder"]
                        teammate_pos = teammate_result["positionOrder"]

                        driver_better = None
                        if pd.isna(driver_pos) or driver_pos == 0:
                            if pd.isna(teammate_pos) or teammate_pos == 0:
                                # Both DNF, compare laps
                                driver_laps = driver_result["laps"]
                                teammate_laps = teammate_result["laps"]
                                if driver_laps != teammate_laps:
                                    driver_better = driver_laps > teammate_laps
                            else:
                                # Driver DNF, teammate finished
                                driver_better = False
                        else:
                            if pd.isna(teammate_pos) or teammate_pos == 0:
                                # Driver finished, teammate DNF
                                driver_better = True
                            else:
                                # Both finished
                                driver_better = driver_pos < teammate_pos

                        if driver_better is not None:
                            comparisons.append({
                                "race_id": race_id,
                                "driver_position": driver_pos if not pd.isna(driver_pos) else "DNF",
                                "teammate_id": teammate_result["driverId"],
                                "teammate_position": teammate_pos if not pd.isna(teammate_pos) else "DNF",
                                "driver_better": driver_better
                            })

                if not comparisons:
                    result = MetricResult(
                        metric_name=self.name,
                        value=None,
                        driver_id=driver_id,
                        season=season,
                        metadata={"message": "No valid teammate race comparisons found"}
                    )
                else:
                    comp_df = pd.DataFrame(comparisons)
                    wins = comp_df["driver_better"].sum()
                    total = len(comp_df)
                    win_rate = (wins / total * 100) if total > 0 else 0

                    # Get driver name
                    drivers = data_loader.get_drivers()
                    driver_row = drivers[drivers["driverId"] == driver_id]
                    driver_name = None
                    if not driver_row.empty:
                        driver_name = f"{driver_row.iloc[0]['forename']} {driver_row.iloc[0]['surname']}"

                    # Get teammate stats
                    teammate_stats = {}
                    for teammate_id in comp_df["teammate_id"].unique():
                        teammate_comparisons = comp_df[comp_df["teammate_id"] == teammate_id]
                        teammate_row = drivers[drivers["driverId"] == teammate_id]
                        teammate_name = "Unknown"
                        if not teammate_row.empty:
                            teammate_name = f"{teammate_row.iloc[0]['forename']} {teammate_row.iloc[0]['surname']}"

                        teammate_wins = teammate_comparisons["driver_better"].sum()
                        teammate_total = len(teammate_comparisons)
                        teammate_stats[teammate_name] = {
                            "wins": int(teammate_wins),
                            "total": int(teammate_total),
                            "win_rate": round((teammate_wins / teammate_total * 100), 2) if teammate_total > 0 else 0
                        }

                    result = MetricResult(
                        metric_name=self.name,
                        value={
                            "overall_win_rate": round(win_rate, 2),
                            "wins": int(wins),
                            "total": int(total),
                            "losses": int(total - wins),
                            "record": f"{wins}-{total - wins}",
                            "teammate_breakdown": teammate_stats
                        },
                        driver_id=driver_id,
                        driver_name=driver_name,
                        season=season,
                        metadata={
                            "total_comparisons": int(total),
                            "unique_teammates": len(comp_df["teammate_id"].unique())
                        }
                    )

            metric_cache.set(self.name, result, **cache_key)
            return result

        except Exception as e:
            logger.error(f"Error calculating {self.name}: {e}")
            raise