"""
agents/interior_agent.py
--------------------------
"buddy" - the agentic orchestrator described in the project spec.

Responsibilities:
  1. generate_design(): runs the room_analyzer -> style_suggester ->
     furniture_optimizer -> budget_planner pipeline and returns one
     combined, structured design.
  2. handle_message(): a lightweight conversational agent used by the
     multilingual voice assistant. It parses free-text / speech-to-text
     input (English, Hindi, or Telugu) for booking intents ("book the
     sofa", "मुझे सोफ़ा बुक करना है", "సోఫా బుక్ చేయండి") and drives the
     furniture booking workflow autonomously, replying in the same
     language.

ASSUMPTION: The spec calls for LangChain + an LLM endpoint (e.g. Hugging
Face) to power the agent's reasoning and the speech-to-text pipeline.
Neither an LLM API key nor internet access is available in this
environment, so `handle_message` implements the same *agent contract*
(understand a natural-language request -> take an action -> respond)
using deterministic keyword/intent matching across the three supported
languages instead of an LLM. Speech-to-text and text-to-speech are done
entirely in the browser via the Web Speech API (static/js/voice.js), so
no server-side ASR/TTS model is required either. Swapping in a real
LangChain agent later only means replacing `handle_message`'s body -
the calling contract (text in, {reply, action} out) stays the same.
"""

from tools.room_analyzer import RoomAnalyzer
from tools.style_suggester import StyleSuggester
from tools.furniture_optimizer import FurnitureOptimizer
from tools.budget_planner import BudgetPlanner
from tools.design_catalog import DesignCatalog
from models import Booking

# Keyword banks used for simple multilingual intent detection.
BOOK_KEYWORDS = {
    "en": ["book", "order", "buy", "purchase"],
    "hi": ["बुक", "ऑर्डर", "खरीद"],
    "te": ["బుక్", "ఆర్డర్", "కొను"],
}
STATUS_KEYWORDS = {
    "en": ["status", "where is my", "track"],
    "hi": ["स्थिति", "कहाँ है"],
    "te": ["స్థితి", "ఎక్కడ ఉంది"],
}
GREETING_KEYWORDS = {
    "en": ["hello", "hi", "hey"],
    "hi": ["नमस्ते", "हैलो"],
    "te": ["నమస్కారం", "హలో"],
}

REPLIES = {
    "greeting": {
        "en": "Hi! I'm buddy, your design assistant. Tell me which furniture you'd like to book.",
        "hi": "नमस्ते! मैं बडी हूँ, आपका डिज़ाइन सहायक। बताइए किस फर्नीचर को बुक करना है।",
        "te": "నమస్కారం! నేను బడ్డీ, మీ డిజైన్ సహాయకుడిని. ఏ ఫర్నిచర్ బుక్ చేయాలో చెప్పండి.",
    },
    "booked": {
        "en": "Done! I've booked the {item} for your design. Status: pending confirmation.",
        "hi": "हो गया! मैंने आपके डिज़ाइन के लिए {item} बुक कर दिया है। स्थिति: पुष्टि लंबित।",
        "te": "పూర్తయింది! మీ డిజైన్ కోసం {item} బుక్ చేసాను. స్థితి: నిర్ధారణ పెండింగ్‌లో ఉంది.",
    },
    "not_understood": {
        "en": "Sorry, I didn't catch which item to book. Try saying 'book the sofa'.",
        "hi": "क्षमा करें, मुझे समझ नहीं आया कौन सा आइटम बुक करना है। 'सोफ़ा बुक करें' कहकर देखें।",
        "te": "క్షమించండి, ఏ వస్తువు బుక్ చేయాలో అర్థం కాలేదు. 'సోఫా బుక్ చేయండి' అని చెప్పండి.",
    },
    "save_first": {
        "en": "Please save your design to the catalog first, then I can book items for you.",
        "hi": "कृपया पहले अपना डिज़ाइन कैटलॉग में सेव करें, फिर मैं आपके लिए आइटम बुक कर सकता हूँ।",
        "te": "దయచేసి ముందు మీ డిజైన్‌ను కేటలాగ్‌లో సేవ్ చేయండి, తర్వాత నేను మీ కోసం వస్తువులు బుక్ చేయగలను.",
    },
    "status": {
        "en": "You have {count} booking(s) so far for this design.",
        "hi": "इस डिज़ाइन के लिए अब तक आपकी {count} बुकिंग हैं।",
        "te": "ఈ డిజైన్ కోసం ఇప్పటివరకు మీకు {count} బుకింగ్‌లు ఉన్నాయి.",
    },
}


class InteriorDesignAgent:
    """AI-powered agentic orchestrator for interior design.
    Coordinates the room analyzer, style suggester, furniture optimizer,
    and budget planner tools to produce a complete design, and drives
    the autonomous, multilingual furniture-booking workflow.
    """

    def __init__(self, room_analyzer=None, style_suggester=None,
                 furniture_optimizer=None, budget_planner=None,
                 design_catalog=None):
        self.room_analyzer = room_analyzer or RoomAnalyzer()
        self.style_suggester = style_suggester or StyleSuggester()
        self.furniture_optimizer = furniture_optimizer or FurnitureOptimizer()
        self.budget_planner = budget_planner or BudgetPlanner()
        self.design_catalog = design_catalog or DesignCatalog()

    # ------------------------------------------------------------------
    # Design generation pipeline
    # ------------------------------------------------------------------
    def generate_design(self, image_path, room_type, style_theme, budget,
                          analysis_data=None):
        """Runs the full tool pipeline and returns one combined payload
        ready to store and render in the Design Studio."""

        analysis = analysis_data or self.room_analyzer.analyze(image_path, room_type)
        area = analysis["dimensions"]["area_sq_feet"]

        style = self.style_suggester.suggest(style_theme, room_type)
        optimization = self.furniture_optimizer.optimize(room_type, area, budget)
        priced_furniture = self.budget_planner.price_ranges(
            optimization["furniture"], budget
        )
        budget_plan = self.budget_planner.plan(budget)

        story = (
            f"A beautifully curated {room_type} featuring {style['style_theme']} "
            f"design principles. This space combines {len(priced_furniture)} carefully "
            f"selected pieces to create a harmonious and functional environment "
            f"within a ₹{budget:,.0f} budget."
        )

        return {
            "analysis": analysis,
            "style": style,
            "furniture": priced_furniture,
            "layout_tips": optimization["layout_tips"],
            "space_utilization": optimization["space_utilization"],
            "budget_plan": budget_plan,
            "design_story": story,
        }

    def save_design(self, user_id, room_type, style_theme, budget, image_path, result):
        return self.design_catalog.save(
            user_id=user_id,
            room_type=room_type,
            style=result["style"]["style_theme"],
            budget=budget,
            image_path=image_path,
            analysis_data=result["analysis"],
            design_data=result,
            furniture_items=result["furniture"],
        )

    # ------------------------------------------------------------------
    # Conversational / voice booking agent ("buddy")
    # ------------------------------------------------------------------
    def handle_message(self, design_id, text, language="en"):
        """Parses a natural-language (voice-transcribed) message and
        autonomously performs a furniture-booking action, replying in
        the same language. Returns {reply, action, booking_id?}.
        """
        text_lower = text.lower().strip()
        language = language if language in REPLIES["greeting"] else "en"

        if any(k in text_lower for k in GREETING_KEYWORDS["en"]) or \
           any(k in text for k in GREETING_KEYWORDS["hi"] + GREETING_KEYWORDS["te"]):
            return {"reply": REPLIES["greeting"][language], "action": "greeting"}

        if any(k in text_lower for k in STATUS_KEYWORDS["en"]) or \
           any(k in text for k in STATUS_KEYWORDS["hi"] + STATUS_KEYWORDS["te"]):
            count = len(Booking.find_by_design(design_id)) if design_id else 0
            return {
                "reply": REPLIES["status"][language].format(count=count),
                "action": "status",
            }

        is_booking_intent = (
            any(k in text_lower for k in BOOK_KEYWORDS["en"]) or
            any(k in text for k in BOOK_KEYWORDS["hi"] + BOOK_KEYWORDS["te"])
        )

        if is_booking_intent:
            item = self._extract_item(text_lower)
            if item and design_id:
                booking_id = Booking.create(design_id, item, language=language)
                reply = REPLIES["booked"][language].format(item=item.title())
                return {"reply": reply, "action": "booked", "booking_id": booking_id, "item": item}
            if item and not design_id:
                return {"reply": REPLIES["save_first"][language], "action": "clarify"}
            return {"reply": REPLIES["not_understood"][language], "action": "clarify"}

        return {"reply": REPLIES["not_understood"][language], "action": "clarify"}

    @staticmethod
    def _extract_item(text_lower):
        """Matches common furniture names spoken/typed in English, Hindi,
        or Telugu against a small canonical furniture vocabulary, and
        returns the canonical English name (used for the booking record
        and the price/priority lookups in the furniture catalog).

        ASSUMPTION: this is a curated dictionary covering the furniture
        items this app actually recommends, rather than a full
        translation model - sufficient for the "book the sofa" /
        "सोफ़ा बुक करें" / "సోఫా బుక్ చేయండి" style commands the voice
        assistant is designed for.
        """
        item_translations = {
            "sofa": ["sofa", "सोफ़ा", "सोफा", "సోఫా"],
            "loveseat": ["loveseat", "लवसीट", "లవ్‌సీట్"],
            "armchair": ["armchair", "आर्मचेयर", "కుర్చీ"],
            "coffee table": ["coffee table", "कॉफ़ी टेबल", "కాఫీ టేబుల్"],
            "tv stand": ["tv stand", "टीवी स्टैंड", "టీవీ స్టాండ్"],
            "bookshelf": ["bookshelf", "किताबों की अलमारी", "పుస్తకాల అర"],
            "bed frame": ["bed frame", "bed", "बेड", "పడక"],
            "wardrobe": ["wardrobe", "अलमारी", "వార్డ్రోబ్"],
            "nightstand": ["nightstand", "साइड टेबल", "నైట్‌స్టాండ్"],
            "dresser": ["dresser", "ड्रेसर", "డ్రెస్సర్"],
            "reading chair": ["reading chair", "पढ़ने की कुर्सी", "చదివే కుర్చీ"],
            "kitchen island": ["kitchen island", "किचन आइलैंड", "కిచెన్ ఐలాండ్"],
            "bar stools": ["bar stools", "बार स्टूल", "బార్ స్టూల్"],
            "dining table": ["dining table", "डाइनिंग टेबल", "డైనింగ్ టేబుల్"],
            "dining chairs": ["dining chairs", "डाइनिंग कुर्सियाँ", "డైనింగ్ కుర్చీలు"],
            "sideboard": ["sideboard", "साइडबोर्ड", "సైడ్‌బోర్డ్"],
            "desk": ["desk", "डेस्क", "డెస్క్"],
            "ergonomic chair": ["ergonomic chair", "एर्गोनॉमिक कुर्सी", "ఎర్గోనామిక్ కుర్చీ"],
        }
        for canonical, variants in item_translations.items():
            for variant in variants:
                if variant in text_lower:
                    return canonical
        return None
