"""Constructor lap time performance metrics."""

from typing import Optional
import pandas as pd
import numpy as np

from backend.metrics.base import BaseConstructorMetric, MetricResult
from backend.data.loader import data_loader


class ConstructorAverageLapTime(BaseConstructorMetric):
    """Calculate average lap time across all races."""

    name = "constructor_average_lap_time"
    description = "Average lap time across all races"
    unit = "seconds"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            lap_times = data_loader.get_constructor_lap_times(season, constructor_id)

            if lap_times.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No lap time data found"})

            # Convert milliseconds to seconds
            lap_times["seconds"] = lap_times["milliseconds"] / 1000
            avg_time = lap_times["seconds"].mean()

            return MetricResult(
                self.name, round(avg_time, 3), constructor_id=constructor_id,
                metadata={
                    "total_laps": int(len(lap_times)),
                    "fastest_lap": round(lap_times["seconds"].min(), 3),
                    "slowest_lap": round(lap_times["seconds"].max(), 3),
                    "races_analyzed": int(len(lap_times["raceId"].unique()))
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorFastestLap(BaseConstructorMetric):
    """Find fastest lap time achieved."""

    name = "constructor_fastest_lap"
    description = "Fastest lap time achieved across all races"
    unit = "seconds"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            lap_times = data_loader.get_constructor_lap_times(season, constructor_id)

            if lap_times.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No lap time data found"})

            lap_times["seconds"] = lap_times["milliseconds"] / 1000
            fastest_time = lap_times["seconds"].min()

            # Find the specific lap
            fastest_lap = lap_times[lap_times["seconds"] == fastest_time].iloc[0]

            return MetricResult(
                self.name, round(fastest_time, 3), constructor_id=constructor_id,
                metadata={
                    "race_id": int(fastest_lap["raceId"]) if "raceId" in fastest_lap else None,
                    "lap": int(fastest_lap["lap"]) if "lap" in fastest_lap else None,
                    "year": int(fastest_lap["year"]) if "year" in fastest_lap else None,
                    "driver_id": int(fastest_lap["driverId"]) if "driverId" in fastest_lap else None
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorLapTimeConsistency(BaseConstructorMetric):
    """Measure consistency of lap times."""

    name = "constructor_lap_time_consistency"
    description = "Consistency of lap times across all laps (lower standard deviation is more consistent)"
    unit = "seconds"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            lap_times = data_loader.get_constructor_lap_times(season, constructor_id)

            if lap_times.empty or len(lap_times) < 10:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "Insufficient lap time data for consistency analysis"})

            lap_times["seconds"] = lap_times["milliseconds"] / 1000

            # Remove outliers (laps more than 3 standard deviations from mean)
            mean_time = lap_times["seconds"].mean()
            std_time = lap_times["seconds"].std()
            filtered_laps = lap_times[
                abs(lap_times["seconds"] - mean_time) <= 3 * std_time
            ]

            consistency = filtered_laps["seconds"].std()
            cv = (consistency / filtered_laps["seconds"].mean()) * 100

            return MetricResult(
                self.name, round(consistency, 3), constructor_id=constructor_id,
                metadata={
                    "coefficient_of_variation": round(cv, 2),
                    "total_laps": int(len(lap_times)),
                    "filtered_laps": int(len(filtered_laps)),
                    "mean_lap_time": round(filtered_laps["seconds"].mean(), 3),
                    "consistency_grade": "Excellent" if cv < 2 else "Good" if cv < 3 else "Average" if cv < 4 else "Poor"
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorRacePace(BaseConstructorMetric):
    """Average race pace relative to competitors."""

    name = "constructor_race_pace"
    description = "Average race pace relative to field average"
    unit = "percentage"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            # Get constructor lap times
            constructor_laps = data_loader.get_constructor_lap_times(season, constructor_id)

            if constructor_laps.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No lap time data found"})

            # Get all lap times for comparison
            all_laps = data_loader.get_constructor_lap_times(season)

            if all_laps.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No comparison data available"})

            constructor_laps["seconds"] = constructor_laps["milliseconds"] / 1000
            all_laps["seconds"] = all_laps["milliseconds"] / 1000

            # Calculate pace by race
            race_pace_analysis = []

            for race_id in constructor_laps["raceId"].unique():
                constructor_race_laps = constructor_laps[constructor_laps["raceId"] == race_id]
                all_race_laps = all_laps[all_laps["raceId"] == race_id]

                if len(constructor_race_laps) > 0 and len(all_race_laps) > 0:
                    constructor_avg = constructor_race_laps["seconds"].mean()
                    field_avg = all_race_laps["seconds"].mean()

                    pace_diff = ((constructor_avg - field_avg) / field_avg) * 100
                    race_pace_analysis.append(pace_diff)

            if race_pace_analysis:
                avg_pace_diff = np.mean(race_pace_analysis)
                return MetricResult(
                    self.name, round(-avg_pace_diff, 2), constructor_id=constructor_id,  # Negative so positive = faster
                    metadata={
                        "interpretation": "Positive values indicate faster than average",
                        "races_analyzed": int(len(race_pace_analysis)),
                        "best_race_performance": round(-min(race_pace_analysis), 2),
                        "worst_race_performance": round(-max(race_pace_analysis), 2),
                        "consistency": round(np.std(race_pace_analysis), 2)
                    }
                )
            else:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No valid race comparisons available"})

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorLapTimeImprovement(BaseConstructorMetric):
    """Analyze lap time improvement throughout races."""

    name = "constructor_lap_time_improvement"
    description = "Average lap time improvement from start to end of races"
    unit = "seconds"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            lap_times = data_loader.get_constructor_lap_times(season, constructor_id)

            if lap_times.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No lap time data found"})

            lap_times["seconds"] = lap_times["milliseconds"] / 1000

            # Analyze improvement per race
            race_improvements = []

            for race_id in lap_times["raceId"].unique():
                race_laps = lap_times[lap_times["raceId"] == race_id].sort_values("lap")

                if len(race_laps) >= 10:  # Need sufficient laps for analysis
                    # Compare first 5 laps vs last 5 laps
                    early_laps = race_laps.head(5)["seconds"].mean()
                    late_laps = race_laps.tail(5)["seconds"].mean()

                    improvement = early_laps - late_laps  # Positive = improvement
                    race_improvements.append(improvement)

            if race_improvements:
                avg_improvement = np.mean(race_improvements)
                return MetricResult(
                    self.name, round(avg_improvement, 3), constructor_id=constructor_id,
                    metadata={
                        "races_analyzed": int(len(race_improvements)),
                        "positive_improvement_races": int(sum(1 for x in race_improvements if x > 0)),
                        "best_race_improvement": round(max(race_improvements), 3),
                        "worst_race_degradation": round(min(race_improvements), 3),
                        "interpretation": "Positive values indicate improvement during races"
                    }
                )
            else:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "Insufficient data for improvement analysis"})

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorTireManagement(BaseConstructorMetric):
    """Analyze lap time degradation (tire management)."""

    name = "constructor_tire_management"
    description = "Lap time degradation analysis (lower values indicate better tire management)"
    unit = "seconds per 10 laps"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            lap_times = data_loader.get_constructor_lap_times(season, constructor_id)

            if lap_times.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No lap time data found"})

            lap_times["seconds"] = lap_times["milliseconds"] / 1000

            # Analyze degradation per race stint
            degradation_rates = []

            for race_id in lap_times["raceId"].unique():
                race_laps = lap_times[lap_times["raceId"] == race_id].sort_values("lap")

                if len(race_laps) >= 20:  # Need sufficient laps
                    # Calculate trend over race distance
                    x = np.array(range(len(race_laps)))
                    y = race_laps["seconds"].values

                    # Fit linear trend to get degradation rate
                    slope = np.polyfit(x, y, 1)[0]

                    # Convert to per 10 laps for easier interpretation
                    degradation_per_10_laps = slope * 10
                    degradation_rates.append(degradation_per_10_laps)

            if degradation_rates:
                avg_degradation = np.mean(degradation_rates)
                return MetricResult(
                    self.name, round(avg_degradation, 3), constructor_id=constructor_id,
                    metadata={
                        "races_analyzed": int(len(degradation_rates)),
                        "best_tire_management": round(min(degradation_rates), 3),
                        "worst_tire_management": round(max(degradation_rates), 3),
                        "consistency": round(np.std(degradation_rates), 3),
                        "interpretation": "Lower values indicate better tire management"
                    }
                )
            else:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "Insufficient data for tire management analysis"})

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorCompetitiveLapRate(BaseConstructorMetric):
    """Percentage of laps within 103% of fastest lap."""

    name = "constructor_competitive_lap_rate"
    description = "Percentage of laps within 103% of fastest lap time in each race"
    unit = "percentage"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            lap_times = data_loader.get_constructor_lap_times(season, constructor_id)

            if lap_times.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No lap time data found"})

            lap_times["seconds"] = lap_times["milliseconds"] / 1000

            competitive_laps = 0
            total_laps = 0

            # Get all lap times to find fastest lap per race
            all_lap_times = data_loader.get_constructor_lap_times(season)
            all_lap_times["seconds"] = all_lap_times["milliseconds"] / 1000

            for race_id in lap_times["raceId"].unique():
                race_constructor_laps = lap_times[lap_times["raceId"] == race_id]
                race_all_laps = all_lap_times[all_lap_times["raceId"] == race_id]

                if not race_all_laps.empty:
                    fastest_lap_time = race_all_laps["seconds"].min()
                    competitive_threshold = fastest_lap_time * 1.03  # 103% of fastest

                    race_competitive = len(race_constructor_laps[
                        race_constructor_laps["seconds"] <= competitive_threshold
                    ])

                    competitive_laps += race_competitive
                    total_laps += len(race_constructor_laps)

            competitive_rate = (competitive_laps / total_laps) * 100 if total_laps > 0 else 0

            return MetricResult(
                self.name, round(competitive_rate, 1), constructor_id=constructor_id,
                metadata={
                    "competitive_laps": int(competitive_laps),
                    "total_laps": int(total_laps),
                    "races_analyzed": int(len(lap_times["raceId"].unique())),
                    "threshold": "103% of fastest lap"
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorLapTimeVariability(BaseConstructorMetric):
    """Analyze lap time variability by track conditions."""

    name = "constructor_lap_time_variability"
    description = "Lap time variability across different track conditions"
    unit = "coefficient of variation"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            lap_times = data_loader.get_constructor_lap_times(season, constructor_id)

            if lap_times.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No lap time data found"})

            lap_times["seconds"] = lap_times["milliseconds"] / 1000

            # Calculate variability per race
            race_variabilities = []

            for race_id in lap_times["raceId"].unique():
                race_laps = lap_times[lap_times["raceId"] == race_id]

                if len(race_laps) >= 10:
                    mean_time = race_laps["seconds"].mean()
                    std_time = race_laps["seconds"].std()
                    cv = (std_time / mean_time) * 100
                    race_variabilities.append(cv)

            if race_variabilities:
                avg_variability = np.mean(race_variabilities)
                return MetricResult(
                    self.name, round(avg_variability, 2), constructor_id=constructor_id,
                    metadata={
                        "races_analyzed": int(len(race_variabilities)),
                        "most_consistent_race": round(min(race_variabilities), 2),
                        "least_consistent_race": round(max(race_variabilities), 2),
                        "variability_std": round(np.std(race_variabilities), 2),
                        "interpretation": "Lower values indicate more consistent performance"
                    }
                )
            else:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "Insufficient data for variability analysis"})

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorPaceDominance(BaseConstructorMetric):
    """Percentage of races leading lap time charts."""

    name = "constructor_pace_dominance"
    description = "Percentage of races where constructor had the fastest average lap time"
    unit = "percentage"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            # Get all constructor lap performance for comparison
            all_performance = data_loader.get_constructor_lap_performance(season)

            if all_performance.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No lap performance data found"})

            # Filter to get races where this constructor participated
            constructor_races = all_performance[
                all_performance["constructorId"] == constructor_id
            ]["raceId"].unique()

            if len(constructor_races) == 0:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No races found for this constructor"})

            dominant_races = 0

            for race_id in constructor_races:
                race_performance = all_performance[all_performance["raceId"] == race_id]

                if not race_performance.empty:
                    # Find the fastest average lap time in this race
                    fastest_constructor = race_performance.loc[
                        race_performance["avg_lap_time_s"].idxmin()
                    ]

                    if fastest_constructor["constructorId"] == constructor_id:
                        dominant_races += 1

            dominance_rate = (dominant_races / len(constructor_races)) * 100

            return MetricResult(
                self.name, round(dominance_rate, 1), constructor_id=constructor_id,
                metadata={
                    "dominant_races": int(dominant_races),
                    "total_races": int(len(constructor_races)),
                    "races_analyzed": int(len(constructor_races))
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorFuelAdjustedPace(BaseConstructorMetric):
    """Estimated pace accounting for fuel load."""

    name = "constructor_fuel_adjusted_pace"
    description = "Estimated race pace adjusted for fuel load effects"
    unit = "seconds"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            lap_times = data_loader.get_constructor_lap_times(season, constructor_id)

            if lap_times.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No lap time data found"})

            lap_times["seconds"] = lap_times["milliseconds"] / 1000

            # Estimate fuel-adjusted pace
            # Assumption: ~0.03-0.04s per lap per kg of fuel, ~1.5kg per lap consumption
            fuel_effect_per_lap = 0.035 * 1.5  # seconds per lap

            adjusted_times = []

            for race_id in lap_times["raceId"].unique():
                race_laps = lap_times[lap_times["raceId"] == race_id].sort_values("lap")

                if len(race_laps) >= 10:
                    # Adjust for fuel load - subtract fuel effect from early laps
                    race_laps_copy = race_laps.copy()
                    race_laps_copy["fuel_adjustment"] = (len(race_laps) - race_laps_copy["lap"] + 1) * fuel_effect_per_lap
                    race_laps_copy["adjusted_time"] = race_laps_copy["seconds"] - race_laps_copy["fuel_adjustment"]

                    adjusted_times.extend(race_laps_copy["adjusted_time"].tolist())

            if adjusted_times:
                avg_adjusted_pace = np.mean(adjusted_times)
                return MetricResult(
                    self.name, round(avg_adjusted_pace, 3), constructor_id=constructor_id,
                    metadata={
                        "total_adjusted_laps": int(len(adjusted_times)),
                        "fuel_effect_assumption": f"{fuel_effect_per_lap:.3f} seconds per lap",
                        "raw_average": round(lap_times["seconds"].mean(), 3),
                        "adjustment_difference": round(avg_adjusted_pace - lap_times["seconds"].mean(), 3),
                        "races_analyzed": int(len(lap_times["raceId"].unique()))
                    }
                )
            else:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "Insufficient data for fuel adjustment analysis"})

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})