"""F1 data loading utilities."""

import pandas as pd
from pathlib import Path
from typing import Dict, Optional, List
import logging
from backend.config import DATASET_DIR, MIN_YEAR

logger = logging.getLogger(__name__)


class F1DataLoader:
    """Handles loading and caching of F1 CSV data."""

    def __init__(self):
        self._data_cache: Dict[str, pd.DataFrame] = {}
        self._joined_cache: Dict[str, pd.DataFrame] = {}

    def load_csv(self, filename: str, use_cache: bool = True) -> pd.DataFrame:
        """Load a CSV file from the dataset directory."""
        if use_cache and filename in self._data_cache:
            return self._data_cache[filename].copy()

        filepath = DATASET_DIR / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Dataset file not found: {filepath}")

        try:
            df = pd.read_csv(filepath)
            logger.info(f"Loaded {filename}: {len(df)} rows")

            if use_cache:
                self._data_cache[filename] = df.copy()

            return df

        except Exception as e:
            logger.error(f"Failed to load {filename}: {e}")
            raise

    def get_races(self, season: Optional[int] = None) -> pd.DataFrame:
        """Get races data, optionally filtered by season."""
        races = self.load_csv("races.csv")

        # Filter by minimum year
        races = races[races["year"] >= MIN_YEAR]

        if season:
            races = races[races["year"] == season]

        return races.sort_values(["year", "round"])

    def get_results(self, race_ids: Optional[List[int]] = None) -> pd.DataFrame:
        """Get race results, optionally filtered by race IDs."""
        results = self.load_csv("results.csv")

        if race_ids is not None:
            results = results[results["raceId"].isin(race_ids)]

        return results

    def get_qualifying(self, race_ids: Optional[List[int]] = None) -> pd.DataFrame:
        """Get qualifying results, optionally filtered by race IDs."""
        qualifying = self.load_csv("qualifying.csv")

        if race_ids is not None:
            qualifying = qualifying[qualifying["raceId"].isin(race_ids)]

        return qualifying

    def get_lap_times(self, race_ids: Optional[List[int]] = None) -> pd.DataFrame:
        """Get lap times, optionally filtered by race IDs."""
        lap_times = self.load_csv("lap_times.csv")

        if race_ids is not None:
            lap_times = lap_times[lap_times["raceId"].isin(race_ids)]

        return lap_times

    def get_pit_stops(self, race_ids: Optional[List[int]] = None) -> pd.DataFrame:
        """Get pit stop data, optionally filtered by race IDs."""
        pit_stops = self.load_csv("pit_stops.csv")

        if race_ids is not None:
            pit_stops = pit_stops[pit_stops["raceId"].isin(race_ids)]

        return pit_stops

    def get_drivers(self) -> pd.DataFrame:
        """Get drivers data."""
        return self.load_csv("drivers.csv")

    def get_constructors(self) -> pd.DataFrame:
        """Get constructors data."""
        return self.load_csv("constructors.csv")

    def get_driver_results_with_names(
        self,
        driver_id: Optional[int] = None,
        season: Optional[int] = None,
        race_ids: Optional[List[int]] = None
    ) -> pd.DataFrame:
        """Get results joined with driver and race information."""
        cache_key = f"driver_results_{driver_id}_{season}_{hash(tuple(race_ids or []))}"

        if cache_key in self._joined_cache:
            return self._joined_cache[cache_key].copy()

        # Get races
        races = self.get_races(season)
        race_ids_filtered = race_ids or races["raceId"].tolist()

        # Get results
        results = self.get_results(race_ids_filtered)

        if driver_id:
            results = results[results["driverId"] == driver_id]

        # Join with races and drivers
        drivers = self.get_drivers()

        joined = (results
                 .merge(races, on="raceId", how="left")
                 .merge(drivers, on="driverId", how="left"))

        # Add computed columns
        joined["driver_name"] = joined["forename"] + " " + joined["surname"]

        self._joined_cache[cache_key] = joined.copy()
        return joined

    def get_teammate_pairs(self, season: Optional[int] = None) -> pd.DataFrame:
        """Get all teammate pairs for comparison metrics."""
        races = self.get_races(season)
        results = self.get_results(races["raceId"].tolist())

        # Get teammates (same constructor in same race)
        teammate_pairs = []
        for _, race in races.iterrows():
            race_results = results[results["raceId"] == race["raceId"]]

            for constructor_id in race_results["constructorId"].unique():
                constructor_drivers = race_results[
                    race_results["constructorId"] == constructor_id
                ]

                if len(constructor_drivers) == 2:
                    drivers = constructor_drivers["driverId"].tolist()
                    teammate_pairs.append({
                        "raceId": race["raceId"],
                        "year": race["year"],
                        "constructorId": constructor_id,
                        "driver1_id": drivers[0],
                        "driver2_id": drivers[1]
                    })

        return pd.DataFrame(teammate_pairs)

    def get_constructor_standings(self, season: Optional[int] = None) -> pd.DataFrame:
        """Get constructor standings data, optionally filtered by season."""
        standings = self.load_csv("constructor_standings.csv")

        if season:
            # Get race IDs for the season
            races = self.get_races(season)
            standings = standings[standings["raceId"].isin(races["raceId"])]
        else:
            # Filter by minimum year
            races = self.get_races()  # Already filtered by MIN_YEAR
            standings = standings[standings["raceId"].isin(races["raceId"])]

        return standings

    def get_constructor_results(self, season: Optional[int] = None,
                               constructor_id: Optional[int] = None) -> pd.DataFrame:
        """Get constructor results by aggregating driver results."""
        races = self.get_races(season)
        results = self.get_results(races["raceId"].tolist())

        if constructor_id:
            results = results[results["constructorId"] == constructor_id]

        # Join with race data for context
        constructor_results = (results
                              .merge(races, on="raceId", how="left")
                              .merge(self.get_constructors(), on="constructorId", how="left"))

        # Ensure numeric columns
        constructor_results["position"] = pd.to_numeric(constructor_results["position"], errors="coerce")
        constructor_results["points"] = pd.to_numeric(constructor_results["points"], errors="coerce").fillna(0)

        return constructor_results

    def get_constructor_championship_positions(self, season: Optional[int] = None) -> pd.DataFrame:
        """Get final constructor championship positions by season."""
        standings = self.get_constructor_standings(season)

        if standings.empty:
            return pd.DataFrame()

        # Join with races to get year information
        races = self.get_races()
        standings_with_year = standings.merge(races[["raceId", "year", "round"]], on="raceId", how="left")

        # Get final standings (last race of each season)
        final_standings = (standings_with_year
                          .groupby(["year", "constructorId"])
                          .last()
                          .reset_index())

        return final_standings

    def get_constructor_race_wins(self, season: Optional[int] = None,
                                 constructor_id: Optional[int] = None) -> pd.DataFrame:
        """Get races won by constructors (1st and 2nd place)."""
        results = self.get_constructor_results(season, constructor_id)

        # Group by race and constructor to count positions
        race_results = (results
                       .groupby(["raceId", "constructorId", "year", "round"])
                       .agg({
                           "position": ["min", "max", "count"],
                           "points": "sum"
                       })
                       .reset_index())

        # Flatten column names
        race_results.columns = ["raceId", "constructorId", "year", "round",
                               "best_position", "worst_position", "drivers_count", "total_points"]

        # Constructor wins: both cars finish 1st and 2nd
        constructor_wins = race_results[
            (race_results["best_position"] == 1) &
            (race_results["worst_position"] == 2) &
            (race_results["drivers_count"] == 2)
        ]

        return constructor_wins

    def get_constructor_podium_lockouts(self, season: Optional[int] = None,
                                       constructor_id: Optional[int] = None) -> pd.DataFrame:
        """Get races where constructor achieved podium lockouts (1-2 or 1-2-3)."""
        results = self.get_constructor_results(season, constructor_id)

        # Get podium results only
        podium_results = results[results["position"].isin([1, 2, 3])]

        # Count podium positions by race and constructor
        podium_counts = (podium_results
                        .groupby(["raceId", "constructorId", "year", "round"])
                        .agg({
                            "position": ["min", "count"],
                            "driverId": "count"
                        })
                        .reset_index())

        # Flatten column names
        podium_counts.columns = ["raceId", "constructorId", "year", "round",
                                "best_position", "podium_positions", "drivers_count"]

        # 1-2 lockouts: constructor has both 1st and 2nd
        lockouts_12 = podium_counts[
            (podium_counts["best_position"] == 1) &
            (podium_counts["podium_positions"] >= 2)
        ]

        return lockouts_12

    def get_constructor_qualifying_performance(self, season: Optional[int] = None,
                                              constructor_id: Optional[int] = None) -> pd.DataFrame:
        """Get constructor qualifying performance data."""
        races = self.get_races(season)
        qualifying = self.get_qualifying(races["raceId"].tolist())

        if constructor_id:
            # Get results to find constructor info
            results = self.get_results(races["raceId"].tolist())
            driver_constructor_map = results.groupby("driverId")["constructorId"].first().to_dict()

            # Filter qualifying by constructor
            qualifying["constructorId"] = qualifying["driverId"].map(driver_constructor_map)
            qualifying = qualifying[qualifying["constructorId"] == constructor_id]

        # Join with race and constructor data
        qual_performance = (qualifying
                           .merge(races, on="raceId", how="left"))

        return qual_performance

    def get_constructor_reliability_data(self, season: Optional[int] = None,
                                        constructor_id: Optional[int] = None) -> pd.DataFrame:
        """Get constructor reliability data (DNFs, mechanical failures)."""
        results = self.get_constructor_results(season, constructor_id)

        # Get status data for failure analysis
        status_data = self.load_csv("status.csv")

        # Join results with status information
        reliability_data = (results
                           .merge(status_data, left_on="statusId", right_on="statusId", how="left"))

        return reliability_data

    def get_constructor_pit_stop_performance(self, season: Optional[int] = None,
                                           constructor_id: Optional[int] = None) -> pd.DataFrame:
        """Get constructor pit stop performance data."""
        races = self.get_races(season)
        pit_stops = self.get_pit_stops(races["raceId"].tolist())

        if constructor_id:
            # Get results to map drivers to constructors
            results = self.get_results(races["raceId"].tolist())
            driver_constructor_map = results.groupby("driverId")["constructorId"].first().to_dict()

            # Filter pit stops by constructor
            pit_stops["constructorId"] = pit_stops["driverId"].map(driver_constructor_map)
            pit_stops = pit_stops[pit_stops["constructorId"] == constructor_id]

        return pit_stops

    def get_constructor_points_data(self, season: Optional[int] = None,
                                   constructor_id: Optional[int] = None) -> pd.DataFrame:
        """Get detailed constructor points data by race."""
        results = self.get_constructor_results(season, constructor_id)

        if results.empty:
            return pd.DataFrame()

        # Ensure numeric columns
        results["points"] = pd.to_numeric(results["points"], errors="coerce").fillna(0)
        results["position"] = pd.to_numeric(results["position"], errors="coerce")

        # Aggregate points by constructor and race
        points_data = (results
                      .groupby(["raceId", "constructorId", "year", "round"])
                      .agg({
                          "points": "sum",
                          "position": ["min", "mean", "count"]
                      })
                      .reset_index())

        # Flatten column names
        points_data.columns = ["raceId", "constructorId", "year", "round",
                              "total_points", "best_finish", "avg_finish", "cars_finished"]

        return points_data

    def get_constructor_lap_times(self, season: Optional[int] = None,
                                  constructor_id: Optional[int] = None) -> pd.DataFrame:
        """Get constructor lap times with race and constructor context."""
        races = self.get_races(season)
        lap_times = self.get_lap_times(races["raceId"].tolist())

        if lap_times.empty:
            return pd.DataFrame()

        if constructor_id:
            # Get results to map drivers to constructors
            results = self.get_results(races["raceId"].tolist())
            driver_constructor_map = results.groupby("driverId")["constructorId"].first().to_dict()

            # Filter lap times by constructor
            lap_times["constructorId"] = lap_times["driverId"].map(driver_constructor_map)
            lap_times = lap_times[lap_times["constructorId"] == constructor_id]

        # Join with race data for context
        lap_times_with_context = (lap_times
                                .merge(races[["raceId", "year", "round", "name", "date"]],
                                       on="raceId", how="left"))

        # Ensure numeric columns
        lap_times_with_context["milliseconds"] = pd.to_numeric(
            lap_times_with_context["milliseconds"], errors="coerce")

        return lap_times_with_context

    def get_constructor_pit_stop_stats(self, season: Optional[int] = None,
                                     constructor_id: Optional[int] = None) -> pd.DataFrame:
        """Get constructor pit stop statistics with aggregated data."""
        pit_stops = self.get_constructor_pit_stop_performance(season, constructor_id)

        if pit_stops.empty:
            return pd.DataFrame()

        # Ensure numeric columns
        pit_stops["milliseconds"] = pd.to_numeric(pit_stops["milliseconds"], errors="coerce")
        pit_stops["lap"] = pd.to_numeric(pit_stops["lap"], errors="coerce")
        pit_stops["stop"] = pd.to_numeric(pit_stops["stop"], errors="coerce")

        return pit_stops

    def get_constructor_lap_performance(self, season: Optional[int] = None,
                                      constructor_id: Optional[int] = None) -> pd.DataFrame:
        """Get constructor lap performance with statistical analysis."""
        lap_times = self.get_constructor_lap_times(season, constructor_id)

        if lap_times.empty:
            return pd.DataFrame()

        # Add derived columns for analysis
        lap_times["seconds"] = lap_times["milliseconds"] / 1000

        # Group by race and constructor for race-level statistics
        race_stats = (lap_times
                     .groupby(["raceId", "constructorId", "year", "round"])
                     .agg({
                         "milliseconds": ["mean", "min", "max", "std", "count"],
                         "seconds": ["mean", "min", "max", "std"]
                     })
                     .reset_index())

        # Flatten column names
        race_stats.columns = ["raceId", "constructorId", "year", "round",
                             "avg_lap_time_ms", "fastest_lap_ms", "slowest_lap_ms",
                             "lap_time_std_ms", "total_laps",
                             "avg_lap_time_s", "fastest_lap_s", "slowest_lap_s", "lap_time_std_s"]

        return race_stats

    def get_constructor_name(self, constructor_id: int) -> Optional[str]:
        """Get constructor name by ID."""
        constructors = self.get_constructors()
        constructor_row = constructors[constructors["constructorId"] == constructor_id]

        if constructor_row.empty:
            return None

        return constructor_row.iloc[0]["name"]

    def clear_cache(self):
        """Clear all cached data."""
        self._data_cache.clear()
        self._joined_cache.clear()
        logger.info("Data cache cleared")


# Global instance
data_loader = F1DataLoader()