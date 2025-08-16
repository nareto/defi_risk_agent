from pydantic import BaseModel, Field
from abc import ABC, abstractmethod

class BaseMetricOutput(BaseModel):
    """Common interface for all metric tool outputs."""

    metric_name: str = Field(..., description="Human readable metric name")
    #description: str = Field(default="", description="Description of the metric")
    explanation: str 

    @property
    @abstractmethod
    def value(self) -> float:
        """Returns a 0–100 normalized value."""
        pass
