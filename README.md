# 🏎️ F1 Performance Metrics System

A comprehensive **Formula 1 driver and constructor performance analysis system** with modular metrics calculation, FastAPI backend, and interactive Streamlit frontend. Features driver comparisons, constructor analysis, and detailed performance insights across multiple dimensions.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ Features

### 📊 **Performance Metrics**
- **9 Driver Metrics**: Qualifying performance, race results, consistency, teammate comparisons
- **65+ Constructor Metrics**: Championship performance, race results, qualifying, reliability, competitiveness, pit stops, lap performance
- **Individual Analysis**: Each metric calculated independently with detailed metadata
- **Seasonal Filtering**: Analyze performance for specific seasons or career totals

### 🔗 **Interactive Comparisons**
- **Driver vs Driver**: Head-to-head comparisons with normalized radar charts
- **Constructor vs Constructor**: Comprehensive team performance analysis
- **Bar Charts & Radar Charts**: Multiple visualization formats
- **Real-time Filtering**: Dynamic metric selection and timeframe analysis

### 🚀 **Modern Architecture**
- **FastAPI Backend**: High-performance API with automatic documentation
- **Streamlit Frontend**: Interactive web interface with real-time updates
- **Modular Design**: Easy to extend with new metrics
- **Efficient Caching**: File-based caching with TTL for fast repeated queries

### 🌐 **Deployment Ready**
- **Free Hosting Options**: Pre-configured for Streamlit Cloud + Render
- **Docker Support**: Containerized deployment options
- **Production Security**: CORS configuration and environment-based settings

## 🏗️ Project Structure

```
f1-elo/
├── backend/                    # FastAPI Backend
│   ├── api/                   # API Layer
│   │   ├── routes/           # API endpoints
│   │   │   ├── metrics.py    # Metric calculation endpoints
│   │   │   ├── drivers.py    # Driver information endpoints
│   │   │   └── constructors.py # Constructor information endpoints
│   │   ├── schemas.py        # Pydantic models
│   │   └── main.py          # FastAPI application
│   ├── data/                 # Data Management
│   │   ├── loader.py        # F1 data loading with caching
│   │   └── cache.py         # Metric result caching
│   ├── metrics/             # Performance Metrics
│   │   ├── base.py          # Base metric classes
│   │   ├── driver/          # Driver-specific metrics
│   │   │   ├── qualifying.py # Qualifying performance
│   │   │   ├── race.py      # Race performance
│   │   │   └── teammate.py  # Teammate comparisons
│   │   └── constructor/     # Constructor metrics (6 categories)
│   │       ├── championship.py      # Championship performance
│   │       ├── race_performance.py  # Race results
│   │       ├── qualifying.py       # Qualifying performance
│   │       ├── reliability.py      # Reliability metrics
│   │       ├── competitiveness.py  # Competitiveness analysis
│   │       ├── pit_stops.py        # Pit stop performance
│   │       └── lap_performance.py  # Lap time analysis
│   └── config.py            # Configuration settings
├── frontend/
│   └── app.py              # Streamlit web interface
├── dataset/               # F1 CSV Data (21MB)
│   ├── races.csv         # Race information
│   ├── results.csv       # Race results
│   ├── qualifying.csv    # Qualifying results
│   ├── drivers.csv       # Driver information
│   ├── constructors.csv  # Constructor information
│   ├── lap_times.csv     # Lap time data
│   └── pit_stops.csv     # Pit stop data
├── cache/                # File-based metric cache
├── .streamlit/           # Streamlit configuration
│   ├── config.toml      # App theme and settings
│   └── secrets.toml     # API URL configuration (template)
├── requirements.txt      # Python dependencies for deployment
├── render.yaml          # Render deployment configuration
├── Procfile            # Alternative deployment configuration
├── DEPLOYMENT.md       # Comprehensive deployment guide
└── pyproject.toml      # Project configuration
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+**
- **uv** (recommended package manager) or **pip**

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/f1-elo.git
cd f1-elo

# Install dependencies with uv (recommended)
uv sync

# OR install with pip
pip install -r requirements.txt
```

### Running the Application

**Option 1: Both services together (Recommended)**
```bash
# Starts FastAPI backend (port 8000) + Streamlit frontend (port 8501)
uv run python -m backend.api.main
```

**Option 2: Services separately**
```bash
# Terminal 1: FastAPI backend
uv run uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Streamlit frontend
uv run streamlit run frontend/app.py
```

### Access the Application

- **Frontend**: http://localhost:8501 (Streamlit interface)
- **Backend API**: http://localhost:8000 (FastAPI server)
- **API Documentation**: http://localhost:8000/docs (Interactive API docs)

## 📊 Available Metrics

### 👤 **Driver Metrics (9 metrics)**

**Qualifying Performance:**
- `qualifying_position_average` - Average qualifying position
- `qualifying_consistency` - Standard deviation of qualifying positions
- `pole_position_rate` - Percentage of pole positions

**Race Performance:**
- `average_finish_position` - Average race finish position (DNFs excluded)
- `points_per_race` - Average championship points per race
- `dnf_rate` - Percentage of DNFs (Did Not Finish)
- `podium_rate` - Percentage of podium finishes (top 3)

**Teammate Comparisons:**
- `teammate_qualifying_comparison` - Head-to-head qualifying vs teammates
- `teammate_race_comparison` - Head-to-head race finishing vs teammates

### 🏗️ **Constructor Metrics (65+ metrics)**

**Championship Performance (5 metrics):**
- Championship position, wins, points per season/race, top-3 finishes

**Race Performance (8 metrics):**
- Win rate, podium rate, race wins, lockouts, average finish position, points scoring rate

**Qualifying Performance (6 metrics):**
- Pole position rate, average qualifying position, consistency, front row starts, top-10 rate

**Reliability (5 metrics):**
- DNF rate, mechanical failure rate, finish rate, reliability index

**Competitiveness (6 metrics):**
- Season dominance, consistency index, competitiveness rating, win streaks

**Pit Stops (9 metrics):**
- Average pit stop time, fastest stops, consistency, sub-3-second stops, efficiency

**Lap Performance (10 metrics):**
- Average lap time, fastest laps, pace analysis, tire management, variability

## 🌐 Free Deployment

Deploy your F1 Performance Metrics system for **free** using:

### **Recommended Setup**
- **Frontend**: [Streamlit Community Cloud](https://share.streamlit.io) - 100% free
- **Backend**: [Render](https://render.com) - Free tier available

### **Quick Deploy Steps**

1. **Push to GitHub** (public repo)
2. **Deploy Backend** to Render:
   - Connect GitHub repo
   - Use provided `render.yaml` configuration
   - Set environment: `ENVIRONMENT=production`
3. **Deploy Frontend** to Streamlit Cloud:
   - Connect GitHub repo
   - Set main file: `frontend/app.py`
   - Configure secrets with backend URL

📋 **Complete deployment guide**: See [DEPLOYMENT.md](DEPLOYMENT.md)

## 🔧 Development

### Running Tests
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=backend
```

### Code Quality
```bash
# Format code
uv run ruff format

# Lint code
uv run ruff check

# Type checking
uv run mypy backend/
```

### Adding New Metrics

1. **Create metric class** inheriting from `DriverMetric` or `ConstructorMetric`
2. **Implement methods**: `calculate()` and `get_required_data()`
3. **Add to registry** in `backend/api/routes/metrics.py`
4. **Metric automatically available** via API and frontend

Example:
```python
class NewDriverMetric(DriverMetric):
    def __init__(self):
        super().__init__(
            name="new_metric",
            description="Description of new metric"
        )

    def calculate(self, driver_id: int, **kwargs) -> MetricResult:
        # Metric calculation logic
        return MetricResult(
            metric_name=self.name,
            value=calculated_value,
            driver_id=driver_id
        )
```

## 📊 Data Source

The system uses **Formula 1 historical data** from the comprehensive Kaggle dataset:

- **Primary Source**: [Formula 1 World Championship (1950-2020)](https://www.kaggle.com/datasets/rohanrao/formula-1-world-championship-1950-2020) by Rohan Rao
- **Dataset Size**: 21MB CSV files with complete race, qualifying, and timing data
- **Coverage**: Races, results, qualifying, drivers, constructors, lap times, pit stops
- **Analysis Range**: 2011 onwards (when complete telemetry data became available)
- **Data Quality**: Professionally maintained dataset with high accuracy and completeness

### Data Files Included:
- `races.csv` - Race information and calendar data
- `results.csv` - Race results with finishing positions and points
- `qualifying.csv` - Qualifying session results and grid positions
- `drivers.csv` - Driver biographical and career information
- `constructors.csv` - Constructor team information and history
- `lap_times.csv` - Individual lap timing data (2011+)
- `pit_stops.csv` - Pit stop timing and strategy data (2011+)

## 🎯 Key Features in Detail

### **Modular Metric System**
- Each metric is independent and can be displayed separately
- Standardized `MetricResult` objects with metadata
- Automatic caching with configurable TTL
- Easy to extend with new performance dimensions

### **Interactive Frontend**
- **Real-time filtering** by driver, season, constructor
- **Multiple visualization types**: Cards, bar charts, radar charts
- **Comparison interface** with normalized scoring
- **Responsive design** optimized for desktop and mobile

### **High-Performance Backend**
- **FastAPI** with automatic OpenAPI documentation
- **Efficient data loading** with pandas and caching
- **RESTful API** design with proper HTTP status codes
- **Production-ready** CORS and security configuration

### **Deployment Architecture**
- **Environment-based configuration** (dev/production)
- **Docker support** for containerized deployment
- **Free hosting compatibility** with major platforms
- **CI/CD ready** with provided configuration files

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-metric`)
3. **Add tests** for new functionality
4. **Ensure quality** checks pass (`uv run ruff check && uv run pytest`)
5. **Submit** a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Formula 1** for the amazing sport and racing data
- **Rohan Rao** for the comprehensive [Kaggle F1 dataset](https://www.kaggle.com/datasets/rohanrao/formula-1-world-championship-1950-2020)
- **Ergast Developer API** for the original data source and API structure
- **FastAPI & Streamlit** teams for excellent frameworks
- **F1 Community** for inspiration, feedback, and passion for data analysis

---

**Built with ❤️ for Formula 1 fans and data enthusiasts**