"""Shared primitive types used across multiple models."""

from pydantic import BaseModel, Field


class ColorSwatch(BaseModel):
    """A single dominant color extracted from an ad creative."""

    hex: str = Field(description="Hex color code, e.g. '#FF3366'")
    h: float = Field(description="HSL hue, 0–360")
    s: float = Field(description="HSL saturation, 0.0–1.0")
    l: float = Field(description="HSL lightness, 0.0–1.0")


class BoundingBox(BaseModel):
    """Pixel bounding box for a DOM element, relative to full-page screenshot."""

    x: float = Field(description="Left edge in pixels")
    y: float = Field(description="Top edge in pixels")
    width: float
    height: float
