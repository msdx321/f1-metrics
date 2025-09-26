"""Constructor pit stop performance metrics."""

from typing import Optional
import pandas as pd
import numpy as np

from backend.metrics.base import BaseConstructorMetric, MetricResult
from backend.data.loader import data_loader


class ConstructorAveragePitStopTime(BaseConstructorMetric):
    """Calculate average pit stop duration."""

    name = "constructor_average_pit_stop_time"
    description = "Average pit stop duration across all stops"
    unit = "seconds"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            pit_stops = data_loader.get_constructor_pit_stop_stats(season, constructor_id)

            if pit_stops.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No pit stop data found"})

            # Convert milliseconds to seconds
            pit_stops["duration_seconds"] = pit_stops["milliseconds"] / 1000

            # Filter out outliers (stops > 60 seconds are likely repairs/retirements, not racing pit stops)
            total_stops_before_filter = len(pit_stops)
            pit_stops = pit_stops[pit_stops["duration_seconds"] <= 60.0]

            if pit_stops.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No valid pit stop data after filtering outliers"})

            avg_time = pit_stops["duration_seconds"].mean()

            return MetricResult(
                self.name, round(avg_time, 3), constructor_id=constructor_id,
                metadata={
                    "total_stops": int(len(pit_stops)),
                    "stops_before_filtering": int(total_stops_before_filter),
                    "outliers_filtered": int(total_stops_before_filter - len(pit_stops)),
                    "fastest_stop": round(pit_stops["duration_seconds"].min(), 3),
                    "slowest_stop": round(pit_stops["duration_seconds"].max(), 3),
                    "seasons_analyzed": int(len(pit_stops["year"].unique())) if "year" in pit_stops.columns else 1
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorFastestPitStop(BaseConstructorMetric):
    """Find fastest single pit stop time."""

    name = "constructor_fastest_pit_stop"
    description = "Fastest single pit stop time achieved"
    unit = "seconds"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            pit_stops = data_loader.get_constructor_pit_stop_stats(season, constructor_id)

            if pit_stops.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No pit stop data found"})

            pit_stops["duration_seconds"] = pit_stops["milliseconds"] / 1000

            # Filter out outliers (stops > 60 seconds)
            total_stops_before_filter = len(pit_stops)
            pit_stops = pit_stops[pit_stops["duration_seconds"] <= 60.0]

            if pit_stops.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No valid pit stop data after filtering outliers"})

            fastest_time = pit_stops["duration_seconds"].min()

            # Find the race where this happened
            fastest_stop = pit_stops[pit_stops["duration_seconds"] == fastest_time].iloc[0]

            return MetricResult(
                self.name, round(fastest_time, 3), constructor_id=constructor_id,
                metadata={
                    "race_id": int(fastest_stop["raceId"]) if "raceId" in fastest_stop else None,
                    "lap": int(fastest_stop["lap"]) if "lap" in fastest_stop else None,
                    "year": int(fastest_stop["year"]) if "year" in fastest_stop else None,
                    "total_stops": int(len(pit_stops))
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorPitStopConsistency(BaseConstructorMetric):
    """Measure consistency of pit stop times."""

    name = "constructor_pit_stop_consistency"
    description = "Standard deviation of pit stop times (lower is more consistent)"
    unit = "seconds"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            pit_stops = data_loader.get_constructor_pit_stop_stats(season, constructor_id)

            if pit_stops.empty or len(pit_stops) < 2:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "Insufficient pit stop data for consistency analysis"})

            pit_stops["duration_seconds"] = pit_stops["milliseconds"] / 1000

            # Filter out outliers (stops > 60 seconds)
            total_stops_before_filter = len(pit_stops)
            pit_stops = pit_stops[pit_stops["duration_seconds"] <= 60.0]

            if len(pit_stops) < 2:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "Insufficient valid pit stop data for consistency analysis after filtering"})

            std_dev = pit_stops["duration_seconds"].std()
            mean_time = pit_stops["duration_seconds"].mean()

            # Calculate coefficient of variation (CV) as a percentage
            cv = (std_dev / mean_time) * 100 if mean_time > 0 else 0

            return MetricResult(
                self.name, round(std_dev, 3), constructor_id=constructor_id,
                metadata={
                    "mean_time": round(mean_time, 3),
                    "coefficient_of_variation": round(cv, 1),
                    "total_stops": int(len(pit_stops)),
                    "consistency_grade": "Excellent" if cv < 5 else "Good" if cv < 10 else "Average" if cv < 15 else "Poor"
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorSubThreeSecondStops(BaseConstructorMetric):
    """Percentage of stops under 3 seconds."""

    name = "constructor_sub_three_second_stops"
    description = "Percentage of pit stops completed in under 3 seconds"
    unit = "percentage"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            pit_stops = data_loader.get_constructor_pit_stop_stats(season, constructor_id)

            if pit_stops.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No pit stop data found"})

            pit_stops["duration_seconds"] = pit_stops["milliseconds"] / 1000
            sub_three_stops = len(pit_stops[pit_stops["duration_seconds"] < 3.0])
            total_stops = len(pit_stops)

            percentage = (sub_three_stops / total_stops) * 100 if total_stops > 0 else 0

            return MetricResult(
                self.name, round(percentage, 1), constructor_id=constructor_id,
                metadata={
                    "sub_three_stops": int(sub_three_stops),
                    "total_stops": int(total_stops),
                    "average_time": round(pit_stops["duration_seconds"].mean(), 3)
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorPitStopEfficiency(BaseConstructorMetric):
    """Compare to average pit stop times in same races."""

    name = "constructor_pit_stop_efficiency"
    description = "Performance relative to average pit stop times in same races"
    unit = "percentage"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            # Get constructor pit stops
            constructor_stops = data_loader.get_constructor_pit_stop_stats(season, constructor_id)

            if constructor_stops.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No pit stop data found"})

            # Get all pit stops for comparison
            all_stops = data_loader.get_constructor_pit_stop_stats(season)

            if all_stops.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No comparison data available"})

            constructor_stops["duration_seconds"] = constructor_stops["milliseconds"] / 1000
            all_stops["duration_seconds"] = all_stops["milliseconds"] / 1000

            # Calculate average times by race
            race_averages = all_stops.groupby("raceId")["duration_seconds"].mean()

            # Map race averages to constructor stops
            constructor_stops["race_average"] = constructor_stops["raceId"].map(race_averages)

            # Calculate efficiency (negative means faster than average)
            constructor_stops["efficiency"] = ((constructor_stops["duration_seconds"] - constructor_stops["race_average"])
                                             / constructor_stops["race_average"]) * 100

            avg_efficiency = constructor_stops["efficiency"].mean()

            return MetricResult(
                self.name, round(-avg_efficiency, 1), constructor_id=constructor_id,  # Negative so positive = better
                metadata={
                    "interpretation": "Positive values indicate faster than average",
                    "constructor_avg": round(constructor_stops["duration_seconds"].mean(), 3),
                    "field_avg": round(all_stops["duration_seconds"].mean(), 3),
                    "races_analyzed": int(len(constructor_stops["raceId"].unique()))
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorAveragePitStopsPerRace(BaseConstructorMetric):
    """Average number of pit stops per race."""

    name = "constructor_average_pit_stops_per_race"
    description = "Average number of pit stops per race"
    unit = "stops"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            pit_stops = data_loader.get_constructor_pit_stop_stats(season, constructor_id)

            if pit_stops.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No pit stop data found"})

            # Count stops per race
            stops_per_race = pit_stops.groupby("raceId").size()
            avg_stops = stops_per_race.mean()

            return MetricResult(
                self.name, round(avg_stops, 2), constructor_id=constructor_id,
                metadata={
                    "total_races": int(len(stops_per_race)),
                    "total_stops": int(len(pit_stops)),
                    "max_stops_in_race": int(stops_per_race.max()),
                    "min_stops_in_race": int(stops_per_race.min())
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorPitStopTimeImprovement(BaseConstructorMetric):
    """Analyze pit stop time trends across the season."""

    name = "constructor_pit_stop_time_improvement"
    description = "Trend of pit stop times across the season (negative = improving)"
    unit = "seconds per race"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            pit_stops = data_loader.get_constructor_pit_stop_stats(season, constructor_id)

            if pit_stops.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No pit stop data found"})

            if season:
                # Single season trend analysis
                pit_stops["duration_seconds"] = pit_stops["milliseconds"] / 1000

                # Calculate average pit stop time per race
                race_averages = pit_stops.groupby(["raceId", "round"])["duration_seconds"].mean().reset_index()
                race_averages = race_averages.sort_values("round")

                if len(race_averages) < 3:
                    return MetricResult(self.name, None, constructor_id=constructor_id,
                                      metadata={"error": "Insufficient races for trend analysis"})

                # Calculate linear trend
                x = np.arange(len(race_averages))
                y = race_averages["duration_seconds"].values
                slope = np.polyfit(x, y, 1)[0]

                return MetricResult(
                    self.name, round(slope, 4), constructor_id=constructor_id,
                    metadata={
                        "season": int(season),
                        "races_analyzed": int(len(race_averages)),
                        "early_season_avg": round(race_averages["duration_seconds"].head(3).mean(), 3),
                        "late_season_avg": round(race_averages["duration_seconds"].tail(3).mean(), 3),
                        "interpretation": "Negative values indicate improvement over time"
                    }
                )
            else:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "Season parameter required for trend analysis"})

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorPitStopReliability(BaseConstructorMetric):
    """Percentage of successful pit stops without issues."""

    name = "constructor_pit_stop_reliability"
    description = "Percentage of pit stops without major delays or issues"
    unit = "percentage"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            pit_stops = data_loader.get_constructor_pit_stop_stats(season, constructor_id)

            if pit_stops.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No pit stop data found"})

            pit_stops["duration_seconds"] = pit_stops["milliseconds"] / 1000

            # Filter out outliers (stops > 60 seconds are likely repairs/retirements, not racing pit stops)
            total_stops_before_filter = len(pit_stops)
            pit_stops = pit_stops[pit_stops["duration_seconds"] <= 60.0]

            if pit_stops.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No valid pit stop data after filtering outliers"})

            # Calculate dynamic threshold based on team's average pit stop time
            avg_pit_stop_time = pit_stops["duration_seconds"].mean()

            # Define "problematic" stops as those taking more than 1.2x the team's average
            # This makes the threshold relative to the team's performance
            problematic_threshold = avg_pit_stop_time * 1.2
            successful_stops = len(pit_stops[pit_stops["duration_seconds"] <= problematic_threshold])
            total_stops = len(pit_stops)

            reliability_rate = (successful_stops / total_stops) * 100 if total_stops > 0 else 0

            return MetricResult(
                self.name, round(reliability_rate, 1), constructor_id=constructor_id,
                metadata={
                    "successful_stops": int(successful_stops),
                    "total_stops": int(total_stops),
                    "problematic_stops": int(total_stops - successful_stops),
                    "threshold_seconds": round(problematic_threshold, 3),
                    "average_pit_stop_time": round(avg_pit_stop_time, 3),
                    "threshold_multiplier": 1.2,
                    "longest_stop": round(pit_stops["duration_seconds"].max(), 3),
                    "stops_before_filtering": int(total_stops_before_filter),
                    "outliers_filtered": int(total_stops_before_filter - total_stops)
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorPitStopStrategicSuccess(BaseConstructorMetric):
    """Analyze strategic effectiveness of pit stop timing."""

    name = "constructor_pit_stop_strategic_success"
    description = "Effectiveness of pit stop strategy timing"
    unit = "index"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            pit_stops = data_loader.get_constructor_pit_stop_stats(season, constructor_id)

            if pit_stops.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No pit stop data found"})

            # This is a simplified strategic analysis based on pit stop timing
            # Group by race and analyze stop patterns
            race_analysis = []

            for race_id in pit_stops["raceId"].unique():
                race_stops = pit_stops[pit_stops["raceId"] == race_id]

                # Calculate strategic metrics
                early_stops = len(race_stops[race_stops["lap"] <= 15])  # Early strategy
                mid_stops = len(race_stops[(race_stops["lap"] > 15) & (race_stops["lap"] <= 40)])  # Mid race
                late_stops = len(race_stops[race_stops["lap"] > 40])  # Late strategy

                total_race_stops = len(race_stops)

                race_analysis.append({
                    "race_id": race_id,
                    "early_stops": early_stops,
                    "mid_stops": mid_stops,
                    "late_stops": late_stops,
                    "total_stops": total_race_stops
                })

            # Calculate strategic diversity index
            if race_analysis:
                df_analysis = pd.DataFrame(race_analysis)
                strategic_diversity = df_analysis[["early_stops", "mid_stops", "late_stops"]].std(axis=1).mean()

                return MetricResult(
                    self.name, round(strategic_diversity, 2), constructor_id=constructor_id,
                    metadata={
                        "races_analyzed": int(len(race_analysis)),
                        "avg_early_stops": round(df_analysis["early_stops"].mean(), 1),
                        "avg_mid_stops": round(df_analysis["mid_stops"].mean(), 1),
                        "avg_late_stops": round(df_analysis["late_stops"].mean(), 1),
                        "interpretation": "Higher values indicate more strategic variety"
                    }
                )
            else:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No strategic data available"})

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})