"""Base classes for F1 metrics calculation."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
import pandas as pd
import numpy as np


@dataclass
class MetricResult:
    """Result of a metric calculation."""
    metric_name: str
    value: Union[float, int, Dict[str, Any], None]
    driver_id: Optional[int] = None
    driver_name: Optional[str] = None
    constructor_id: Optional[int] = None
    constructor_name: Optional[str] = None
    season: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate and clean data after initialization."""
        self.value = self._serialize_value(self.value)
        if self.metadata:
            self.metadata = self._serialize_dict(self.metadata)

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """Convert numpy types and other non-serializable types to Python native types."""
        if isinstance(value, (np.integer, np.int64, np.int32)):
            return int(value)
        elif isinstance(value, (np.floating, np.float64, np.float32)):
            return float(value)
        elif isinstance(value, np.bool_):
            return bool(value)
        elif isinstance(value, dict):
            return MetricResult._serialize_dict(value)
        elif isinstance(value, list):
            return [MetricResult._serialize_value(item) for item in value]
        return value

    @staticmethod
    def _serialize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively serialize dictionary values."""
        return {key: MetricResult._serialize_value(value) for key, value in data.items()}


class BaseMetric(ABC):
    """Abstract base class for all F1 metrics."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def calculate(
        self,
        driver_id: Optional[int] = None,
        constructor_id: Optional[int] = None,
        season: Optional[int] = None,
        race_ids: Optional[List[int]] = None,
        **kwargs
    ) -> Union[MetricResult, List[MetricResult]]:
        """Calculate the metric for given parameters."""
        pass

    @abstractmethod
    def get_required_data(self) -> List[str]:
        """Return list of required CSV files for this metric."""
        pass


class DriverMetric(BaseMetric):
    """Base class for driver-specific metrics."""
    pass


class BaseConstructorMetric(ABC):
    """Abstract base class for constructor metrics."""

    name: str = ""
    description: str = ""
    unit: str = ""

    @abstractmethod
    def calculate(self, constructor_id: int, season: Optional[int] = None, **kwargs) -> MetricResult:
        """Calculate the metric for a specific constructor."""
        pass

    def get_info(self) -> Dict[str, Any]:
        """Get metric information."""
        return {
            "name": self.name,
            "description": self.description,
            "unit": self.unit,
            "type": "constructor"
        }


class ConstructorMetric(BaseMetric):
    """Base class for constructor-specific metrics."""
    pass


class ComparisonMetric(BaseMetric):
    """Base class for comparison metrics between drivers or constructors."""
    pass