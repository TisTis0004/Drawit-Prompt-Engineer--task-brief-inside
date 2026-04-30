"""
Pydantic models for validating the Drawit drawing analysis schema.
All numeric fields must be floats in [0.0, 1.0] — silent breakage crashes the UI.
"""

from pydantic import BaseModel, field_validator, model_validator  # noqa: F401


VALID_MOODS = {"positive", "neutral", "concerning", "ايجابي", "طبيعي", "يستدعي الانتباه"}

ARABIC_TO_ENGLISH_MOOD = {
    "ايجابي": "positive",
    "طبيعي": "neutral",
    "يستدعي الانتباه": "concerning",
}


class DominantColor(BaseModel):
    color: str
    percentage: float
    symbolism: str

    @field_validator("percentage")
    @classmethod
    def check_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"percentage must be in [0.0, 1.0], got {v}")
        return v


class ColorUsage(BaseModel):
    dominantColors: list[DominantColor]
    colorDiversity: float
    emotionalColorChoices: float
    ageAppropriateColorUse: float
    colorSymbolism: str
    colorPatterns: str
    unusualColorChoices: str

    @field_validator("colorDiversity", "emotionalColorChoices", "ageAppropriateColorUse")
    @classmethod
    def check_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"value must be in [0.0, 1.0], got {v}")
        return v


class EmotionalIndicators(BaseModel):
    happiness: float
    confidence: float
    creativity: float
    socialBonds: float

    @field_validator("happiness", "confidence", "creativity", "socialBonds")
    @classmethod
    def check_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"value must be in [0.0, 1.0], got {v}")
        return v


class PersonalityTraits(BaseModel):
    extroversion: float
    emotionalStability: float
    conscientiousness: float
    openness: float
    agreeableness: float

    @field_validator("extroversion", "emotionalStability", "conscientiousness", "openness", "agreeableness")
    @classmethod
    def check_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"value must be in [0.0, 1.0], got {v}")
        return v


class KeyInsight(BaseModel):
    emoji: str
    title: str
    description: str


class DrawingAnalysis(BaseModel):
    drawingTitle: str
    overallMood: str  # "positive"|"neutral"|"concerning" or Arabic equivalents for Module C

    @field_validator("overallMood")
    @classmethod
    def check_mood(cls, v: str) -> str:
        if v not in VALID_MOODS:
            raise ValueError(f"overallMood must be one of {VALID_MOODS}, got '{v}'")
        return v
    colorUsage: ColorUsage
    emotionalIndicators: EmotionalIndicators
    personalityTraits: PersonalityTraits
    keyInsights: list[KeyInsight]
    recommendations: list[str]
    concerns: list[str]
    createdAt: str

    @model_validator(mode="after")
    def check_list_lengths(self) -> "DrawingAnalysis":
        if not 3 <= len(self.keyInsights) <= 6:
            raise ValueError(f"keyInsights must have 3–6 entries, got {len(self.keyInsights)}")
        if not 1 <= len(self.recommendations) <= 4:
            raise ValueError(f"recommendations must have 1–4 entries, got {len(self.recommendations)}")
        if not 1 <= len(self.concerns) <= 6:
            raise ValueError(f"concerns must have 1–6 entries, got {len(self.concerns)}")
        return self
