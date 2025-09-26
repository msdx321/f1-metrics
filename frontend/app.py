"""Streamlit frontend for F1 Performance Metrics."""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any, Optional
import logging

# Configure page
st.set_page_config(
    page_title="F1 Performance Metrics",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API configuration - Use Streamlit secrets for deployment
def get_api_base_url():
    """Get API base URL from secrets or default to localhost for development."""
    try:
        return st.secrets["api"]["base_url"]
    except (KeyError, FileNotFoundError):
        # Fallback to localhost for local development
        return "http://localhost:8000/api/v1"

API_BASE_URL = get_api_base_url()


class APIClient:
    """Client for interacting with the F1 Metrics API."""

    def __init__(self, base_url: str):
        self.base_url = base_url

    def get_drivers(self, start_year: Optional[int] = None, end_year: Optional[int] = None, active_only: bool = False) -> List[Dict]:
        """Get drivers with optional filtering."""
        try:
            params = {}
            if start_year is not None:
                params['start_year'] = start_year
            if end_year is not None:
                params['end_year'] = end_year
            if active_only:
                params['active_only'] = active_only

            response = requests.get(f"{self.base_url}/drivers/", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Failed to fetch drivers: {e}")
            return []

    def search_drivers(self, query: str) -> List[Dict]:
        """Search drivers by name."""
        try:
            response = requests.get(f"{self.base_url}/drivers/search/{query}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Failed to search drivers: {e}")
            return []

    def get_constructors(self, start_year: Optional[int] = None, end_year: Optional[int] = None, active_only: bool = False) -> List[Dict]:
        """Get constructors with optional filtering."""
        try:
            params = {}
            if start_year is not None:
                params['start_year'] = start_year
            if end_year is not None:
                params['end_year'] = end_year
            if active_only:
                params['active_only'] = active_only

            response = requests.get(f"{self.base_url}/constructors/", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Failed to fetch constructors: {e}")
            return []

    def search_constructors(self, query: str) -> List[Dict]:
        """Search constructors by name."""
        try:
            response = requests.get(f"{self.base_url}/constructors/search/{query}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Failed to search constructors: {e}")
            return []

    def get_available_metrics(self) -> Dict:
        """Get available metrics."""
        try:
            response = requests.get(f"{self.base_url}/metrics/available")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Failed to fetch available metrics: {e}")
            return {"driver_metrics": [], "constructor_metrics": [], "comparison_metrics": []}

    def get_metric_info(self, metric_name: str) -> Dict:
        """Get metric information."""
        try:
            response = requests.get(f"{self.base_url}/metrics/driver/{metric_name}/info")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch metric info for {metric_name}: {e}")
            return {}

    def calculate_metric(self, metric_name: str, request_data: Dict) -> Dict:
        """Calculate a specific metric."""
        try:
            response = requests.post(
                f"{self.base_url}/metrics/driver/{metric_name}",
                json=request_data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Failed to calculate metric {metric_name}: {e}")
            return {}

    def calculate_bulk_metrics(self, metric_names: List[str], request_data: Dict) -> List[Dict]:
        """Calculate multiple metrics at once."""
        try:
            payload = {
                "metric_names": metric_names,
                "request": request_data
            }
            response = requests.post(
                f"{self.base_url}/metrics/driver/bulk",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Failed to calculate bulk metrics: {e}")
            return []

    def calculate_constructor_metric(self, metric_name: str, request_data: Dict) -> Dict:
        """Calculate a constructor metric."""
        try:
            response = requests.post(
                f"{self.base_url}/metrics/constructor/{metric_name}",
                json=request_data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Failed to calculate constructor metric {metric_name}: {e}")
            return {}

    def calculate_bulk_constructor_metrics(self, metric_names: List[str], request_data: Dict) -> List[Dict]:
        """Calculate multiple constructor metrics at once."""
        try:
            payload = {
                "metric_names": metric_names,
                "request": request_data
            }
            response = requests.post(
                f"{self.base_url}/metrics/constructor/bulk",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Failed to calculate bulk constructor metrics: {e}")
            return []

    def get_constructor_metric_info(self, metric_name: str) -> Dict:
        """Get constructor metric information."""
        try:
            response = requests.get(f"{self.base_url}/metrics/constructor/{metric_name}/info")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch constructor metric info for {metric_name}: {e}")
            return {}

    def get_driver_races(self, driver_id: int, season: Optional[int] = None, limit: Optional[int] = None) -> List[Dict]:
        """Get races where driver participated."""
        try:
            params = {}
            if season:
                params["season"] = season
            if limit:
                params["limit"] = limit

            response = requests.get(f"{self.base_url}/drivers/{driver_id}/races", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch races for driver {driver_id}: {e}")
            return []

    def get_constructor_races(self, constructor_id: int, season: Optional[int] = None, limit: Optional[int] = None) -> List[Dict]:
        """Get races where constructor participated."""
        try:
            params = {}
            if season:
                params["season"] = season
            if limit:
                params["limit"] = limit

            response = requests.get(f"{self.base_url}/constructors/{constructor_id}/races", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch races for constructor {constructor_id}: {e}")
            return []


# Initialize API client
@st.cache_resource
def get_api_client():
    return APIClient(API_BASE_URL)


# Cache drivers data
@st.cache_data(ttl=3600)
def get_drivers():
    client = get_api_client()
    return client.get_drivers()

# Cache constructors data
@st.cache_data(ttl=3600)
def get_constructors():
    client = get_api_client()
    return client.get_constructors()


@st.cache_data(ttl=3600)
def get_filtered_drivers(start_year: int = 2011, end_year: int = 2024) -> List[Dict]:
    """Get drivers who were active between start_year and end_year, with caching."""
    client = get_api_client()
    return client.get_drivers(start_year=start_year, end_year=end_year, active_only=True)


@st.cache_data(ttl=3600)
def get_filtered_constructors(start_year: int = 2011, end_year: int = 2024) -> List[Dict]:
    """Get constructors who were active between start_year and end_year, with caching."""
    client = get_api_client()
    return client.get_constructors(start_year=start_year, end_year=end_year, active_only=True)


# Cache available metrics
@st.cache_data(ttl=3600)
def get_available_metrics():
    client = get_api_client()
    raw_metrics = client.get_available_metrics()

    # Remove duplicates from driver_metrics that also appear in comparison_metrics
    if raw_metrics and "driver_metrics" in raw_metrics and "comparison_metrics" in raw_metrics:
        comparison_set = set(raw_metrics["comparison_metrics"])
        # Keep driver metrics that are not in comparison_metrics
        raw_metrics["driver_metrics"] = [
            metric for metric in raw_metrics["driver_metrics"]
            if metric not in comparison_set
        ]

    return raw_metrics


def format_metric_value(value: Any, metric_name: str) -> str:
    """Format metric value for display."""
    if value is None:
        return "N/A"

    if isinstance(value, dict):
        if "overall_win_rate" in value:
            return f"{value['overall_win_rate']}% ({value['record']})"
        return str(value)

    if isinstance(value, (int, float)):
        if "rate" in metric_name or "percentage" in metric_name:
            return f"{value}%"
        elif "position" in metric_name:
            return f"P{value}"
        elif "points" in metric_name:
            return f"{value} pts"
        else:
            return str(value)

    return str(value)


def create_metric_card(metric_name: str, result: Dict, info: Dict):
    """Create a metric card display."""
    with st.container():
        st.subheader(metric_name.replace("_", " ").title())

        if info:
            st.caption(info.get("description", "No description available"))

        value = result.get("value")
        formatted_value = format_metric_value(value, metric_name)

        # Main metric value
        col1, col2 = st.columns([2, 1])
        with col1:
            st.metric(
                label="Value",
                value=formatted_value
            )

        # Metadata
        metadata = result.get("metadata", {})
        if metadata:
            with st.expander("Details"):
                for key, val in metadata.items():
                    if val is not None:
                        st.write(f"**{key.replace('_', ' ').title()}:** {val}")

        # Special handling for teammate comparisons
        if isinstance(value, dict) and "teammate_breakdown" in value:
            st.write("**Teammate Breakdown:**")
            for teammate, stats in value["teammate_breakdown"].items():
                st.write(f"- **{teammate}:** {stats['win_rate']}% ({stats['wins']}-{stats['total'] - stats['wins']})")


def render_driver_metrics():
    """Render the driver metrics interface."""
    # Get drivers and metrics (filtered to 2011-2024 period)
    drivers = get_filtered_drivers()
    available_metrics = get_available_metrics()

    if not drivers:
        st.error("Failed to load drivers data. Please check if the API is running.")
        return

    # Driver selection
    driver_options = {f"{d['forename']} {d['surname']}": d['driver_id'] for d in drivers}
    selected_driver_name = st.selectbox("Select Driver", options=list(driver_options.keys()))
    selected_driver_id = driver_options[selected_driver_name]

    # Season filter
    current_year = 2024
    season_options = ["All Seasons"] + list(range(current_year, 2010, -1))
    selected_season = st.selectbox("Season", options=season_options)
    season_value = None if selected_season == "All Seasons" else selected_season

    # Metric selection
    st.subheader("Metrics")
    driver_metrics = available_metrics.get("driver_metrics", [])

    if not driver_metrics:
        st.error("No metrics available. Please check the API.")
        return

    # Group metrics by category
    qualifying_metrics = [m for m in driver_metrics if "qualifying" in m or "pole" in m]
    race_metrics = [m for m in driver_metrics if any(keyword in m for keyword in ["finish", "points", "dnf", "podium"])]
    comparison_metrics = [m for m in driver_metrics if "teammate" in m]

    # Metric category selection
    col1, col2, col3 = st.columns(3)
    with col1:
        show_qualifying = st.checkbox("Qualifying Metrics", value=True)
    with col2:
        show_race = st.checkbox("Race Performance Metrics", value=True)
    with col3:
        show_comparison = st.checkbox("Teammate Comparisons", value=True)

    selected_metrics = []
    if show_qualifying:
        selected_metrics.extend(qualifying_metrics)
    if show_race:
        selected_metrics.extend(race_metrics)
    if show_comparison:
        selected_metrics.extend(comparison_metrics)

    if not selected_metrics:
        st.warning("Please select at least one metric category.")
        return

    # Calculate metrics button
    if st.button("Calculate Driver Metrics", type="primary"):
        with st.spinner("Calculating metrics..."):
            client = get_api_client()

            # Prepare request
            request_data = {
                "driver_id": selected_driver_id,
                "season": season_value
            }

            # Calculate metrics
            results = []
            metric_info = {}

            for metric_name in selected_metrics:
                try:
                    result = client.calculate_metric(metric_name, request_data)
                    if result:
                        results.append(result)

                    # Get metric info
                    info = client.get_metric_info(metric_name)
                    metric_info[metric_name] = info

                except Exception as e:
                    st.error(f"Failed to calculate {metric_name}: {e}")

            # Display results
            if results:
                st.success(f"Calculated {len(results)} metrics for {selected_driver_name}")

                # Display driver info
                st.header(f"Performance Metrics: {selected_driver_name}")
                if season_value:
                    st.subheader(f"Season: {season_value}")
                else:
                    st.subheader("All Seasons (2011+)")

                # Group results by category
                qualifying_results = [r for r in results if any(keyword in r['metric_name'] for keyword in ["qualifying", "pole"])]
                race_results = [r for r in results if any(keyword in r['metric_name'] for keyword in ["finish", "points", "dnf", "podium"])]
                comparison_results = [r for r in results if "teammate" in r['metric_name']]

                # Display qualifying metrics
                if qualifying_results and show_qualifying:
                    st.header("🏁 Qualifying Performance")
                    cols = st.columns(len(qualifying_results))
                    for i, result in enumerate(qualifying_results):
                        with cols[i]:
                            metric_name = result['metric_name']
                            create_metric_card(metric_name, result, metric_info.get(metric_name, {}))

                # Display race metrics
                if race_results and show_race:
                    st.header("🏆 Race Performance")
                    cols = st.columns(min(len(race_results), 3))
                    for i, result in enumerate(race_results):
                        with cols[i % 3]:
                            metric_name = result['metric_name']
                            create_metric_card(metric_name, result, metric_info.get(metric_name, {}))

                # Display comparison metrics
                if comparison_results and show_comparison:
                    st.header("👥 Teammate Comparisons")
                    for result in comparison_results:
                        metric_name = result['metric_name']
                        create_metric_card(metric_name, result, metric_info.get(metric_name, {}))

            else:
                st.warning("No metrics could be calculated. This might be due to insufficient data.")


def render_constructor_metrics():
    """Render the constructor metrics interface."""
    # Get constructors and metrics (filtered to 2011-2024 period)
    constructors = get_filtered_constructors()
    available_metrics = get_available_metrics()

    if not constructors:
        st.error("Failed to load constructors data. Please check if the API is running.")
        return

    # Constructor selection
    constructor_options = {c['name']: c['constructor_id'] for c in constructors}
    selected_constructor_name = st.selectbox("Select Constructor", options=list(constructor_options.keys()))
    selected_constructor_id = constructor_options[selected_constructor_name]

    # Season filter
    current_year = 2024
    season_options = ["All Seasons"] + list(range(current_year, 2010, -1))
    selected_season = st.selectbox("Season", options=season_options, key="constructor_season")
    season_value = None if selected_season == "All Seasons" else selected_season

    # Metric selection
    st.subheader("Constructor Metrics")
    constructor_metrics = available_metrics.get("constructor_metrics", [])

    if not constructor_metrics:
        st.error("No constructor metrics available. Please check the API.")
        return

    # Group constructor metrics by category
    championship_metrics = [m for m in constructor_metrics if "championship" in m]
    race_perf_metrics = [m for m in constructor_metrics if any(keyword in m for keyword in ["win_rate", "podium", "finish", "points"])]
    qualifying_metrics = [m for m in constructor_metrics if "qualifying" in m or "pole" in m or "front_row" in m]
    reliability_metrics = [m for m in constructor_metrics if "dnf" in m or "reliability" in m or "mechanical" in m or "finish_rate" in m]
    competitiveness_metrics = [m for m in constructor_metrics if any(keyword in m for keyword in ["season_dominance", "consistency_index", "competitiveness", "streak", "seasonal_improvement"])]
    pit_stop_metrics = [m for m in constructor_metrics if "pit_stop" in m]
    lap_performance_metrics = [m for m in constructor_metrics if any(keyword in m for keyword in ["lap_time", "race_pace", "fastest_lap", "tire", "competitive", "variability", "dominance", "fuel"])]

    # Metric category selection
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        show_championship = st.checkbox("Championship", value=True)
        show_race_perf = st.checkbox("Race Performance", value=True)
    with col2:
        show_qual = st.checkbox("Qualifying", value=True)
        show_reliability = st.checkbox("Reliability", value=True)
    with col3:
        show_competitiveness = st.checkbox("Competitiveness", value=False)
        show_pit_stops = st.checkbox("Pit Stops", value=False)
    with col4:
        show_lap_performance = st.checkbox("Lap Performance", value=False)

    selected_metrics = []
    if show_championship:
        selected_metrics.extend(championship_metrics)
    if show_race_perf:
        selected_metrics.extend(race_perf_metrics)
    if show_qual:
        selected_metrics.extend(qualifying_metrics)
    if show_reliability:
        selected_metrics.extend(reliability_metrics)
    if show_competitiveness:
        selected_metrics.extend(competitiveness_metrics)
    if show_pit_stops:
        selected_metrics.extend(pit_stop_metrics)
    if show_lap_performance:
        selected_metrics.extend(lap_performance_metrics)

    if not selected_metrics:
        st.warning("Please select at least one metric category.")
        return

    # Calculate metrics button
    if st.button("Calculate Constructor Metrics", type="primary"):
        with st.spinner("Calculating constructor metrics..."):
            client = get_api_client()

            # Prepare request
            request_data = {
                "constructor_id": selected_constructor_id,
                "season": season_value
            }

            # Calculate metrics
            results = []
            metric_info = {}

            for metric_name in selected_metrics:
                try:
                    result = client.calculate_constructor_metric(metric_name, request_data)
                    if result:
                        results.append(result)

                    # Get metric info
                    info = client.get_constructor_metric_info(metric_name)
                    metric_info[metric_name] = info

                except Exception as e:
                    st.error(f"Failed to calculate {metric_name}: {e}")

            # Display results
            if results:
                st.success(f"Calculated {len(results)} metrics for {selected_constructor_name}")

                # Display constructor info
                st.header(f"Constructor Performance: {selected_constructor_name}")
                if season_value:
                    st.subheader(f"Season: {season_value}")
                else:
                    st.subheader("All Seasons (2011+)")

                # Group results by category
                championship_results = [r for r in results if "championship" in r['metric_name']]
                race_perf_results = [r for r in results if any(keyword in r['metric_name'] for keyword in ["win_rate", "podium", "finish", "points"])]
                qual_results = [r for r in results if "qualifying" in r['metric_name'] or "pole" in r['metric_name'] or "front_row" in r['metric_name']]
                reliability_results = [r for r in results if any(keyword in r['metric_name'] for keyword in ["dnf", "reliability", "mechanical", "finish_rate"])]
                competitiveness_results = [r for r in results if any(keyword in r['metric_name'] for keyword in ["season_dominance", "consistency_index", "competitiveness", "streak", "seasonal_improvement"])]
                pit_stop_results = [r for r in results if "pit_stop" in r['metric_name']]
                lap_performance_results = [r for r in results if any(keyword in r['metric_name'] for keyword in ["lap_time", "race_pace", "fastest_lap", "tire", "competitive", "variability", "dominance", "fuel"])]

                # Display championship metrics
                if championship_results and show_championship:
                    st.header("🏆 Championship Performance")
                    cols = st.columns(min(len(championship_results), 3))
                    for i, result in enumerate(championship_results):
                        with cols[i % 3]:
                            metric_name = result['metric_name']
                            create_metric_card(metric_name, result, metric_info.get(metric_name, {}))

                # Display race performance metrics
                if race_perf_results and show_race_perf:
                    st.header("🏁 Race Performance")
                    cols = st.columns(min(len(race_perf_results), 3))
                    for i, result in enumerate(race_perf_results):
                        with cols[i % 3]:
                            metric_name = result['metric_name']
                            create_metric_card(metric_name, result, metric_info.get(metric_name, {}))

                # Display qualifying metrics
                if qual_results and show_qual:
                    st.header("🚦 Qualifying Performance")
                    cols = st.columns(min(len(qual_results), 3))
                    for i, result in enumerate(qual_results):
                        with cols[i % 3]:
                            metric_name = result['metric_name']
                            create_metric_card(metric_name, result, metric_info.get(metric_name, {}))

                # Display reliability metrics
                if reliability_results and show_reliability:
                    st.header("🔧 Reliability")
                    cols = st.columns(min(len(reliability_results), 3))
                    for i, result in enumerate(reliability_results):
                        with cols[i % 3]:
                            metric_name = result['metric_name']
                            create_metric_card(metric_name, result, metric_info.get(metric_name, {}))

                # Display competitiveness metrics
                if competitiveness_results and show_competitiveness:
                    st.header("📊 Competitiveness")
                    cols = st.columns(min(len(competitiveness_results), 3))
                    for i, result in enumerate(competitiveness_results):
                        with cols[i % 3]:
                            metric_name = result['metric_name']
                            create_metric_card(metric_name, result, metric_info.get(metric_name, {}))

                # Display pit stop metrics
                if pit_stop_results and show_pit_stops:
                    st.header("⚡ Pit Stop Performance")
                    cols = st.columns(min(len(pit_stop_results), 3))
                    for i, result in enumerate(pit_stop_results):
                        with cols[i % 3]:
                            metric_name = result['metric_name']
                            create_metric_card(metric_name, result, metric_info.get(metric_name, {}))

                # Display lap performance metrics
                if lap_performance_results and show_lap_performance:
                    st.header("🏁 Lap Performance")
                    cols = st.columns(min(len(lap_performance_results), 3))
                    for i, result in enumerate(lap_performance_results):
                        with cols[i % 3]:
                            metric_name = result['metric_name']
                            create_metric_card(metric_name, result, metric_info.get(metric_name, {}))

            else:
                st.warning("No metrics could be calculated. This might be due to insufficient data.")


def render_comparison_page():
    """Render the comparison page for drivers and constructors."""
    st.header("⚖️ Performance Comparison")
    st.write("Compare two drivers or two constructors side by side")

    # Choose comparison type
    comparison_type = st.selectbox(
        "What would you like to compare?",
        ["👤 Drivers", "🏗️ Constructors"],
        index=0
    )

    if comparison_type == "👤 Drivers":
        render_driver_comparison()
    else:
        render_constructor_comparison()


def render_driver_comparison():
    """Render driver comparison interface."""
    st.subheader("👤 Driver Comparison")

    client = APIClient(API_BASE_URL)
    drivers = get_filtered_drivers()

    if not drivers:
        st.error("Could not load drivers data")
        return

    # Create two columns for driver selection
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Driver A**")
        driver_a = st.selectbox(
            "Select first driver",
            drivers,
            format_func=lambda x: f"{x['forename']} {x['surname']}",
            key="driver_a"
        )
        season_a = st.selectbox(
            "Season (All seasons if none)",
            [None] + list(range(2011, 2025)),
            index=0,
            key="season_a"
        )

    with col2:
        st.markdown("**Driver B**")
        driver_b = st.selectbox(
            "Select second driver",
            drivers,
            format_func=lambda x: f"{x['forename']} {x['surname']}",
            key="driver_b"
        )
        season_b = st.selectbox(
            "Season (All seasons if none)",
            [None] + list(range(2011, 2025)),
            index=0,
            key="season_b"
        )

    # Select metrics to compare
    available_metrics = client.get_available_metrics()
    if not available_metrics or "driver_metrics" not in available_metrics:
        st.error("Could not load available metrics")
        return

    selected_metrics = st.multiselect(
        "Select metrics to compare",
        available_metrics["driver_metrics"],
        default=["average_finish_position", "points_per_race", "pole_position_rate", "podium_rate"]
    )

    if st.button("🔍 Compare Drivers"):
        if driver_a and driver_b and selected_metrics:
            if driver_a["driver_id"] == driver_b["driver_id"] and season_a == season_b:
                st.warning("Please select different drivers or different seasons")
                return

            compare_drivers(client, driver_a, driver_b, season_a, season_b, selected_metrics)


def render_constructor_comparison():
    """Render constructor comparison interface."""
    st.subheader("🏗️ Constructor Comparison")

    client = APIClient(API_BASE_URL)
    constructors = get_filtered_constructors()

    if not constructors:
        st.error("Could not load constructors data")
        return

    # Create two columns for constructor selection
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Constructor A**")
        constructor_a = st.selectbox(
            "Select first constructor",
            constructors,
            format_func=lambda x: x['name'],
            key="constructor_a"
        )
        season_a = st.selectbox(
            "Season (All seasons if none)",
            [None] + list(range(2011, 2025)),
            index=0,
            key="constructor_season_a"
        )

    with col2:
        st.markdown("**Constructor B**")
        constructor_b = st.selectbox(
            "Select second constructor",
            constructors,
            format_func=lambda x: x['name'],
            key="constructor_b"
        )
        season_b = st.selectbox(
            "Season (All seasons if none)",
            [None] + list(range(2011, 2025)),
            index=0,
            key="constructor_season_b"
        )

    # Select metrics to compare
    available_metrics = client.get_available_metrics()
    if not available_metrics or "constructor_metrics" not in available_metrics:
        st.error("Could not load available metrics")
        return

    selected_metrics = st.multiselect(
        "Select metrics to compare",
        available_metrics["constructor_metrics"],
        default=["constructor_points_per_race", "constructor_podium_rate", "constructor_average_pit_stop_time", "constructor_dnf_rate"]
    )

    if st.button("🔍 Compare Constructors"):
        if constructor_a and constructor_b and selected_metrics:
            if constructor_a["constructor_id"] == constructor_b["constructor_id"] and season_a == season_b:
                st.warning("Please select different constructors or different seasons")
                return

            compare_constructors(client, constructor_a, constructor_b, season_a, season_b, selected_metrics)


def compare_drivers(client, driver_a, driver_b, season_a, season_b, selected_metrics):
    """Compare two drivers side by side."""
    st.markdown("---")
    st.subheader("📊 Driver Comparison Results")

    # Create requests for both drivers
    request_a = {"driver_id": driver_a["driver_id"]}
    request_b = {"driver_id": driver_b["driver_id"]}

    if season_a:
        request_a["season"] = season_a
    if season_b:
        request_b["season"] = season_b

    # Calculate metrics for both drivers
    try:
        results_a = client.calculate_bulk_metrics(selected_metrics, request_a)
        results_b = client.calculate_bulk_metrics(selected_metrics, request_b)
    except Exception as e:
        st.error(f"Error calculating metrics: {e}")
        return

    # Display comparison header
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"### 👤 {driver_a['forename']} {driver_a['surname']}")
        if season_a:
            st.markdown(f"**Season:** {season_a}")
        else:
            st.markdown("**Season:** All seasons")

    with col2:
        st.markdown(f"### 👤 {driver_b['forename']} {driver_b['surname']}")
        if season_b:
            st.markdown(f"**Season:** {season_b}")
        else:
            st.markdown("**Season:** All seasons")

    # Display metrics side by side
    if results_a and results_b:
        display_side_by_side_comparison(results_a, results_b, "driver")

        # Create comparison chart
        create_comparison_chart(results_a, results_b, driver_a, driver_b, "driver")


def compare_constructors(client, constructor_a, constructor_b, season_a, season_b, selected_metrics):
    """Compare two constructors side by side."""
    st.markdown("---")
    st.subheader("📊 Constructor Comparison Results")

    # Create requests for both constructors
    request_a = {"constructor_id": constructor_a["constructor_id"]}
    request_b = {"constructor_id": constructor_b["constructor_id"]}

    if season_a:
        request_a["season"] = season_a
    if season_b:
        request_b["season"] = season_b

    # Calculate metrics for both constructors
    try:
        results_a = client.calculate_bulk_constructor_metrics(selected_metrics, request_a)
        results_b = client.calculate_bulk_constructor_metrics(selected_metrics, request_b)
    except Exception as e:
        st.error(f"Error calculating metrics: {e}")
        return

    # Display comparison header
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"### 🏗️ {constructor_a['name']}")
        if season_a:
            st.markdown(f"**Season:** {season_a}")
        else:
            st.markdown("**Season:** All seasons")

    with col2:
        st.markdown(f"### 🏗️ {constructor_b['name']}")
        if season_b:
            st.markdown(f"**Season:** {season_b}")
        else:
            st.markdown("**Season:** All seasons")

    # Display metrics side by side
    if results_a and results_b:
        display_side_by_side_comparison(results_a, results_b, "constructor")

        # Create comparison chart
        create_comparison_chart(results_a, results_b, constructor_a, constructor_b, "constructor")


def display_side_by_side_comparison(results_a, results_b, entity_type):
    """Display metrics comparison side by side."""
    col1, col2 = st.columns(2)

    # Create dictionaries for quick lookup
    metrics_a = {result["metric_name"]: result for result in results_a}
    metrics_b = {result["metric_name"]: result for result in results_b}

    # Get all metrics (in case one side has missing data)
    all_metrics = set(metrics_a.keys()) | set(metrics_b.keys())

    for metric_name in sorted(all_metrics):
        result_a = metrics_a.get(metric_name)
        result_b = metrics_b.get(metric_name)

        with col1:
            if result_a and result_a["value"] is not None:
                create_comparison_metric_card(metric_name, result_a, "A")
            else:
                st.markdown(f"**{metric_name.replace('_', ' ').title()}**")
                st.markdown("❌ No data available")
                st.markdown("---")

        with col2:
            if result_b and result_b["value"] is not None:
                create_comparison_metric_card(metric_name, result_b, "B")
            else:
                st.markdown(f"**{metric_name.replace('_', ' ').title()}**")
                st.markdown("❌ No data available")
                st.markdown("---")


def create_comparison_metric_card(metric_name: str, result: Dict, suffix: str):
    """Create a metric card for comparison view."""
    value = result.get("value")
    metadata = result.get("metadata", {})

    # Format the metric name
    display_name = metric_name.replace('_', ' ').title()
    if display_name.startswith('Constructor '):
        display_name = display_name[12:]

    st.markdown(f"**{display_name}**")

    if value is not None:
        if isinstance(value, (int, float)):
            if "rate" in metric_name or "percentage" in metric_name:
                st.metric("", f"{value}%")
            elif "position" in metric_name:
                st.metric("", f"P{value}")
            elif "time" in metric_name:
                st.metric("", f"{value}s")
            else:
                st.metric("", f"{value}")
        else:
            st.write(f"**Value:** {value}")

        # Show key metadata
        if metadata:
            with st.expander("Details"):
                for key, val in metadata.items():
                    if key != "error":
                        st.write(f"**{key.replace('_', ' ').title()}:** {val}")
    else:
        st.markdown("❌ No data available")

    st.markdown("---")


def create_comparison_chart(results_a, results_b, entity_a, entity_b, entity_type):
    """Create a comparison chart."""
    st.subheader("📊 Visual Comparison")

    # Prepare data for chart
    metrics_data = []

    # Create dictionaries for quick lookup
    metrics_a = {result["metric_name"]: result for result in results_a}
    metrics_b = {result["metric_name"]: result for result in results_b}

    # Get metrics that have numeric values for both entities
    common_metrics = set(metrics_a.keys()) & set(metrics_b.keys())

    for metric_name in common_metrics:
        result_a = metrics_a[metric_name]
        result_b = metrics_b[metric_name]

        value_a = result_a.get("value")
        value_b = result_b.get("value")

        if (isinstance(value_a, (int, float)) and isinstance(value_b, (int, float)) and
            value_a is not None and value_b is not None):

            display_name = metric_name.replace('_', ' ').title()
            if display_name.startswith('Constructor '):
                display_name = display_name[12:]

            if entity_type == "driver":
                name_a = f"{entity_a['forename']} {entity_a['surname']}"
                name_b = f"{entity_b['forename']} {entity_b['surname']}"
            else:
                name_a = entity_a['name']
                name_b = entity_b['name']

            metrics_data.extend([
                {"Entity": name_a, "Metric": display_name, "Value": value_a},
                {"Entity": name_b, "Metric": display_name, "Value": value_b}
            ])

    if metrics_data:
        df = pd.DataFrame(metrics_data)

        # Create bar chart
        fig = px.bar(
            df,
            x="Metric",
            y="Value",
            color="Entity",
            barmode="group",
            title="Performance Comparison",
            height=500
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

        # Create radar chart for normalized comparison
        create_radar_comparison_chart(df, entity_type)
    else:
        st.warning("No comparable numeric metrics found for chart visualization")


def create_radar_comparison_chart(df, entity_type):
    """Create a radar chart for normalized comparison."""
    st.subheader("🕸️ Normalized Performance Radar")

    # Remove duplicates before pivoting (keep first occurrence)
    df_clean = df.drop_duplicates(subset=["Entity", "Metric"], keep="first")

    # Check if we have enough data after cleaning
    if len(df_clean) == 0:
        st.warning("No data available for radar chart")
        return

    # Pivot data for radar chart
    pivot_df = df_clean.pivot(index="Entity", columns="Metric", values="Value")

    if len(pivot_df) < 2:
        st.warning("Need at least 2 entities for radar comparison")
        return

    # Normalize values (0-100 scale) - higher is better for all metrics except positions and times
    normalized_df = pivot_df.copy()

    for col in normalized_df.columns:
        col_lower = col.lower()
        values = normalized_df[col]

        if "position" in col_lower or "dnf" in col_lower or "time" in col_lower:
            # Lower is better - invert the scale
            if values.max() != values.min():
                normalized_df[col] = 100 * (values.max() - values) / (values.max() - values.min())
            else:
                normalized_df[col] = 50
        else:
            # Higher is better
            if values.max() != values.min():
                normalized_df[col] = 100 * (values - values.min()) / (values.max() - values.min())
            else:
                normalized_df[col] = 50

    # Create radar chart
    fig = go.Figure()

    for entity in normalized_df.index:
        fig.add_trace(go.Scatterpolar(
            r=normalized_df.loc[entity].values,
            theta=normalized_df.columns,
            fill='toself',
            name=entity,
            line=dict(width=2)
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=True,
        title="Normalized Performance Comparison (0-100 scale)",
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)
    st.caption("Note: Values are normalized to 0-100 scale. For positions and times, lower original values score higher on the radar.")


def main():
    """Main application."""
    st.title("🏎️ F1 Performance Metrics")
    st.write("Analyze individual driver and constructor performance metrics across multiple dimensions")

    # Create tabs for driver metrics, constructor metrics, and comparisons
    driver_tab, constructor_tab, compare_tab = st.tabs(["👤 Driver Metrics", "🏗️ Constructor Metrics", "⚖️ Compare"])

    with driver_tab:
        render_driver_metrics()

    with constructor_tab:
        render_constructor_metrics()

    with compare_tab:
        render_comparison_page()

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**About:** Individual driver and constructor performance metrics system")
    st.sidebar.markdown("**Data:** F1 race results from 2011 onwards")

    # API status
    try:
        response = requests.get(f"{API_BASE_URL.replace('/api/v1', '')}/health", timeout=5)
        if response.status_code == 200:
            st.sidebar.success("🟢 API Connected")
        else:
            st.sidebar.error("🔴 API Issues")
    except:
        st.sidebar.error("🔴 API Offline")


if __name__ == "__main__":
    main()