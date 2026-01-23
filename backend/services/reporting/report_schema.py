from typing import Any, Dict, List
from pydantic import BaseModel, Field

class ReportSection(BaseModel):
    heading: str
    content: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)  # chunk ids, pages, etc.

class KeyFigure(BaseModel):
    name: str
    value: str
    unit: str
    context: str = ""

class ReportModel(BaseModel):
    title: str
    summary: str
    sections: List[ReportSection]
    key_figures: List[KeyFigure] = Field(default_factory=list)
    conclusion: str