"""Constructor reliability metrics."""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from backend.metrics.base import BaseConstructorMetric, MetricResult
from backend.data.loader import data_loader


class ConstructorDNFRate(BaseConstructorMetric):
    """Calculate constructor DNF (Did Not Finish) rate."""

    name = "constructor_dnf_rate"
    description = "Percentage of car entries that did not finish the race"
    unit = "percentage"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            results = data_loader.get_constructor_results(season, constructor_id)

            if results.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No race results found"})

            # Count total entries and DNFs
            total_entries = len(results)
            dnfs = len(results[results["position"].isna() | (results["position"] == 0)])

            dnf_rate = (dnfs / total_entries) * 100 if total_entries > 0 else 0

            return MetricResult(
                self.name, round(dnf_rate, 1), constructor_id=constructor_id,
                metadata={
                    "total_entries": total_entries,
                    "dnfs": dnfs,
                    "finishes": total_entries - dnfs,
                    "finish_rate": round(100 - dnf_rate, 1)
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorMechanicalFailureRate(BaseConstructorMetric):
    """Calculate rate of mechanical failures specifically."""

    name = "constructor_mechanical_failure_rate"
    description = "Percentage of retirements due to mechanical failures"
    unit = "percentage"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            reliability_data = data_loader.get_constructor_reliability_data(season, constructor_id)

            if reliability_data.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No reliability data found"})

            # Define mechanical failure status IDs (common ones)
            mechanical_failures = [
                "Engine", "Gearbox", "Transmission", "Clutch", "Hydraulics",
                "Electrical", "Brakes", "Suspension", "Power Unit", "ERS",
                "Turbo", "Battery", "MGU-K", "MGU-H"
            ]

            total_entries = len(reliability_data)
            dnfs = reliability_data[reliability_data["position"].isna() | (reliability_data["position"] == 0)]

            # Filter mechanical failures
            mechanical_dnfs = 0
            if "status" in dnfs.columns:
                for _, dnf in dnfs.iterrows():
                    status = str(dnf.get("status", "")).lower()
                    if any(failure.lower() in status for failure in mechanical_failures):
                        mechanical_dnfs += 1

            mechanical_failure_rate = (mechanical_dnfs / total_entries) * 100 if total_entries > 0 else 0

            # Breakdown by failure type
            failure_breakdown = {}
            if "status" in dnfs.columns:
                for failure_type in mechanical_failures:
                    count = len(dnfs[dnfs["status"].str.contains(failure_type, case=False, na=False)])
                    if count > 0:
                        failure_breakdown[failure_type.lower()] = count

            return MetricResult(
                self.name, round(mechanical_failure_rate, 1), constructor_id=constructor_id,
                metadata={
                    "total_entries": total_entries,
                    "mechanical_failures": mechanical_dnfs,
                    "total_dnfs": len(dnfs),
                    "failure_breakdown": failure_breakdown
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorFinishRate(BaseConstructorMetric):
    """Calculate percentage of races where both cars finish."""

    name = "constructor_finish_rate"
    description = "Percentage of races where both constructor cars finish"
    unit = "percentage"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            results = data_loader.get_constructor_results(season, constructor_id)

            if results.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No race results found"})

            # Group by race and check finishes
            race_finishes = (results
                           .groupby("raceId")
                           .agg({
                               "position": lambda x: sum(pd.notna(x) & (x > 0)),  # Count finishers
                               "driverId": "count"  # Count total entries
                           })
                           .reset_index())
            race_finishes.columns = ["raceId", "finishers", "total_cars"]

            total_races = len(race_finishes)
            both_cars_finish = len(race_finishes[race_finishes["finishers"] == race_finishes["total_cars"]])

            double_finish_rate = (both_cars_finish / total_races) * 100 if total_races > 0 else 0

            # Additional statistics
            at_least_one_finish = len(race_finishes[race_finishes["finishers"] > 0])
            no_finishers = len(race_finishes[race_finishes["finishers"] == 0])

            return MetricResult(
                self.name, round(double_finish_rate, 1), constructor_id=constructor_id,
                metadata={
                    "total_races": total_races,
                    "both_cars_finish": both_cars_finish,
                    "at_least_one_finish": at_least_one_finish,
                    "no_finishers": no_finishers
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorReliabilityIndex(BaseConstructorMetric):
    """Calculate overall reliability index combining various factors."""

    name = "constructor_reliability_index"
    description = "Composite reliability score (0-100, higher is better)"
    unit = "index"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            results = data_loader.get_constructor_results(season, constructor_id)

            if results.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No race results found"})

            total_entries = len(results)
            finishes = len(results[results["position"].notna() & (results["position"] > 0)])

            # Base reliability score (finish rate)
            finish_rate = (finishes / total_entries) * 100 if total_entries > 0 else 0

            # Points-scoring reliability (additional weight for competitive finishes)
            points_finishes = len(results[results["points"] > 0])
            points_reliability = (points_finishes / total_entries) * 100 if total_entries > 0 else 0

            # Race completion reliability (avoiding early retirements)
            # This would require lap completion data, so we'll use position-based proxy
            competitive_finishes = len(results[
                results["position"].notna() &
                (results["position"] > 0) &
                (results["position"] <= 15)
            ])
            competitive_reliability = (competitive_finishes / total_entries) * 100 if total_entries > 0 else 0

            # Combined reliability index (weighted average)
            reliability_index = (
                finish_rate * 0.4 +  # 40% weight on basic finishing
                points_reliability * 0.35 +  # 35% weight on points-scoring
                competitive_reliability * 0.25  # 25% weight on competitive finishes
            )

            # Reliability grade
            if reliability_index >= 90:
                grade = "Excellent"
            elif reliability_index >= 80:
                grade = "Very Good"
            elif reliability_index >= 70:
                grade = "Good"
            elif reliability_index >= 60:
                grade = "Average"
            else:
                grade = "Poor"

            return MetricResult(
                self.name, round(reliability_index, 1), constructor_id=constructor_id,
                metadata={
                    "total_entries": total_entries,
                    "finish_rate": round(finish_rate, 1),
                    "points_reliability": round(points_reliability, 1),
                    "competitive_reliability": round(competitive_reliability, 1),
                    "reliability_grade": grade
                }
            )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})


class ConstructorAverageReliability(BaseConstructorMetric):
    """Calculate average reliability across seasons."""

    name = "constructor_average_reliability"
    description = "Average reliability performance across all seasons"
    unit = "percentage"

    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        try:
            results = data_loader.get_constructor_results(season, constructor_id)

            if results.empty:
                return MetricResult(self.name, None, constructor_id=constructor_id,
                                  metadata={"error": "No race results found"})

            if season:
                # Single season analysis
                total_entries = len(results)
                finishes = len(results[results["position"].notna() & (results["position"] > 0)])
                reliability = (finishes / total_entries) * 100 if total_entries > 0 else 0

                return MetricResult(
                    self.name, round(reliability, 1), constructor_id=constructor_id,
                    metadata={
                        "season": int(season),
                        "total_entries": int(total_entries),
                        "finishes": int(finishes)
                    }
                )
            else:
                # Multi-season analysis
                season_reliability = []

                for year in results["year"].unique():
                    year_results = results[results["year"] == year]
                    year_entries = len(year_results)
                    year_finishes = len(year_results[year_results["position"].notna() & (year_results["position"] > 0)])

                    if year_entries > 0:
                        year_reliability = (year_finishes / year_entries) * 100
                        season_reliability.append({
                            "year": int(year),
                            "reliability": year_reliability,
                            "entries": int(year_entries),
                            "finishes": int(year_finishes)
                        })

                if not season_reliability:
                    return MetricResult(self.name, None, constructor_id=constructor_id,
                                      metadata={"error": "No valid seasonal data found"})

                avg_reliability = np.mean([s["reliability"] for s in season_reliability])
                reliability_by_year = {int(s["year"]): round(s["reliability"], 1) for s in season_reliability}

                return MetricResult(
                    self.name, round(avg_reliability, 1), constructor_id=constructor_id,
                    metadata={
                        "seasons_analyzed": len(season_reliability),
                        "reliability_by_year": reliability_by_year,
                        "best_season": int(max(season_reliability, key=lambda x: x["reliability"])["year"]),
                        "worst_season": int(min(season_reliability, key=lambda x: x["reliability"])["year"])
                    }
                )

        except Exception as e:
            return MetricResult(self.name, None, constructor_id=constructor_id,
                              metadata={"error": str(e)})