"""API routes for driver information."""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
import logging

from backend.api.schemas import DriverInfo, RaceInfo
from backend.data.loader import data_loader

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.get("/", response_model=List[DriverInfo])
async def get_all_drivers(
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    active_only: bool = False
):
    """Get all drivers, optionally filtered by year range."""
    try:
        drivers = data_loader.get_drivers()

        if active_only and start_year and end_year:
            # Filter drivers who participated in races within the year range
            active_driver_ids = set()

            # Get all races in the year range
            all_races = data_loader.get_races()
            year_races = all_races[
                (all_races["year"] >= start_year) &
                (all_races["year"] <= end_year)
            ]

            if not year_races.empty:
                # Get all results for races in this period
                race_ids = year_races["raceId"].tolist()
                results = data_loader.get_results(race_ids)

                # Get unique driver IDs from results
                if not results.empty:
                    active_driver_ids = set(results["driverId"].unique())

            # Filter drivers to only active ones
            drivers = drivers[drivers["driverId"].isin(active_driver_ids)]

        return [
            DriverInfo(
                driver_id=int(row["driverId"]),
                forename=row["forename"],
                surname=row["surname"],
                nationality=row["nationality"],
                dob=row["dob"] if "dob" in row else None,
                url=row["url"] if "url" in row else None
            )
            for _, row in drivers.iterrows()
        ]
    except Exception as e:
        logger.error(f"Error fetching drivers: {e}")
        raise HTTPException(status_code=500, detail="Error fetching drivers")


@router.get("/{driver_id}", response_model=DriverInfo)
async def get_driver(driver_id: int):
    """Get specific driver information."""
    try:
        drivers = data_loader.get_drivers()
        driver_data = drivers[drivers["driverId"] == driver_id]

        if driver_data.empty:
            raise HTTPException(status_code=404, detail="Driver not found")

        row = driver_data.iloc[0]
        return DriverInfo(
            driver_id=int(row["driverId"]),
            forename=row["forename"],
            surname=row["surname"],
            nationality=row["nationality"],
            dob=row["dob"] if "dob" in row else None,
            url=row["url"] if "url" in row else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching driver {driver_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching driver")


@router.get("/{driver_id}/races", response_model=List[RaceInfo])
async def get_driver_races(
    driver_id: int,
    season: Optional[int] = None,
    limit: Optional[int] = None
):
    """Get races where driver participated."""
    try:
        # Get driver results with race information
        results = data_loader.get_driver_results_with_names(
            driver_id=driver_id,
            season=season
        )

        if results.empty:
            return []

        # Convert to race info
        races = results.groupby(["raceId", "year", "round", "name", "date"]).first().reset_index()

        race_list = [
            RaceInfo(
                race_id=int(row["raceId"]),
                year=int(row["year"]),
                round=int(row["round"]),
                name=row["name"],
                date=row["date"],
                circuit_name=row.get("circuit_name")
            )
            for _, row in races.iterrows()
        ]

        # Sort by year and round
        race_list.sort(key=lambda x: (x.year, x.round))

        # Apply limit if specified
        if limit:
            race_list = race_list[-limit:]  # Get most recent races

        return race_list

    except Exception as e:
        logger.error(f"Error fetching races for driver {driver_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching driver races")


@router.get("/search/{name_query}")
async def search_drivers(name_query: str) -> List[DriverInfo]:
    """Search drivers by name."""
    try:
        drivers = data_loader.get_drivers()

        # Search in forename and surname (case insensitive)
        name_query_lower = name_query.lower()
        matching_drivers = drivers[
            drivers["forename"].str.lower().str.contains(name_query_lower, na=False) |
            drivers["surname"].str.lower().str.contains(name_query_lower, na=False) |
            (drivers["forename"] + " " + drivers["surname"]).str.lower().str.contains(name_query_lower, na=False)
        ]

        return [
            DriverInfo(
                driver_id=int(row["driverId"]),
                forename=row["forename"],
                surname=row["surname"],
                nationality=row["nationality"],
                dob=row["dob"] if "dob" in row else None,
                url=row["url"] if "url" in row else None
            )
            for _, row in matching_drivers.iterrows()
        ]

    except Exception as e:
        logger.error(f"Error searching drivers with query '{name_query}': {e}")
        raise HTTPException(status_code=500, detail="Error searching drivers")