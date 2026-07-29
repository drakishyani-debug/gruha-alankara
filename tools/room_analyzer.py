"""
tools/room_analyzer.py
-----------------------
Analyses an uploaded room photo and extracts structural / visual signals
that feed the rest of the design pipeline: approximate dimensions,
lighting quality, a dominant colour palette, and a rough "complexity"
score based on edge density.

ASSUMPTION: True room dimensions cannot be derived from a single 2D
photograph without depth data (LiDAR / stereo camera / user-provided
reference object). Since none of those are available here, `estimate_dimensions`
uses a documented heuristic based on the image's aspect ratio and a
configurable assumed camera field-of-view, purely to produce plausible,
consistent numbers for the UI. This is clearly labelled as an estimate
in the returned payload and should be replaced with a proper depth-estimation
model (e.g. MiDaS) for production use.
"""

import numpy as np
from PIL import Image
import cv2


def _dominant_colors(image: Image.Image, k=5):
    """Return up to k dominant hex colors using simple color quantization."""
    small = image.convert("RGB").resize((100, 100))
    quantized = small.quantize(colors=k, method=Image.MEDIANCUT)
    palette = quantized.getpalette()[: k * 3]
    counts = sorted(quantized.getcolors(), reverse=True)
    hex_colors = []
    for count, idx in counts[:k]:
        r, g, b = palette[idx * 3: idx * 3 + 3]
        hex_colors.append("#{:02x}{:02x}{:02x}".format(r, g, b))
    return hex_colors


def _brightness(image: Image.Image):
    gray = np.array(image.convert("L"))
    return float(gray.mean())


def _edge_density(image: Image.Image):
    """Rough proxy for room 'complexity' / clutter using Canny edges."""
    gray = np.array(image.convert("L"))
    edges = cv2.Canny(gray, 100, 200)
    edge_pixels = int(np.count_nonzero(edges))
    density = edge_pixels / edges.size
    return edge_pixels, density


def _estimate_dimensions(image: Image.Image, assumed_wall_height_ft=9.0):
    """Heuristic-only room size estimate based on image aspect ratio.
    See module docstring for the ASSUMPTION this relies on.
    """
    width_px, height_px = image.size
    aspect = width_px / height_px

    height_ft = assumed_wall_height_ft
    # Wider photos are assumed to capture proportionally wider rooms.
    width_ft = round(height_ft * aspect * 1.6, 1)
    length_ft = round(height_ft * 1.55, 1)
    area_sq_ft = round(width_ft * length_ft, 2)

    return {
        "width_feet": width_ft,
        "length_feet": length_ft,
        "height_feet": height_ft,
        "area_sq_feet": area_sq_ft,
        "estimated": True,
    }


class RoomAnalyzer:
    """Agent tool: analyzes a room photo and extracts dimensions, lighting,
    color palette, and room feature/complexity signals."""

    name = "room_analyzer"
    description = "Upload a photo and this tool extracts dimensions, lighting, and structural features automatically."

    def analyze(self, image_path: str, room_type: str = "living room") -> dict:
        image = Image.open(image_path)

        dimensions = _estimate_dimensions(image)
        brightness = round(_brightness(image), 1)
        colors = _dominant_colors(image)
        edge_pixels, density = _edge_density(image)

        if brightness > 140:
            lighting_quality = "bright"
            lighting_note = "Good natural lighting. Consider warm accent lights for evening ambiance."
        elif brightness > 80:
            lighting_quality = "moderate"
            lighting_note = "Adequate lighting. Layered lighting (ambient + task + accent) will help."
        else:
            lighting_quality = "dim"
            lighting_note = "Low light detected. Prioritize additional ceiling and floor lamps."

        if density > 0.15:
            complexity = "high"
        elif density > 0.07:
            complexity = "medium"
        else:
            complexity = "low"

        orientation = "vertical" if image.size[1] >= image.size[0] else "horizontal"

        return {
            "room_type": room_type,
            "dimensions": dimensions,
            "lighting": {
                "quality": lighting_quality,
                "brightness": f"{brightness}/255",
                "note": lighting_note,
            },
            "color_palette": colors,
            "room_features": {
                "complexity": complexity,
                "detected_edges": edge_pixels,
                "orientation": orientation,
            },
        }
