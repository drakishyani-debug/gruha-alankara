"""
tools/style_suggester.py
--------------------------
Suggests a design style theme (colors, materials, description) for a room.

ASSUMPTION: The original spec references "IBM Granite AI Models" run
through Hugging Face Transformers for style generation. Those model
weights (multi-GB) cannot be downloaded in this offline environment, so
this module implements the same *interface* (input: room analysis + user
preference -> output: structured style recommendation) using a curated,
rule-based knowledge base of interior-design styles instead of a neural
network. The `agents/interior_agent.py` orchestrator calls this tool the
same way it would call a model-backed version, so swapping in a real
Hugging Face pipeline later only requires changing this file.
"""

STYLE_LIBRARY = {
    "Modern Minimalist": {
        "description": (
            "Clean lines, neutral colors, and functional furniture with "
            "minimal clutter."
        ),
        "palette": ["#ffffff", "#000000", "#8a8a8a", "#f5f5f0"],
        "materials": ["Glass", "Steel", "Concrete", "Light wood"],
    },
    "Scandinavian": {
        "description": "Bright, airy spaces with natural materials and soft, muted tones.",
        "palette": ["#f7f3ee", "#d8c9b8", "#a9b7a5", "#4a4a48"],
        "materials": ["Light oak", "Wool", "Linen", "Rattan"],
    },
    "Traditional": {
        "description": "Warm, classic furnishings with rich wood tones and symmetrical layouts.",
        "palette": ["#6b3d2e", "#c9a86a", "#7a1f1f", "#eae0c8"],
        "materials": ["Dark wood", "Velvet", "Brass", "Leather"],
    },
    "Industrial": {
        "description": "Exposed materials, metal accents, and a raw, urban warehouse feel.",
        "palette": ["#333333", "#7c7c7c", "#b5651d", "#1a1a1a"],
        "materials": ["Exposed brick", "Iron", "Reclaimed wood", "Concrete"],
    },
    "Bohemian": {
        "description": "Eclectic, layered textiles and global-inspired patterns in warm colors.",
        "palette": ["#d97d3d", "#7c4a3b", "#e8c07d", "#4f6d5c"],
        "materials": ["Woven textiles", "Rattan", "Macrame", "Reclaimed wood"],
    },
    "Coastal": {
        "description": "Light, breezy interiors inspired by beach tones and natural light.",
        "palette": ["#e8f1f2", "#a9cbd8", "#3a6b7a", "#f2e9dc"],
        "materials": ["Whitewashed wood", "Cotton", "Rope", "Rattan"],
    },
}

# Furniture "starter kit" per room type, used both here and by
# furniture_optimizer to keep recommendations consistent.
ROOM_STYLE_FURNITURE_HINTS = {
    "living room": ["Sofa", "Coffee table", "TV stand", "Armchair", "Bookshelf"],
    "bedroom": ["Bed frame", "Wardrobe", "Nightstand", "Dresser", "Reading chair"],
    "kitchen": ["Kitchen island", "Bar stools", "Open shelving", "Dining table"],
    "dining room": ["Dining table", "Dining chairs", "Sideboard", "Pendant light"],
    "home office": ["Desk", "Ergonomic chair", "Bookshelf", "Storage cabinet"],
}


class StyleSuggester:
    """Agent tool: recommends style, palette, and materials based on user
    preferences and current design trends (curated knowledge base)."""

    name = "style_suggester"
    description = "Get personalized style recommendations based on your preferences and current design trends."

    def suggest(self, style_theme: str, room_type: str = "living room") -> dict:
        style = STYLE_LIBRARY.get(style_theme, STYLE_LIBRARY["Modern Minimalist"])
        furniture_hints = ROOM_STYLE_FURNITURE_HINTS.get(
            room_type.lower(), ROOM_STYLE_FURNITURE_HINTS["living room"]
        )
        return {
            "style_theme": style_theme if style_theme in STYLE_LIBRARY else "Modern Minimalist",
            "description": style["description"],
            "color_palette": style["palette"],
            "materials": style["materials"],
            "recommended_furniture": furniture_hints,
        }

    def list_styles(self):
        return list(STYLE_LIBRARY.keys())
