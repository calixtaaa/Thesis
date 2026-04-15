"""
Hygiene Hero — Offline chatbot engine for the vending machine.

This engine uses keyword matching and rule-based logic so it works
entirely offline on a Raspberry Pi 5 with zero external API calls.
"""

import random
import re
from chatbot.knowledge_base import (
    PRODUCTS,
    HYGIENE_TIPS,
    TROUBLESHOOTING,
    FIRST_AID,
    GREETINGS,
    FAREWELLS,
    EMERGENCY_KEYWORDS,
    PROFANITIES,
)


class HygieneHeroBot:
    """
    Role: You are the "Hygiene Hero," a helpful, friendly, and professional
    AI assistant built into an automated personal hygiene vending machine.
    Your goal is to assist users with their health and hygiene needs.

    Context: Running on a Raspberry Pi 5. The machine sells soap, toothpaste,
    napkins, alcohol, and face masks.

    Constraints:
    - Be Concise: Keep responses under 3 sentences.
    - Offline: All data comes from the local knowledge base.
    - Tone: Supportive, clean, and efficient.
    - Safety: For serious medical emergencies, advise seeking professional help.
    """

    SYSTEM_PROMPT = (
        "You are the 'Hygiene Hero,' a helpful, friendly, and professional AI assistant "
        "built into an automated personal hygiene vending machine. Your goal is to assist "
        "users with their health and hygiene needs.\n\n"
        "Context: You are running on a Raspberry Pi 5. The machine sells items like soap, "
        "toothpaste, napkins, alcohol, and face masks.\n\n"
        "Constraints:\n"
        "- Be Concise: Users are standing in front of a vending machine; keep responses under 3 sentences.\n"
        "- Offline: Focus on the data provided in the local database.\n"
        "- Tone: Supportive, clean, and efficient. Avoid medical jargon unless explaining a product.\n"
        "- Safety: If a user asks about a serious medical emergency, advise them to seek professional "
        "medical help immediately."
    )

    # Greeting responses
    _GREETING_RESPONSES = [
        "Hi there! 👋 I'm Hygiene Hero, your friendly vending machine assistant. How can I help you today?",
        "Hello! 🤖 Welcome to the hygiene vending machine. Ask me about any product or hygiene tip!",
        "Hey! 😊 I'm here to help you with products, hygiene tips, or machine questions. What do you need?",
        "Good day! 🌟 I'm your Hygiene Hero assistant. Ask me anything about our products!",
    ]

    _FAREWELL_RESPONSES = [
        "Goodbye! Stay clean, stay healthy! 🧼✨",
        "See you next time! Remember to wash your hands. 👋😊",
        "Take care! Your hygiene matters. 💪🌟",
        "Bye! Don't forget — 20 seconds of handwashing saves lives! 🧴",
    ]

    _EMERGENCY_RESPONSE = (
        "⚠️ This sounds like a medical emergency. Please call your local emergency number "
        "or go to the nearest hospital immediately. This machine cannot provide emergency medical care."
    )

    _FALLBACK_RESPONSES = [
        "I'm not sure about that, but I can help with product info, hygiene tips, or machine troubleshooting! Try asking about one of those. 😊",
        "Hmm, I don't have info on that. Try asking me about our products (soap, alcohol, toothpaste, napkins, face masks) or hygiene tips!",
        "I'm your Hygiene Hero — I know about our products and hygiene tips! Try asking something like 'Tell me about alcohol' or 'Give me a hygiene tip'. 🤖",
    ]

    def __init__(self):
        self.conversation_history = []
        self._tip_index = 0

    def reset(self):
        """Clear conversation history."""
        self.conversation_history = []
        self._tip_index = 0

    def get_response(self, user_message: str) -> str:
        """
        Process a user message and return a concise response.
        All logic is offline — no API calls.
        """
        if not user_message or not user_message.strip():
            return "Please type a message so I can help you! 😊"

        text = user_message.strip()
        text_lower = text.lower()

        # Store in conversation history
        self.conversation_history.append({"role": "user", "text": text})

        # 0) Check for profanities
        response = self._check_profanity(text_lower)
        if response:
            self.conversation_history.append({"role": "bot", "text": response})
            return response

        # 1) Check for medical emergencies first (SAFETY)
        response = self._check_emergency(text_lower)
        if response:
            self.conversation_history.append({"role": "bot", "text": response})
            return response

        # 2) Check for greetings
        response = self._check_greeting(text_lower)
        if response:
            self.conversation_history.append({"role": "bot", "text": response})
            return response

        # 3) Check for farewells
        response = self._check_farewell(text_lower)
        if response:
            self.conversation_history.append({"role": "bot", "text": response})
            return response

        # 4) Check for specific product questions
        response = self._check_product_query(text_lower)
        if response:
            self.conversation_history.append({"role": "bot", "text": response})
            return response

        # 5) Check for the special "70% vs 40%" alcohol question
        response = self._check_alcohol_comparison(text_lower)
        if response:
            self.conversation_history.append({"role": "bot", "text": response})
            return response

        # 6) Check for troubleshooting questions
        response = self._check_troubleshooting(text_lower)
        if response:
            self.conversation_history.append({"role": "bot", "text": response})
            return response

        # 7) Check for first aid questions
        response = self._check_first_aid(text_lower)
        if response:
            self.conversation_history.append({"role": "bot", "text": response})
            return response

        # 8) Check for hygiene tip requests
        response = self._check_hygiene_tip_request(text_lower)
        if response:
            self.conversation_history.append({"role": "bot", "text": response})
            return response

        # 9) Check for "what do you sell" / product list questions
        response = self._check_product_list(text_lower)
        if response:
            self.conversation_history.append({"role": "bot", "text": response})
            return response

        # 10) Check for "who are you" / about questions
        response = self._check_about(text_lower)
        if response:
            self.conversation_history.append({"role": "bot", "text": response})
            return response

        # Fallback
        response = random.choice(self._FALLBACK_RESPONSES)
        self.conversation_history.append({"role": "bot", "text": response})
        return response

    # ── Private matcher methods ──────────────────

    def _check_emergency(self, text: str) -> str | None:
        for keyword in EMERGENCY_KEYWORDS:
            if keyword in text:
                return self._EMERGENCY_RESPONSE
        return None

    def _check_profanity(self, text: str) -> str | None:
        words = text.split()
        for w in words:
            clean_w = re.sub(r'[^\w\s]', '', w)
            if clean_w in PROFANITIES:
                return "I'm just a vending machine, but you definitely need our soap to wash that mouth! 🧼🤐"
        for p in PROFANITIES:
            if " " in p and p in text:
                return "I'm just a vending machine, but you definitely need our soap to wash that mouth! 🧼🤐"
        return None

    def _check_greeting(self, text: str) -> str | None:
        # Only match if the message is short (likely a greeting)
        words = text.split()
        if len(words) <= 4:
            for g in GREETINGS:
                # Multi-word greetings use substring; single-word greetings require word match
                if " " in g:
                    if g in text:
                        return random.choice(self._GREETING_RESPONSES)
                elif g in words:
                    return random.choice(self._GREETING_RESPONSES)
        return None

    def _check_farewell(self, text: str) -> str | None:
        words = text.split()
        if len(words) <= 5:
            for f in FAREWELLS:
                if " " in f:
                    if f in text:
                        return random.choice(self._FAREWELL_RESPONSES)
                elif f in words:
                    return random.choice(self._FAREWELL_RESPONSES)
        return None

    def _check_product_query(self, text: str) -> str | None:
        """Match product-related questions."""
        for key, product in PRODUCTS.items():
            if key in text:
                # Determine what kind of info the user wants
                if any(w in text for w in ["benefit", "why", "good", "help", "what", "about", "use"]):
                    return f"🧴 **{product['name']}**: {product['benefits']}"
                elif any(w in text for w in ["tip", "how", "advic", "recommend"]):
                    return f"💡 **Tip for {product['name']}**: {product['tip']}"
                else:
                    # General product info
                    return f"🧴 **{product['name']}**: {product['benefits']} 💡 Tip: {product['tip']}"
        return None

    def _check_alcohol_comparison(self, text: str) -> str | None:
        """Handle the classic '70% vs 40%' question."""
        patterns = [
            r"70.*(?:vs|versus|better|than).*40",
            r"40.*(?:vs|versus|worse|than).*70",
            r"why.*70",
            r"percent.*alcohol",
            r"70.*percent",
            r"40.*percent",
        ]
        for pat in patterns:
            if re.search(pat, text):
                extra = PRODUCTS.get("alcohol", {}).get("extra", {})
                answer = extra.get("why_70", "")
                if answer:
                    return f"🔬 Great question! {answer}"
        return None

    def _check_troubleshooting(self, text: str) -> str | None:
        """Match machine troubleshooting questions."""
        for key, answer in TROUBLESHOOTING.items():
            if key in text:
                return f"🔧 {answer}"

        if "paano gamitin" in text or "how to use this machine" in text or "how to used this machine" in text:
            return f"🔧 {TROUBLESHOOTING['how to use']}"

        # Broader troubleshooting triggers
        trouble_words = ["machine", "broken", "not working", "problem", "issue", "help me", "doesn't work", "sira", "tulong", "ayaw gumana"]
        if any(w in text for w in trouble_words):
            return (
                "🔧 I'm sorry to hear you're having trouble! "
                "Please use the 'Report' button on the main menu to submit a bug report, "
                "or ask me a specific question about the machine.\n"
                "(Tagalog: Pindutin ang 'Report' sa main menu o magtanong ulit.)"
            )
        return None

    def _check_first_aid(self, text: str) -> str | None:
        """Match first aid / wound care queries."""
        for key, advice in FIRST_AID.items():
            if key in text:
                return f"🩹 {advice}"

        if any(w in text for w in ["first aid", "injury", "cut", "bleed", "sugat", "dugo"]):
            return f"🩹 {FIRST_AID['wound']}"
        return None

    def _check_hygiene_tip_request(self, text: str) -> str | None:
        """User asks for a random hygiene tip."""
        trigger_words = ["tip", "advice", "suggest", "recommend", "hygiene", "health tip", "random", "payo"]
        if any(w in text for w in trigger_words):
            tip = HYGIENE_TIPS[self._tip_index % len(HYGIENE_TIPS)]
            self._tip_index += 1
            return f"💡 **Hygiene Tip**: {tip}"
        return None

    def _check_product_list(self, text: str) -> str | None:
        """User asks what the machine sells."""
        triggers = ["what do you sell", "what products", "available", "menu", "items", "sell", "product list", "ano ang tinda", "anong benta"]
        if any(t in text for t in triggers):
            return (
                "🛒 We sell the following hygiene products:\n"
                "• Antibacterial Soap\n"
                "• Fluoride Toothpaste\n"
                "• Tissues / Napkins\n"
                "• Rubbing Alcohol (70%)\n"
                "• Disposable Face Masks\n\n"
                "Ask me about any product for more details!"
            )
        return None

    def _check_about(self, text: str) -> str | None:
        """User asks who the bot is."""
        triggers = ["who are you", "what are you", "your name", "introduce", "about you", "sino ka", "ano ka"]
        if any(t in text for t in triggers):
            return (
                "🤖 I'm **Hygiene Hero**, your friendly AI assistant! "
                "I live inside this vending machine to help you with product info, "
                "hygiene tips, machine troubleshooting, and basic first aid advice.\n"
                "(Tagalog: Nandito ako para tulungan ka sa aming hygiene products!)"
            )
        return None
