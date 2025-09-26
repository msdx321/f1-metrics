"""Constructor qualifying performance metrics."""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from backend.metrics.base import BaseConstructorMetric, MetricResult
from backend.data.loader import data_loader


class ConstructorPolePositionRate(BaseConstructorMetric):
    """Calculate constructor pole position rate."""

    name = "constructor_pole_position_rate"
    description = "Percentage of races where constructor achieved pole position"
    unit = "percentage"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            qual_data = data_loader.get_constructor_qualifying_performance(season, constructor_id)

            if qual_data.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No qualifying data found"})

            # Group by race and find best qualifying position
            race_results = (qual_data
                           .groupby("raceId")
                           .agg({"position": "min"})
                           .reset_index())

            total_races = len(race_results)
            poles = len(race_results[race_results["position"] == 1])
            pole_rate = (poles / total_races) * 100 if total_races > 0 else 0

            return MetricResult(
                self.name, round(pole_rate, 1), constructor_id=constructor_id,
                metadata={
                    "total_races": total_races,
                    "pole_positions": poles,
                    "pole_percentage": round(pole_rate, 1)
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorAverageQualifyingPosition(BaseConstructorMetric):
    """Calculate average qualifying position of constructor's best car."""

    name = "constructor_average_qualifying_position"
    description = "Average qualifying position of constructor's best performing car per race"
    unit = "position"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            qual_data = data_loader.get_constructor_qualifying_performance(season, constructor_id)

            if qual_data.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No qualifying data found"})

            # Filter out DNS/DNQ entries
            valid_positions = qual_data[qual_data["position"].notna() & (qual_data["position"] > 0)]

            if valid_positions.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No valid qualifying positions found"})

            # Get best position per race
            race_best_positions = (valid_positions
                                  .groupby("raceId")
                                  .agg({"position": "min"})
                                  .reset_index())

            avg_position = race_best_positions["position"].mean()
            best_position = race_best_positions["position"].min()
            median_position = race_best_positions["position"].median()

            return MetricResult(
                self.name, round(avg_position, 2), constructor_id=constructor_id,
                metadata={
                    "total_races": len(race_best_positions),
                    "best_qualifying": int(best_position),
                    "median_position": float(median_position),
                    "total_qualifying_sessions": len(valid_positions)
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorQualifyingConsistency(BaseConstructorMetric):
    """Calculate qualifying consistency (standard deviation of positions)."""

    name = "constructor_qualifying_consistency"
    description = "Qualifying consistency measured by standard deviation (lower is better)"
    unit = "position_std"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            qual_data = data_loader.get_constructor_qualifying_performance(season, constructor_id)

            if qual_data.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No qualifying data found"})

            # Get valid positions
            valid_positions = qual_data[qual_data["position"].notna() & (qual_data["position"] > 0)]

            if valid_positions.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No valid qualifying positions found"})

            # Get best position per race
            race_best_positions = (valid_positions
                                  .groupby("raceId")["position"]
                                  .min()
                                  .reset_index())

            if len(race_best_positions) < 3:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "Insufficient data for consistency calculation"})

            consistency = race_best_positions["position"].std()
            position_range = race_best_positions["position"].max() - race_best_positions["position"].min()

            return MetricResult(
                self.name, round(consistency, 2), constructor_id=constructor_id,
                metadata={
                    "total_races": len(race_best_positions),
                    "position_range": int(position_range),
                    "avg_position": round(race_best_positions["position"].mean(), 2),
                    "consistency_rating": "High" if consistency < 3 else "Medium" if consistency < 6 else "Low"
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorFrontRowStartRate(BaseConstructorMetric):
    """Calculate percentage of races starting from front row."""

    name = "constructor_front_row_start_rate"
    description = "Percentage of races with at least one driver starting from front row (P1-P2)"
    unit = "percentage"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            qual_data = data_loader.get_constructor_qualifying_performance(season, constructor_id)

            if qual_data.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No qualifying data found"})

            # Group by race and check for front row starts
            race_results = (qual_data
                           .groupby("raceId")
                           .agg({"position": "min"})
                           .reset_index())

            total_races = len(race_results)
            front_row_starts = len(race_results[race_results["position"] <= 2])
            front_row_rate = (front_row_starts / total_races) * 100 if total_races > 0 else 0

            # Breakdown by position
            poles = len(race_results[race_results["position"] == 1])
            p2_starts = len(race_results[race_results["position"] == 2])

            return MetricResult(
                self.name, round(front_row_rate, 1), constructor_id=constructor_id,
                metadata={
                    "total_races": total_races,
                    "front_row_starts": front_row_starts,
                    "pole_positions": poles,
                    "p2_starts": p2_starts
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorTopTenQualifyingRate(BaseConstructorMetric):
    """Calculate percentage of races qualifying in top 10."""

    name = "constructor_top_ten_qualifying_rate"
    description = "Percentage of races with at least one driver qualifying in top 10"
    unit = "percentage"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            qual_data = data_loader.get_constructor_qualifying_performance(season, constructor_id)

            if qual_data.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No qualifying data found"})

            # Group by race and check for top 10 qualifying
            race_results = (qual_data
                           .groupby("raceId")
                           .agg({"position": "min"})
                           .reset_index())

            total_races = len(race_results)
            top_ten_quali = len(race_results[race_results["position"] <= 10])
            top_ten_rate = (top_ten_quali / total_races) * 100 if total_races > 0 else 0

            # Position breakdown
            position_breakdown = {}
            for pos_range, label in [(1, "pole"), (2, "front_row"), (5, "top_5"), (10, "top_10")]:
                count = len(race_results[race_results["position"] <= pos_range])
                position_breakdown[label] = count

            return MetricResult(
                self.name, round(top_ten_rate, 1), constructor_id=constructor_id,
                metadata={
                    "total_races": total_races,
                    "top_ten_qualifying": top_ten_quali,
                    "position_breakdown": position_breakdown
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorQualifyingAdvantage(BaseConstructorMetric):
    """Calculate qualifying advantage over grid average."""

    name = "constructor_qualifying_advantage"
    description = "Average positions gained compared to grid average position"
    unit = "positions"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            qual_data = data_loader.get_constructor_qualifying_performance(season, constructor_id)

            if qual_data.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No qualifying data found"})

            # Get race-by-race qualifying performance
            race_performance = []

            for race_id in qual_data["raceId"].unique():
                race_quals = qual_data[qual_data["raceId"] == race_id]

                # Get all qualifying data for this race to calculate grid average
                all_race_quals = data_loader.get_qualifying([race_id])

                if not all_race_quals.empty and not race_quals.empty:
                    # Calculate grid average (excluding DNQs)
                    valid_grid = all_race_quals[all_race_quals["position"].notna() & (all_race_quals["position"] > 0)]
                    if not valid_grid.empty:
                        grid_average = valid_grid["position"].mean()

                        # Get constructor's best position
                        constructor_best = race_quals["position"].min()

                        if pd.notna(constructor_best) and constructor_best > 0:
                            advantage = grid_average - constructor_best  # Positive = better than average
                            race_performance.append(advantage)

            if not race_performance:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No valid comparative data found"})

            avg_advantage = np.mean(race_performance)
            total_races = len(race_performance)

            # Performance categorization
            if avg_advantage > 5:
                performance_level = "Excellent"
            elif avg_advantage > 2:
                performance_level = "Good"
            elif avg_advantage > -2:
                performance_level = "Average"
            else:
                performance_level = "Below Average"

            return MetricResult(
                self.name, round(avg_advantage, 2), constructor_id=constructor_id,
                metadata={
                    "total_races_compared": total_races,
                    "performance_level": performance_level,
                    "best_advantage": round(max(race_performance), 2),
                    "worst_advantage": round(min(race_performance), 2)
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})