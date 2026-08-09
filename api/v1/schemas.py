"""Pydantic models -- these ARE allowed in api/, this is the boundary."""
from typing import Any, Literal

from pydantic import BaseModel


class TranscribeResponseModel(BaseModel):
    transcript: str
    detected_language: str
    duration_seconds: float
    provider: str
    speech_detected: bool


class ResultRowModel(BaseModel):
    test_name: str
    value: dict[str, Any]
    unit: str | None
    reference_range: str | None
    flag: str | None
    raw_line: str


class MetaModel(BaseModel):
    patient_name: str | None = None
    age: str | None = None
    sex: str | None = None
    report_date: str | None = None
    lab_name: str | None = None
    reference_no: str | None = None


class ExtractResponseModel(BaseModel):
    meta: MetaModel
    results: list[ResultRowModel]
    is_lab_report: bool
    provider: str


class ErrorResponseModel(BaseModel):
    error: str
    code: str
