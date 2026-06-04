from pydantic import BaseModel, Field


class EvaluationRequest(BaseModel):
    question: str = Field(min_length=3)
    answer: str = Field(min_length=1)
    contexts: list[str] = Field(default_factory=list)
    ground_truth: str | None = None


class EvaluationMetric(BaseModel):
    name: str
    score: float | None
    reason: str


class EvaluationResponse(BaseModel):
    metrics: list[EvaluationMetric]
