"""API routes for metrics."""

from fastapi import APIRouter, HTTPException
from typing import List
import logging

from backend.api.schemas import MetricRequest, MetricResponse
from backend.data.loader import data_loader
from backend.metrics.driver.qualifying import (
    QualifyingPositionAverage,
    QualifyingConsistency,
    PolePositionRate
)
from backend.metrics.driver.race import (
    AverageFinishPosition,
    PointsPerRace,
    DNFRate,
    PodiumRate
)
from backend.metrics.driver.teammate import (
    TeammateQualifyingComparison,
    TeammateRaceComparison
)
from backend.metrics.constructor.championship import (
    ConstructorChampionshipPosition,
    ConstructorChampionshipWins,
    ConstructorPointsPerSeason,
    ConstructorPointsPerRace,
    ConstructorTopThreeFinishes
)
from backend.metrics.constructor.race_performance import (
    ConstructorWinRate,
    ConstructorPodiumRate,
    ConstructorRaceWins,
    ConstructorPodiumLockouts,
    ConstructorAverageFinishPosition,
    ConstructorPointsScoringRate,
    ConstructorFrontRowLockouts,
    ConstructorDoublePodiums
)
from backend.metrics.constructor.qualifying import (
    ConstructorPolePositionRate,
    ConstructorAverageQualifyingPosition,
    ConstructorQualifyingConsistency,
    ConstructorFrontRowStartRate,
    ConstructorTopTenQualifyingRate,
    ConstructorQualifyingAdvantage
)
from backend.metrics.constructor.reliability import (
    ConstructorDNFRate,
    ConstructorMechanicalFailureRate,
    ConstructorFinishRate,
    ConstructorReliabilityIndex,
    ConstructorAverageReliability
)
from backend.metrics.constructor.competitiveness import (
    ConstructorSeasonDominance,
    ConstructorConsistencyIndex,
    ConstructorCompetitivenessRating,
    ConstructorPerformanceConsistency,
    ConstructorRaceWinStreak,
    ConstructorSeasonalImprovement
)
from backend.metrics.constructor.pit_stops import (
    ConstructorAveragePitStopTime,
    ConstructorFastestPitStop,
    ConstructorPitStopConsistency,
    ConstructorSubThreeSecondStops,
    ConstructorPitStopEfficiency,
    ConstructorAveragePitStopsPerRace,
    ConstructorPitStopTimeImprovement,
    ConstructorPitStopReliability,
    ConstructorPitStopStrategicSuccess
)
from backend.metrics.constructor.lap_performance import (
    ConstructorAverageLapTime,
    ConstructorFastestLap,
    ConstructorLapTimeConsistency,
    ConstructorRacePace,
    ConstructorLapTimeImprovement,
    ConstructorTireManagement,
    ConstructorCompetitiveLapRate,
    ConstructorLapTimeVariability,
    ConstructorPaceDominance,
    ConstructorFuelAdjustedPace
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/metrics", tags=["metrics"])

# Initialize metric calculators
DRIVER_METRICS = {
    "qualifying_position_average": QualifyingPositionAverage(),
    "qualifying_consistency": QualifyingConsistency(),
    "pole_position_rate": PolePositionRate(),
    "average_finish_position": AverageFinishPosition(),
    "points_per_race": PointsPerRace(),
    "dnf_rate": DNFRate(),
    "podium_rate": PodiumRate(),
    "teammate_qualifying_comparison": TeammateQualifyingComparison(),
    "teammate_race_comparison": TeammateRaceComparison()
}

CONSTRUCTOR_METRICS = {
    # Championship metrics
    "constructor_championship_position": ConstructorChampionshipPosition(),
    "constructor_championship_wins": ConstructorChampionshipWins(),
    "constructor_points_per_season": ConstructorPointsPerSeason(),
    "constructor_points_per_race": ConstructorPointsPerRace(),
    "constructor_top_three_finishes": ConstructorTopThreeFinishes(),

    # Race performance metrics
    "constructor_win_rate": ConstructorWinRate(),
    "constructor_podium_rate": ConstructorPodiumRate(),
    "constructor_race_wins": ConstructorRaceWins(),
    "constructor_podium_lockouts": ConstructorPodiumLockouts(),
    "constructor_average_finish_position": ConstructorAverageFinishPosition(),
    "constructor_points_scoring_rate": ConstructorPointsScoringRate(),
    "constructor_front_row_lockouts": ConstructorFrontRowLockouts(),
    "constructor_double_podiums": ConstructorDoublePodiums(),

    # Qualifying metrics
    "constructor_pole_position_rate": ConstructorPolePositionRate(),
    "constructor_average_qualifying_position": ConstructorAverageQualifyingPosition(),
    "constructor_qualifying_consistency": ConstructorQualifyingConsistency(),
    "constructor_front_row_start_rate": ConstructorFrontRowStartRate(),
    "constructor_top_ten_qualifying_rate": ConstructorTopTenQualifyingRate(),
    "constructor_qualifying_advantage": ConstructorQualifyingAdvantage(),

    # Reliability metrics
    "constructor_dnf_rate": ConstructorDNFRate(),
    "constructor_mechanical_failure_rate": ConstructorMechanicalFailureRate(),
    "constructor_finish_rate": ConstructorFinishRate(),
    "constructor_reliability_index": ConstructorReliabilityIndex(),
    "constructor_average_reliability": ConstructorAverageReliability(),

    # Competitiveness metrics
    "constructor_season_dominance": ConstructorSeasonDominance(),
    "constructor_consistency_index": ConstructorConsistencyIndex(),
    "constructor_competitiveness_rating": ConstructorCompetitivenessRating(),
    "constructor_performance_consistency": ConstructorPerformanceConsistency(),
    "constructor_race_win_streak": ConstructorRaceWinStreak(),
    "constructor_seasonal_improvement": ConstructorSeasonalImprovement(),

    # Pit stop metrics
    "constructor_average_pit_stop_time": ConstructorAveragePitStopTime(),
    "constructor_fastest_pit_stop": ConstructorFastestPitStop(),
    "constructor_pit_stop_consistency": ConstructorPitStopConsistency(),
    "constructor_sub_three_second_stops": ConstructorSubThreeSecondStops(),
    "constructor_pit_stop_efficiency": ConstructorPitStopEfficiency(),
    "constructor_average_pit_stops_per_race": ConstructorAveragePitStopsPerRace(),
    "constructor_pit_stop_time_improvement": ConstructorPitStopTimeImprovement(),
    "constructor_pit_stop_reliability": ConstructorPitStopReliability(),
    "constructor_pit_stop_strategic_success": ConstructorPitStopStrategicSuccess(),

    # Lap performance metrics
    "constructor_average_lap_time": ConstructorAverageLapTime(),
    "constructor_fastest_lap": ConstructorFastestLap(),
    "constructor_lap_time_consistency": ConstructorLapTimeConsistency(),
    "constructor_race_pace": ConstructorRacePace(),
    "constructor_lap_time_improvement": ConstructorLapTimeImprovement(),
    "constructor_tire_management": ConstructorTireManagement(),
    "constructor_competitive_lap_rate": ConstructorCompetitiveLapRate(),
    "constructor_lap_time_variability": ConstructorLapTimeVariability(),
    "constructor_pace_dominance": ConstructorPaceDominance(),
    "constructor_fuel_adjusted_pace": ConstructorFuelAdjustedPace()
}


def _convert_metric_result_to_response(result) -> MetricResponse:
    """Convert MetricResult to MetricResponse."""
    constructor_name = result.constructor_name
    if not constructor_name and result.constructor_id:
        constructor_name = data_loader.get_constructor_name(result.constructor_id)

    return MetricResponse(
        metric_name=result.metric_name,
        value=result.value,
        driver_id=result.driver_id,
        driver_name=result.driver_name,
        constructor_id=result.constructor_id,
        constructor_name=constructor_name,
        season=result.season,
        metadata=result.metadata
    )


@router.get("/available")
async def get_available_metrics():
    """Get list of available metrics."""
    return {
        "driver_metrics": list(DRIVER_METRICS.keys()),
        "constructor_metrics": list(CONSTRUCTOR_METRICS.keys()),
        "comparison_metrics": [
            "teammate_qualifying_comparison",
            "teammate_race_comparison"
        ]
    }


@router.post("/driver/bulk")
async def calculate_multiple_driver_metrics(
    metric_names: List[str],
    request: MetricRequest
) -> List[MetricResponse]:
    """Calculate multiple driver metrics at once."""
    results = []
    errors = []

    for metric_name in metric_names:
        if metric_name not in DRIVER_METRICS:
            errors.append(f"Metric '{metric_name}' not found")
            continue

        try:
            metric_calculator = DRIVER_METRICS[metric_name]
            result = metric_calculator.calculate(
                driver_id=request.driver_id,
                constructor_id=request.constructor_id,
                season=request.season,
                race_ids=request.race_ids
            )
            results.append(_convert_metric_result_to_response(result))

        except Exception as e:
            logger.error(f"Error calculating metric {metric_name}: {e}")
            errors.append(f"Error calculating {metric_name}: {str(e)}")

    if errors and not results:
        raise HTTPException(
            status_code=400,
            detail={"errors": errors, "message": "No metrics could be calculated"}
        )

    return results


@router.post("/driver/{metric_name}")
async def calculate_driver_metric(metric_name: str, request: MetricRequest) -> MetricResponse:
    """Calculate a specific driver metric."""
    if metric_name not in DRIVER_METRICS:
        raise HTTPException(
            status_code=404,
            detail=f"Metric '{metric_name}' not found. Available metrics: {list(DRIVER_METRICS.keys())}"
        )

    try:
        metric_calculator = DRIVER_METRICS[metric_name]
        result = metric_calculator.calculate(
            driver_id=request.driver_id,
            constructor_id=request.constructor_id,
            season=request.season,
            race_ids=request.race_ids
        )

        return _convert_metric_result_to_response(result)

    except Exception as e:
        logger.error(f"Error calculating metric {metric_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating metric: {str(e)}"
        )


@router.get("/driver/{metric_name}/info")
async def get_metric_info(metric_name: str):
    """Get information about a specific metric."""
    if metric_name not in DRIVER_METRICS:
        raise HTTPException(
            status_code=404,
            detail=f"Metric '{metric_name}' not found"
        )

    metric = DRIVER_METRICS[metric_name]
    return {
        "name": metric.name,
        "description": metric.description,
        "required_data": metric.get_required_data(),
        "type": "driver_metric"
    }


# Constructor endpoints
@router.post("/constructor/bulk")
async def calculate_multiple_constructor_metrics(
    metric_names: List[str],
    request: MetricRequest
) -> List[MetricResponse]:
    """Calculate multiple constructor metrics at once."""
    if not request.constructor_id:
        raise HTTPException(
            status_code=400,
            detail="constructor_id is required for constructor metrics"
        )

    results = []
    errors = []

    for metric_name in metric_names:
        if metric_name not in CONSTRUCTOR_METRICS:
            errors.append(f"Metric '{metric_name}' not found")
            continue

        try:
            metric_calculator = CONSTRUCTOR_METRICS[metric_name]
            result = metric_calculator.calculate(
                constructor_id=request.constructor_id,
                season=request.season
            )
            results.append(_convert_metric_result_to_response(result))

        except Exception as e:
            logger.error(f"Error calculating constructor metric {metric_name}: {e}")
            errors.append(f"Error calculating {metric_name}: {str(e)}")

    if errors and not results:
        raise HTTPException(
            status_code=400,
            detail={"errors": errors, "message": "No metrics could be calculated"}
        )

    return results


@router.post("/constructor/{metric_name}")
async def calculate_constructor_metric(metric_name: str, request: MetricRequest) -> MetricResponse:
    """Calculate a specific constructor metric."""
    if metric_name not in CONSTRUCTOR_METRICS:
        raise HTTPException(
            status_code=404,
            detail=f"Metric '{metric_name}' not found. Available metrics: {list(CONSTRUCTOR_METRICS.keys())}"
        )

    if not request.constructor_id:
        raise HTTPException(
            status_code=400,
            detail="constructor_id is required for constructor metrics"
        )

    try:
        metric_calculator = CONSTRUCTOR_METRICS[metric_name]
        result = metric_calculator.calculate(
            constructor_id=request.constructor_id,
            season=request.season
        )

        return _convert_metric_result_to_response(result)

    except Exception as e:
        logger.error(f"Error calculating constructor metric {metric_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating metric: {str(e)}"
        )


@router.get("/constructor/{metric_name}/info")
async def get_constructor_metric_info(metric_name: str):
    """Get information about a specific constructor metric."""
    if metric_name not in CONSTRUCTOR_METRICS:
        raise HTTPException(
            status_code=404,
            detail=f"Metric '{metric_name}' not found"
        )

    metric = CONSTRUCTOR_METRICS[metric_name]
    return {
        "name": metric.name,
        "description": metric.description,
        "unit": metric.unit,
        "type": "constructor_metric"
    }