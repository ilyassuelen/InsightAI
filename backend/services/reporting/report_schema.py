from typing import Any, Dict, List, Literal
from pydantic import BaseModel, Field


class ReportSection(BaseModel):
    heading: str
    content: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)


class KeyFigure(BaseModel):
    name: str
    value: str
    unit: str
    context: str = ""


class ReportFinding(BaseModel):
    title: str
    description: str
    importance: Literal["low", "medium", "high"] = "medium"


class ReportRisk(BaseModel):
    title: str
    description: str
    severity: Literal["low", "medium", "high"] = "medium"


class ReportRecommendation(BaseModel):
    title: str
    description: str
    priority: Literal["low", "medium", "high"] = "medium"


class ChartDataPoint(BaseModel):
    label: str
    value: float


class ReportChart(BaseModel):
    title: str
    type: Literal["bar", "line", "pie"] = "bar"
    unit: str = ""
    data: List[ChartDataPoint] = Field(default_factory=list)


class TimelineEvent(BaseModel):
    label: str
    title: str
    description: str = ""


class ReportModel(BaseModel):
    title: str
    summary: str
    sections: List[ReportSection]
    key_figures: List[KeyFigure] = Field(default_factory=list)
    main_findings: List[ReportFinding] = Field(default_factory=list)
    risks: List[ReportRisk] = Field(default_factory=list)
    recommendations: List[ReportRecommendation] = Field(default_factory=list)
    charts: List[ReportChart] = Field(default_factory=list)
    timeline: List[TimelineEvent] = Field(default_factory=list)
    conclusion: str