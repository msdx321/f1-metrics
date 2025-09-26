"""API routes for constructor information."""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
import logging

from backend.api.schemas import ConstructorInfo, RaceInfo
from backend.data.loader import data_loader

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/constructors", tags=["constructors"])


@router.get("/", response_model=List[ConstructorInfo])
async def get_all_constructors(
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    active_only: bool = False
):
    """Get all constructors, optionally filtered by year range."""
    try:
        constructors = data_loader.get_constructors()

        if active_only and start_year and end_year:
            # Filter constructors who participated in races within the year range
            active_constructor_ids = set()

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

                # Get unique constructor IDs from results
                if not results.empty:
                    active_constructor_ids = set(results["constructorId"].unique())

            # Filter constructors to only active ones
            constructors = constructors[constructors["constructorId"].isin(active_constructor_ids)]

        return [
            ConstructorInfo(
                constructor_id=int(row["constructorId"]),
                name=row["name"],
                nationality=row["nationality"],
                url=row["url"] if "url" in row else None
            )
            for _, row in constructors.iterrows()
        ]
    except Exception as e:
        logger.error(f"Error fetching constructors: {e}")
        raise HTTPException(status_code=500, detail="Error fetching constructors")


@router.get("/{constructor_id}", response_model=ConstructorInfo)
async def get_constructor(constructor_id: int):
    """Get specific constructor information."""
    try:
        constructors = data_loader.get_constructors()
        constructor_data = constructors[constructors["constructorId"] == constructor_id]

        if constructor_data.empty:
            raise HTTPException(status_code=404, detail="Constructor not found")

        row = constructor_data.iloc[0]
        return ConstructorInfo(
            constructor_id=int(row["constructorId"]),
            name=row["name"],
            nationality=row["nationality"],
            url=row["url"] if "url" in row else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching constructor {constructor_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching constructor")


@router.get("/{constructor_id}/races", response_model=List[RaceInfo])
async def get_constructor_races(
    constructor_id: int,
    season: Optional[int] = None,
    limit: Optional[int] = None
):
    """Get races where constructor participated."""
    try:
        # Get constructor results
        results = data_loader.get_constructor_results(
            season=season,
            constructor_id=constructor_id
        )

        if results.empty:
            return []

        # Convert to race info, removing duplicates
        races = results.groupby(["raceId", "year", "round", "name", "date"]).first().reset_index()

        race_list = [
            RaceInfo(
                race_id=int(row["raceId"]),
                year=int(row["year"]),
                round=int(row["round"]),
                name=row["name"],
                date=row["date"],
                circuit_name=row.get("circuitId")  # May need to join with circuits table
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
        logger.error(f"Error fetching races for constructor {constructor_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching constructor races")


@router.get("/search/{name_query}")
async def search_constructors(name_query: str) -> List[ConstructorInfo]:
    """Search constructors by name."""
    try:
        constructors = data_loader.get_constructors()

        # Search in name (case insensitive)
        name_query_lower = name_query.lower()
        matching_constructors = constructors[
            constructors["name"].str.lower().str.contains(name_query_lower, na=False)
        ]

        return [
            ConstructorInfo(
                constructor_id=int(row["constructorId"]),
                name=row["name"],
                nationality=row["nationality"],
                url=row["url"] if "url" in row else None
            )
            for _, row in matching_constructors.iterrows()
        ]

    except Exception as e:
        logger.error(f"Error searching constructors with query '{name_query}': {e}")
        raise HTTPException(status_code=500, detail="Error searching constructors")