"""Constructor competitiveness and dominance metrics."""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from backend.metrics.base import BaseConstructorMetric, MetricResult
from backend.data.loader import data_loader


class ConstructorSeasonDominance(BaseConstructorMetric):
    """Calculate season dominance based on wins and points lead."""

    name = "constructor_season_dominance"
    description = "Season dominance index based on wins, points lead, and consistency"
    unit = "index"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            if not season:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "Season parameter required for dominance calculation"})

            standings = data_loader.get_constructor_championship_positions(season)
            points_data = data_loader.get_constructor_points_data(season, constructor_id)

            if standings.empty or points_data.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No championship or points data found"})

            # Get constructor's final position and points
            constructor_standing = standings[standings["constructorId"] == constructor_id]
            if constructor_standing.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "Constructor not found in standings"})

            final_position = constructor_standing.iloc[0]["position"]
            constructor_points = constructor_standing.iloc[0]["points"]

            # Get champion points for comparison
            champion_points = standings[standings["position"] == 1].iloc[0]["points"]

            # Calculate dominance factors
            total_races = len(points_data)
            wins = len(points_data[points_data["best_finish"] == 1])
            win_rate = (wins / total_races) * 100 if total_races > 0 else 0

            # Points dominance (percentage of maximum possible points)
            max_possible_points = total_races * 44  # Assuming 44 points max per race (25+18+1)
            points_dominance = (constructor_points / max_possible_points) * 100 if max_possible_points > 0 else 0

            # Championship margin
            if final_position == 1 and len(standings) > 1:
                runner_up_points = standings[standings["position"] == 2].iloc[0]["points"]
                championship_margin = constructor_points - runner_up_points
            else:
                championship_margin = constructor_points - champion_points

            # Calculate dominance index (0-100)
            dominance_index = (
                win_rate * 0.4 +  # 40% weight on win rate
                points_dominance * 0.35 +  # 35% weight on points efficiency
                (100 if final_position == 1 else max(0, 100 - (final_position - 1) * 20)) * 0.25  # 25% position
            )

            # Dominance level
            if dominance_index >= 80:
                dominance_level = "Dominant"
            elif dominance_index >= 60:
                dominance_level = "Very Strong"
            elif dominance_index >= 40:
                dominance_level = "Competitive"
            elif dominance_index >= 20:
                dominance_level = "Moderate"
            else:
                dominance_level = "Weak"

            return MetricResult(
                self.name, round(dominance_index, 1), constructor_id=constructor_id,
                metadata={
                    "season": season,
                    "final_position": int(final_position),
                    "total_points": float(constructor_points),
                    "wins": wins,
                    "win_rate": round(win_rate, 1),
                    "championship_margin": float(championship_margin),
                    "dominance_level": dominance_level
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorConsistencyIndex(BaseConstructorMetric):
    """Calculate consistency across races in a season."""

    name = "constructor_consistency_index"
    description = "Consistency index based on points variation (higher is better)"
    unit = "index"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            points_data = data_loader.get_constructor_points_data(season, constructor_id)

            if points_data.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No points data found"})

            total_races = len(points_data)
            if total_races < 3:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "Insufficient races for consistency calculation"})

            race_points = points_data["total_points"]
            mean_points = race_points.mean()
            std_points = race_points.std()

            # Coefficient of variation (lower is more consistent)
            if mean_points > 0:
                coefficient_of_variation = std_points / mean_points
                # Convert to consistency index (invert and scale)
                consistency_index = max(0, 100 - (coefficient_of_variation * 100))
            else:
                consistency_index = 0  # No points = no consistency

            # Additional consistency metrics
            zero_points_races = len(points_data[points_data["total_points"] == 0])
            points_scoring_rate = ((total_races - zero_points_races) / total_races) * 100

            # Consistency level
            if consistency_index >= 80:
                consistency_level = "Very Consistent"
            elif consistency_index >= 60:
                consistency_level = "Consistent"
            elif consistency_index >= 40:
                consistency_level = "Moderately Consistent"
            elif consistency_index >= 20:
                consistency_level = "Inconsistent"
            else:
                consistency_level = "Very Inconsistent"

            return MetricResult(
                self.name, round(consistency_index, 1), constructor_id=constructor_id,
                metadata={
                    "total_races": total_races,
                    "mean_points": round(mean_points, 2),
                    "std_points": round(std_points, 2),
                    "points_scoring_rate": round(points_scoring_rate, 1),
                    "consistency_level": consistency_level
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorCompetitivenessRating(BaseConstructorMetric):
    """Overall competitiveness rating combining multiple factors."""

    name = "constructor_competitiveness_rating"
    description = "Overall competitiveness rating (0-100)"
    unit = "rating"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            results = data_loader.get_constructor_results(season, constructor_id)
            points_data = data_loader.get_constructor_points_data(season, constructor_id)

            if results.empty or points_data.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No race or points data found"})

            # Performance metrics
            total_races = len(points_data)
            avg_points = points_data["total_points"].mean()
            best_finish = results["position"].min()
            podiums = len(results[results["position"] <= 3])
            wins = len(results[results["position"] == 1])

            # Scoring components (0-100 each)
            points_rating = min(100, (avg_points / 25) * 100)  # Scale based on max points
            position_rating = max(0, 100 - (best_finish - 1) * 5) if pd.notna(best_finish) else 0
            podium_rating = (podiums / total_races) * 100 if total_races > 0 else 0
            win_rating = (wins / total_races) * 100 if total_races > 0 else 0

            # Combined competitiveness rating
            competitiveness_rating = (
                points_rating * 0.35 +  # 35% points performance
                position_rating * 0.25 +  # 25% best result
                podium_rating * 0.25 +  # 25% podium rate
                win_rating * 0.15  # 15% win rate
            )

            # Rating categories
            if competitiveness_rating >= 85:
                category = "Dominant"
            elif competitiveness_rating >= 70:
                category = "Very Competitive"
            elif competitiveness_rating >= 55:
                category = "Competitive"
            elif competitiveness_rating >= 40:
                category = "Midfield"
            elif competitiveness_rating >= 25:
                category = "Back of Grid"
            else:
                category = "Struggling"

            return MetricResult(
                self.name, round(competitiveness_rating, 1), constructor_id=constructor_id,
                metadata={
                    "total_races": total_races,
                    "avg_points_per_race": round(avg_points, 2),
                    "best_finish": int(best_finish) if pd.notna(best_finish) else None,
                    "podiums": podiums,
                    "wins": wins,
                    "category": category
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorPerformanceConsistency(BaseConstructorMetric):
    """Measure performance consistency across different track types."""

    name = "constructor_performance_consistency"
    description = "Performance consistency across different race types and conditions"
    unit = "index"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            points_data = data_loader.get_constructor_points_data(season, constructor_id)

            if points_data.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No points data found"})

            # Performance quartiles analysis
            race_points = points_data["total_points"]
            q1 = race_points.quantile(0.25)
            q2 = race_points.quantile(0.5)  # Median
            q3 = race_points.quantile(0.75)

            # Performance spread
            iqr = q3 - q1
            performance_range = race_points.max() - race_points.min()

            # Consistency score (inverse of spread, normalized)
            if performance_range > 0:
                consistency_score = max(0, 100 - (iqr / race_points.mean() * 50)) if race_points.mean() > 0 else 0
            else:
                consistency_score = 100  # Perfect consistency if no variation

            # Performance distribution
            high_performance_races = len(race_points[race_points >= q3])
            low_performance_races = len(race_points[race_points <= q1])
            consistent_races = len(race_points[(race_points >= q1) & (race_points <= q3)])

            return MetricResult(
                self.name, round(consistency_score, 1), constructor_id=constructor_id,
                metadata={
                    "total_races": len(points_data),
                    "performance_median": float(q2),
                    "performance_iqr": float(iqr),
                    "performance_range": float(performance_range),
                    "high_performance_races": high_performance_races,
                    "consistent_races": consistent_races,
                    "low_performance_races": low_performance_races
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorRaceWinStreak(BaseConstructorMetric):
    """Calculate longest consecutive win streak."""

    name = "constructor_race_win_streak"
    description = "Longest consecutive race win streak"
    unit = "races"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            results = data_loader.get_constructor_results(season, constructor_id)

            if results.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No race results found"})

            # Sort by year and round
            results_sorted = results.sort_values(["year", "round"])

            # Group by race and find wins
            race_results = (results_sorted
                           .groupby(["raceId", "year", "round"])
                           .agg({"position": "min"})
                           .reset_index())

            race_results["is_win"] = (race_results["position"] == 1).astype(int)

            # Calculate consecutive wins
            win_streaks = []
            current_streak = 0

            for _, race in race_results.iterrows():
                if race["is_win"]:
                    current_streak += 1
                else:
                    if current_streak > 0:
                        win_streaks.append(current_streak)
                    current_streak = 0

            # Don't forget the last streak if it ends with wins
            if current_streak > 0:
                win_streaks.append(current_streak)

            longest_streak = max(win_streaks) if win_streaks else 0
            total_wins = sum(win_streaks)

            return MetricResult(
                self.name, longest_streak, constructor_id=constructor_id,
                metadata={
                    "total_races": len(race_results),
                    "total_wins": total_wins,
                    "win_streaks": win_streaks,
                    "number_of_streaks": len(win_streaks)
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorSeasonalImprovement(BaseConstructorMetric):
    """Measure improvement throughout a season."""

    name = "constructor_seasonal_improvement"
    description = "Performance trend throughout the season (positive = improving)"
    unit = "trend"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            if not season:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "Season parameter required for seasonal trend analysis"})

            points_data = data_loader.get_constructor_points_data(season, constructor_id)

            if points_data.empty or len(points_data) < 5:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "Insufficient data for trend analysis"})

            # Sort by round
            points_sorted = points_data.sort_values("round")

            # Calculate rolling averages for trend analysis
            window_size = min(5, len(points_sorted) // 3)
            rolling_avg = points_sorted["total_points"].rolling(window=window_size, center=True).mean()

            # Linear trend calculation
            race_numbers = np.arange(len(points_sorted))
            trend_slope, _ = np.polyfit(race_numbers, points_sorted["total_points"], 1)

            # Improvement categories
            if trend_slope > 1:
                trend_category = "Strong Improvement"
            elif trend_slope > 0.2:
                trend_category = "Moderate Improvement"
            elif trend_slope > -0.2:
                trend_category = "Stable"
            elif trend_slope > -1:
                trend_category = "Slight Decline"
            else:
                trend_category = "Significant Decline"

            # Season halves comparison
            mid_point = len(points_sorted) // 2
            first_half_avg = points_sorted.iloc[:mid_point]["total_points"].mean()
            second_half_avg = points_sorted.iloc[mid_point:]["total_points"].mean()
            improvement_percentage = ((second_half_avg - first_half_avg) / first_half_avg * 100) if first_half_avg > 0 else 0

            return MetricResult(
                self.name, round(trend_slope, 3), constructor_id=constructor_id,
                metadata={
                    "season": season,
                    "total_races": len(points_sorted),
                    "trend_category": trend_category,
                    "first_half_avg": round(first_half_avg, 2),
                    "second_half_avg": round(second_half_avg, 2),
                    "improvement_percentage": round(improvement_percentage, 1)
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})