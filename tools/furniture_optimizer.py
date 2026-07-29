"""
tools/furniture_optimizer.py
------------------------------
Suggests a furniture list (with quantities and priorities) for a given
room type / style, and produces layout tips + a rough space-utilization
estimate based on the room analyzer's dimensions.

ASSUMPTION: Real optimal furniture placement (x/y coordinates avoiding
collisions) is a constrained-optimization / computer-vision problem.
Here we provide a simplified, deterministic recommendation (which items,
how many, and general layout guidance) rather than pixel-perfect
placement coordinates, which is sufficient for the "Furniture Optimizer"
card on the Design Studio described in the spec.
"""

from tools.style_suggester import ROOM_STYLE_FURNITURE_HINTS

# Approximate footprint (sq ft) per furniture piece, used for the
# "space utilization" estimate on the Furniture tab.
FURNITURE_FOOTPRINT_SQFT = {
    "Sofa": 20, "Loveseat": 14, "Armchair": 9, "Coffee Table": 6,
    "TV Stand": 8, "Bookshelf": 6, "Bed Frame": 30, "Wardrobe": 12,
    "Nightstand": 3, "Dresser": 8, "Reading Chair": 9,
    "Kitchen Island": 24, "Bar Stools": 4, "Open Shelving": 5,
    "Dining Table": 24, "Dining Chairs": 4, "Sideboard": 10,
    "Pendant Light": 1, "Desk": 12, "Ergonomic Chair": 6,
    "Storage Cabinet": 8,
}

PRIORITY_BY_INDEX = ["high", "medium", "low"]


class FurnitureOptimizer:
    """Agent tool: suggests optimal furniture placement and quantities
    for maximum space efficiency and aesthetics."""

    name = "furniture_optimizer"
    description = "Optimal furniture placement suggestions for maximum space efficiency and aesthetics."

    def optimize(self, room_type: str, area_sq_feet: float, budget: float = None) -> dict:
        base_items = ROOM_STYLE_FURNITURE_HINTS.get(
            room_type.lower(), ROOM_STYLE_FURNITURE_HINTS["living room"]
        )

        furniture_list = []
        total_footprint = 0
        for i, item in enumerate(base_items):
            quantity = 2 if item in ("Armchair", "Dining Chairs", "Bar Stools") else 1
            footprint = FURNITURE_FOOTPRINT_SQFT.get(item, 6) * quantity
            total_footprint += footprint
            furniture_list.append({
                "name": item,
                "quantity": quantity,
                "priority": PRIORITY_BY_INDEX[min(i, 2)],
                "footprint_sqft": footprint,
            })

        utilization_pct = round((total_footprint / area_sq_feet) * 100, 1) if area_sq_feet else 0

        layout_tips = [
            "Maintain at least 2-3 feet of walkway space between furniture pieces",
            "Position seating to create conversation areas",
            f"Ensure adequate lighting coverage for the {area_sq_feet} sq ft space",
            "Keep furniture minimal and functional with clear sightlines",
        ]

        return {
            "furniture": furniture_list,
            "layout_tips": layout_tips,
            "space_utilization": {
                "total_furniture_sqft": total_footprint,
                "room_area_sqft": area_sq_feet,
                "utilization_percent": min(utilization_pct, 100.0),
                "rating": self._utilization_rating(utilization_pct),
            },
        }

    @staticmethod
    def _utilization_rating(pct):
        if pct < 25:
            return "sparse"
        if pct < 50:
            return "balanced"
        if pct < 75:
            return "cozy"
        return "crowded"
