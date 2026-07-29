"""
tools/design_catalog.py
-------------------------
Thin helper the agent uses to persist a finished design (and its
furniture list) to the database, and to format catalog entries for the
"My Catalog" page.
"""

from models import Design, Furniture


class DesignCatalog:
    """Agent tool: saves/retrieves a user's designs and their furniture
    lists to build the personal design catalog."""

    name = "design_catalog"
    description = "Save and organize your finished designs into a personal catalog."

    def save(self, user_id, room_type, style, budget, image_path,
              analysis_data, design_data, furniture_items):
        design_id = Design.create(
            user_id=user_id,
            room_type=room_type,
            style=style,
            budget=budget,
            image_path=image_path,
            analysis_data=analysis_data,
            design_data=design_data,
        )
        if furniture_items:
            Furniture.bulk_create(design_id, furniture_items)
        return design_id

    def list_for_user(self, user_id, style=None, room_type=None, order_by="newest"):
        return Design.find_by_user(user_id, style=style, room_type=room_type, order_by=order_by)
