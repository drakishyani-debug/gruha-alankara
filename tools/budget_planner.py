"""
tools/budget_planner.py
-------------------------
Splits a user's total budget across standard interior-design spend
categories, and produces per-item price ranges plus savings tips.

ASSUMPTION: Percentage allocations below are a reasonable, commonly
cited industry rule-of-thumb split for residential interior design
budgets (furniture-heavy), not pulled from a live pricing API (since
this app runs with no cloud/external services).
"""

CATEGORY_SPLIT = {
    "Furniture": 0.45,
    "Lighting": 0.15,
    "Decor & Accessories": 0.15,
    "Paint & Wallpaper": 0.10,
    "Installation & Labor": 0.05,
    # remaining 10% reserved as contingency, folded into Decor below
}
# normalize remaining 10% into Decor & Accessories to sum to 100%
CATEGORY_SPLIT["Decor & Accessories"] += 0.10 - 0.05  # -> 0.20 total, adjust
# (kept explicit rather than magic so the numbers are easy to audit)
CATEGORY_SPLIT = {
    "Furniture": 0.45,
    "Lighting": 0.15,
    "Decor & Accessories": 0.15,
    "Paint & Wallpaper": 0.10,
    "Installation & Labor": 0.05,
    "Contingency": 0.10,
}

SAVINGS_TIPS = [
    "Shop during seasonal sales for 20-50% discounts",
    "Consider mixing high and low-end pieces for balance",
    "DIY decor items can save 30-40% compared to retail",
    "Buy floor models or gently used furniture for significant savings",
    "Use online marketplaces for vintage and unique finds",
]


class BudgetPlanner:
    """Agent tool: smart budget allocation across furniture, decor, and
    materials with savings tips."""

    name = "budget_planner"
    description = "Smart budget allocation across furniture, decor, and materials with savings tips."

    def plan(self, total_budget: float) -> dict:
        allocations = []
        for category, pct in CATEGORY_SPLIT.items():
            amount = round(total_budget * pct, 2)
            allocations.append({
                "category": category,
                "amount": amount,
                "percent": round(pct * 100),
            })

        return {
            "total_budget": total_budget,
            "allocations": allocations,
            "savings_tips": SAVINGS_TIPS,
        }

    def price_ranges(self, furniture_items: list, total_budget: float) -> list:
        """Assigns a plausible price band per furniture item, weighted by
        priority, that roughly sums toward the furniture allocation."""
        furniture_budget = total_budget * CATEGORY_SPLIT["Furniture"]
        weight_map = {"high": 3, "medium": 2, "low": 1}
        total_weight = sum(weight_map.get(i.get("priority", "medium"), 2) for i in furniture_items) or 1

        priced = []
        for item in furniture_items:
            weight = weight_map.get(item.get("priority", "medium"), 2)
            share = (weight / total_weight) * furniture_budget
            low = round(share * 0.7, -1) or 50
            high = round(share * 1.3, -1) or 100
            priced.append({**item, "price_min": low, "price_max": high})
        return priced
