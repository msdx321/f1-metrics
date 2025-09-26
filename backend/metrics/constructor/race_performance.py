"""Constructor race performance metrics."""

from typing import Dict, Any, Optional
import pandas as pd
from backend.metrics.base import BaseConstructorMetric, MetricResult
from backend.data.loader import data_loader


class ConstructorWinRate(BaseConstructorMetric):
    """Calculate constructor race win rate."""

    name = "constructor_win_rate"
    description = "Percentage of races won (at least one driver finishing 1st)"
    unit = "percentage"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            results = data_loader.get_constructor_results(season, constructor_id)

            if results.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No race results found"})

            # Group by race to find wins (any driver finishing 1st)
            race_results = (results
                           .groupby("raceId")
                           .agg({"position": "min"})
                           .reset_index())

            total_races = len(race_results)
            wins = len(race_results[race_results["position"] == 1])
            win_rate = (wins / total_races) * 100 if total_races > 0 else 0

            return MetricResult(
                self.name, round(win_rate, 1), constructor_id=constructor_id,
                metadata={
                    "total_races": total_races,
                    "wins": wins,
                    "win_percentage": round(win_rate, 1)
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorPodiumRate(BaseConstructorMetric):
    """Calculate constructor podium rate."""

    name = "constructor_podium_rate"
    description = "Percentage of races with at least one driver on podium"
    unit = "percentage"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            results = data_loader.get_constructor_results(season, constructor_id)

            if results.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No race results found"})

            # Group by race to find podium finishes
            race_results = (results
                           .groupby("raceId")
                           .agg({"position": "min"})
                           .reset_index())

            total_races = len(race_results)
            podiums = len(race_results[race_results["position"] <= 3])
            podium_rate = (podiums / total_races) * 100 if total_races > 0 else 0

            # Breakdown by position
            position_counts = {}
            for pos in [1, 2, 3]:
                count = len(race_results[race_results["position"] == pos])
                position_counts[f"P{pos}"] = count

            return MetricResult(
                self.name, round(podium_rate, 1), constructor_id=constructor_id,
                metadata={
                    "total_races": total_races,
                    "podiums": podiums,
                    "position_breakdown": position_counts
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorRaceWins(BaseConstructorMetric):
    """Calculate constructor 1-2 finishes (race wins)."""

    name = "constructor_race_wins"
    description = "Number of races with 1-2 finish (both cars 1st and 2nd)"
    unit = "races"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            wins = data_loader.get_constructor_race_wins(season, constructor_id)

            if wins.empty:
                wins_count = 0
                metadata = {"note": "No 1-2 finishes achieved"}
            else:
                wins_count = len(wins)
                win_years = wins["year"].unique().tolist() if "year" in wins.columns else []
                metadata = {
                    "race_wins": wins_count,
                    "seasons_with_wins": win_years
                }

            return MetricResult(
                self.name, wins_count, constructor_id=constructor_id,
                metadata=metadata
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorPodiumLockouts(BaseConstructorMetric):
    """Calculate constructor podium lockouts."""

    name = "constructor_podium_lockouts"
    description = "Number of races with 1-2 finish lockouts"
    unit = "races"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            lockouts = data_loader.get_constructor_podium_lockouts(season, constructor_id)

            if lockouts.empty:
                lockouts_count = 0
                metadata = {"note": "No podium lockouts achieved"}
            else:
                lockouts_count = len(lockouts)
                lockout_years = lockouts["year"].unique().tolist() if "year" in lockouts.columns else []
                metadata = {
                    "podium_lockouts": lockouts_count,
                    "seasons_with_lockouts": lockout_years
                }

            return MetricResult(
                self.name, lockouts_count, constructor_id=constructor_id,
                metadata=metadata
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorAverageFinishPosition(BaseConstructorMetric):
    """Calculate average finish position for constructor's best car per race."""

    name = "constructor_average_finish_position"
    description = "Average finish position of constructor's best performing car per race"
    unit = "position"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            results = data_loader.get_constructor_results(season, constructor_id)

            if results.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No race results found"})

            # Filter out DNFs for cleaner average
            finished_results = results[results["position"].notna()]

            if finished_results.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No finished races found"})

            # Get best position per race
            race_best_positions = (finished_results
                                  .groupby("raceId")
                                  .agg({"position": "min"})
                                  .reset_index())

            avg_position = race_best_positions["position"].mean()
            best_position = race_best_positions["position"].min()
            total_races = len(race_best_positions)

            return MetricResult(
                self.name, round(avg_position, 2), constructor_id=constructor_id,
                metadata={
                    "total_races": total_races,
                    "best_finish": int(best_position),
                    "races_finished": len(finished_results)
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorPointsScoringRate(BaseConstructorMetric):
    """Calculate percentage of races where constructor scores points."""

    name = "constructor_points_scoring_rate"
    description = "Percentage of races where constructor scores at least one point"
    unit = "percentage"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            points_data = data_loader.get_constructor_points_data(season, constructor_id)

            if points_data.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No points data found"})

            total_races = len(points_data)
            points_scoring_races = len(points_data[points_data["total_points"] > 0])

            scoring_rate = (points_scoring_races / total_races) * 100 if total_races > 0 else 0

            # Points distribution
            points_breakdown = {
                "zero_points": len(points_data[points_data["total_points"] == 0]),
                "1_to_10_points": len(points_data[(points_data["total_points"] > 0) & (points_data["total_points"] <= 10)]),
                "11_to_25_points": len(points_data[(points_data["total_points"] > 10) & (points_data["total_points"] <= 25)]),
                "over_25_points": len(points_data[points_data["total_points"] > 25])
            }

            return MetricResult(
                self.name, round(scoring_rate, 1), constructor_id=constructor_id,
                metadata={
                    "total_races": total_races,
                    "points_scoring_races": points_scoring_races,
                    "points_distribution": points_breakdown,
                    "average_points_per_race": round(points_data["total_points"].mean(), 2)
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorFrontRowLockouts(BaseConstructorMetric):
    """Calculate front row lockouts (1st and 2nd on grid)."""

    name = "constructor_front_row_lockouts"
    description = "Number of races starting 1st and 2nd on the grid"
    unit = "races"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            qual_data = data_loader.get_constructor_qualifying_performance(season, constructor_id)

            if qual_data.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No qualifying data found"})

            # Group by race and check for front row lockouts
            race_positions = (qual_data
                            .groupby("raceId")
                            .agg({"position": ["min", "count"]})
                            .reset_index())

            race_positions.columns = ["raceId", "best_position", "cars_count"]

            # Front row lockouts: best position is 1 and have at least 2 cars in top 2
            qualified_races = qual_data[qual_data["position"] <= 2]
            front_row_counts = (qualified_races
                              .groupby("raceId")
                              .size()
                              .reset_index(columns=["front_row_cars"]))

            lockouts = front_row_counts[front_row_counts["front_row_cars"] >= 2]
            lockouts_count = len(lockouts)

            return MetricResult(
                self.name, lockouts_count, constructor_id=constructor_id,
                metadata={
                    "total_races": len(race_positions),
                    "front_row_lockouts": lockouts_count
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorDoublePodiums(BaseConstructorMetric):
    """Calculate double podium finishes (both cars in top 3)."""

    name = "constructor_double_podiums"
    description = "Number of races with both cars finishing in top 3"
    unit = "races"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            results = data_loader.get_constructor_results(season, constructor_id)

            if results.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No race results found"})

            # Filter podium results
            podium_results = results[results["position"] <= 3]

            # Count podium finishes per race
            podium_counts = (podium_results
                           .groupby("raceId")
                           .size()
                           .reset_index(columns=["podium_cars"]))

            # Double podiums: 2 or more cars in top 3
            double_podiums = podium_counts[podium_counts["podium_cars"] >= 2]
            double_podiums_count = len(double_podiums)

            # Get total races for context
            total_races = results["raceId"].nunique()

            return MetricResult(
                self.name, double_podiums_count, constructor_id=constructor_id,
                metadata={
                    "total_races": total_races,
                    "double_podiums": double_podiums_count,
                    "double_podium_rate": round((double_podiums_count / total_races) * 100, 1) if total_races > 0 else 0
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})