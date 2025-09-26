"""Constructor championship and points-related metrics."""

from typing import Dict, Any, Optional
import pandas as pd
from backend.metrics.base import BaseConstructorMetric, MetricResult
from backend.data.loader import data_loader


class ConstructorChampionshipPosition(BaseConstructorMetric):
    """Calculate constructor's championship position for a season."""

    name = "constructor_championship_position"
    description = "Final championship position for the season"
    unit = "position"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            final_standings = data_loader.get_constructor_championship_positions(season)

            if final_standings.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No championship standings found"})

            constructor_position = final_standings[
                final_standings["constructorId"] == constructor_id
            ]

            if constructor_position.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "Constructor not found in standings"})

            if season:
                # Single season
                season_position = constructor_position[constructor_position["year"] == season]
                if season_position.empty:
                    return MetricResult(self.name, None, constructor_id=constructor_id,
                                      metadata={"error": f"No data for {season}"})

                position = season_position.iloc[0]["position"]
                points = season_position.iloc[0]["points"]

                return MetricResult(
                    self.name, position, constructor_id=constructor_id,
                    metadata={
                        "season": season,
                        "points": points,
                        "wins": season_position.iloc[0].get("wins", 0)
                    }
                )
            else:
                # All seasons - return best position
                best_position = constructor_position["position"].min()
                best_season = constructor_position.loc[
                    constructor_position["position"].idxmin(), "year"
                ]

                positions_by_year = constructor_position.set_index("year")["position"].to_dict()

                return MetricResult(
                    self.name, int(best_position), constructor_id=constructor_id,
                    metadata={
                        "best_season": int(best_season),
                        "positions_by_year": positions_by_year,
                        "championships": len(constructor_position[constructor_position["position"] == 1])
                    }
                )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorChampionshipWins(BaseConstructorMetric):
    """Count constructor championship wins."""

    name = "constructor_championship_wins"
    description = "Number of constructor championships won"
    unit = "championships"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            final_standings = data_loader.get_constructor_championship_positions(season)

            if final_standings.empty:
                return MetricResult(self.name, 0, constructor_id=constructor_id,
                                  metadata={"error": "No championship standings found"})

            constructor_standings = final_standings[
                final_standings["constructorId"] == constructor_id
            ]

            championships = constructor_standings[constructor_standings["position"] == 1]
            championship_count = len(championships)

            if championship_count > 0:
                championship_years = championships["year"].tolist()
                return MetricResult(
                    self.name, championship_count, constructor_id=constructor_id,
                    metadata={
                        "championship_years": championship_years,
                        "last_championship": max(championship_years)
                    }
                )
            else:
                return MetricResult(
                    self.name, 0, constructor_id=constructor_id,
                    metadata={"note": "No championships won"}
                )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorPointsPerSeason(BaseConstructorMetric):
    """Calculate total points scored per season."""

    name = "constructor_points_per_season"
    description = "Average points scored per season"
    unit = "points"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            points_data = data_loader.get_constructor_points_data(season, constructor_id)

            if points_data.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No points data found"})

            # Group by season and sum points
            season_points = (points_data
                           .groupby("year")
                           .agg({
                               "total_points": "sum",
                               "raceId": "count"
                           })
                           .reset_index())
            season_points.rename(columns={"raceId": "races"}, inplace=True)

            if season:
                # Single season
                season_data = season_points[season_points["year"] == season]
                if season_data.empty:
                    return MetricResult(self.name, None, constructor_id=constructor_id,
                                      metadata={"error": f"No data for {season}"})

                total_points = season_data.iloc[0]["total_points"]
                races = season_data.iloc[0]["races"]

                return MetricResult(
                    self.name, float(total_points), constructor_id=constructor_id,
                    metadata={
                        "season": season,
                        "races": races,
                        "points_per_race": total_points / races if races > 0 else 0
                    }
                )
            else:
                # All seasons - calculate average
                avg_points = season_points["total_points"].mean()
                total_points = season_points["total_points"].sum()
                seasons_count = len(season_points)

                points_by_year = season_points.set_index("year")["total_points"].to_dict()

                return MetricResult(
                    self.name, round(avg_points, 1), constructor_id=constructor_id,
                    metadata={
                        "seasons_count": seasons_count,
                        "total_points": float(total_points),
                        "best_season": float(season_points["total_points"].max()),
                        "points_by_year": {int(k): float(v) for k, v in points_by_year.items()}
                    }
                )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorPointsPerRace(BaseConstructorMetric):
    """Calculate average points scored per race."""

    name = "constructor_points_per_race"
    description = "Average points scored per race"
    unit = "points/race"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            points_data = data_loader.get_constructor_points_data(season, constructor_id)

            if points_data.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No points data found"})

            avg_points_per_race = points_data["total_points"].mean()
            total_points = points_data["total_points"].sum()
            race_count = len(points_data)

            # Points distribution
            points_breakdown = {
                "zero_points": len(points_data[points_data["total_points"] == 0]),
                "single_points": len(points_data[(points_data["total_points"] > 0) & (points_data["total_points"] < 10)]),
                "double_digit_points": len(points_data[points_data["total_points"] >= 10])
            }

            return MetricResult(
                self.name, round(avg_points_per_race, 2), constructor_id=constructor_id,
                metadata={
                    "total_races": race_count,
                    "total_points": float(total_points),
                    "max_points_race": float(points_data["total_points"].max()),
                    "points_scoring_rate": round((race_count - points_breakdown["zero_points"]) / race_count * 100, 1),
                    "points_breakdown": points_breakdown
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorTopThreeFinishes(BaseConstructorMetric):
    """Calculate rate of top-3 championship finishes."""

    name = "constructor_top_three_finishes"
    description = "Percentage of seasons finishing in top 3 of championship"
    unit = "percentage"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            final_standings = data_loader.get_constructor_championship_positions(season)

            if final_standings.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No championship standings found"})

            constructor_standings = final_standings[
                final_standings["constructorId"] == constructor_id
            ]

            if constructor_standings.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "Constructor not found in standings"})

            total_seasons = len(constructor_standings)
            top_three_finishes = len(constructor_standings[constructor_standings["position"] <= 3])

            top_three_rate = (top_three_finishes / total_seasons) * 100 if total_seasons > 0 else 0

            # Breakdown by position
            position_breakdown = {}
            for pos in [1, 2, 3]:
                count = len(constructor_standings[constructor_standings["position"] == pos])
                if count > 0:
                    years = constructor_standings[constructor_standings["position"] == pos]["year"].tolist()
                    position_breakdown[f"P{pos}"] = {"count": count, "years": years}

            return MetricResult(
                self.name, round(top_three_rate, 1), constructor_id=constructor_id,
                metadata={
                    "total_seasons": total_seasons,
                    "top_three_count": top_three_finishes,
                    "position_breakdown": position_breakdown,
                    "best_position": int(constructor_standings["position"].min())
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})