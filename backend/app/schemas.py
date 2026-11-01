
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class EvidenceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1)
    claim_date: Optional[str] = None
    evidence_date: Optional[str] = None
    source_url: Optional[str] = None
    source_medium: Optional[str] = None
    question: Optional[str] = None


class VerifyRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid"
    )

    claim: str = Field(
        min_length=5,
        max_length=3000,
        description="Claim text to analyze"
    )
    evidence: List[EvidenceInput] = Field(default_factory=list)
    auto_retrieve: bool = Field(default=True, description="Auto-retrieve live evidence from web if none provided")

class EvidenceItem(BaseModel):
    text: str
    polarity: Optional[str] = None
    source_title: Optional[str] = None
    source_url: Optional[str] = None


class VerifyResponse(BaseModel):
    status: str
    claim: str
    verdict: Optional[str] = None
    confidence: Optional[float] = None
    scores: Optional[Dict[str, float]] = None
    evidence: List[EvidenceItem] = Field(default_factory=list)
    explanation: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    model_version: Optional[str] = None
