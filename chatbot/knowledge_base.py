"""
Offline knowledge base for the Hygiene Hero chatbot.
All data is embedded directly — no internet connection required.
"""

# ──────────────────────────────────────────────
#  Product catalogue (matches the vending machine)
# ──────────────────────────────────────────────
PRODUCTS = {
    "soap": {
        "name": "Antibacterial Soap",
        "benefits": (
            "Antibacterial soap helps remove dirt, bacteria, and viruses from your hands. "
            "It is especially useful after using the restroom, before eating, or after touching shared surfaces."
        ),
        "tip": "Lather for at least 20 seconds—about the time it takes to hum 'Happy Birthday' twice.",
    },
    "toothpaste": {
        "name": "Fluoride Toothpaste",
        "benefits": (
            "Fluoride toothpaste strengthens tooth enamel and prevents cavities. "
            "Using it twice daily greatly reduces your risk of tooth decay."
        ),
        "tip": "Use a pea-sized amount on your brush and brush for two full minutes.",
    },
    "napkin": {
        "name": "Tissue / Napkin",
        "benefits": (
            "Tissues help you cover your mouth and nose when coughing or sneezing, "
            "preventing the spread of germs. Dispose of used tissues immediately."
        ),
        "tip": "Always carry tissues so you never have to cough into your hands.",
    },
    "napkins": {
        "name": "Tissue / Napkin",
        "benefits": (
            "Tissues help you cover your mouth and nose when coughing or sneezing, "
            "preventing the spread of germs. Dispose of used tissues immediately."
        ),
        "tip": "Always carry tissues so you never have to cough into your hands.",
    },
    "alcohol": {
        "name": "Rubbing Alcohol (70%)",
        "benefits": (
            "70% isopropyl alcohol is the gold standard for hand sanitizing. "
            "It kills 99.9% of common bacteria and most viruses including flu and COVID-19."
        ),
        "tip": "Apply enough to cover all surfaces of both hands, then rub until dry (~20 seconds).",
        "extra": {
            "why_70": (
                "70% alcohol works better than 40% because the water content slows evaporation, "
                "giving the alcohol more contact time to destroy germs. "
                "Pure 99% alcohol evaporates too fast to be effective."
            ),
        },
    },
    "face mask": {
        "name": "Disposable Face Mask",
        "benefits": (
            "Face masks filter airborne particles and reduce the spread of respiratory illnesses. "
            "They are essential in crowded or enclosed spaces during flu season."
        ),
        "tip": "Pinch the nose wire for a snug fit and make sure the mask covers your nose and chin.",
    },
    "facemask": {
        "name": "Disposable Face Mask",
        "benefits": (
            "Face masks filter airborne particles and reduce the spread of respiratory illnesses. "
            "They are essential in crowded or enclosed spaces during flu season."
        ),
        "tip": "Pinch the nose wire for a snug fit and make sure the mask covers your nose and chin.",
    },
    "mask": {
        "name": "Disposable Face Mask",
        "benefits": (
            "Face masks filter airborne particles and reduce the spread of respiratory illnesses. "
            "They are essential in crowded or enclosed spaces during flu season."
        ),
        "tip": "Pinch the nose wire for a snug fit and make sure the mask covers your nose and chin.",
    },
}

# ──────────────────────────────────────────────
#  Hygiene tips (quick, general-purpose)
# ──────────────────────────────────────────────
HYGIENE_TIPS = [
    "Wash your hands with soap and water for at least 20 seconds before eating and after using the bathroom.",
    "Replace your toothbrush every 3 months or sooner if the bristles are frayed.",
    "Alcohol-based sanitizers are great when soap isn't available—use the 70% variety for best results.",
    "Cover your cough or sneeze with a tissue, then throw the tissue away immediately.",
    "Change your face mask every 4 hours, or immediately if it becomes damp.",
    "Keep your nails trimmed and clean to prevent bacteria buildup underneath.",
    "Stay hydrated—drinking water helps flush bacteria from your body and keeps your skin healthy.",
    "Avoid touching your face, especially your eyes, nose, and mouth, with unwashed hands.",
    "Use a clean towel or air-dry your hands after washing—wet hands transfer germs more easily.",
    "Floss daily! Brushing alone only cleans about 60% of your tooth surfaces.",
]

# ──────────────────────────────────────────────
#  Machine troubleshooting FAQ
# ──────────────────────────────────────────────
TROUBLESHOOTING = {
    "stuck": (
        "If a product appears stuck, please press the Report button on the main menu to notify our staff. "
        "Do not shake the machine."
    ),
    "rfid": (
        "To reload your RFID card, tap 'Reload (RFID)' on the main menu, "
        "enter your card ID, and insert cash into the bill/coin slot."
    ),
    "buy card": (
        "To buy a new RFID card, tap 'Buy RFID Card' on the main menu, "
        "then follow the on-screen instructions to pay."
    ),
    "how to use": (
        "1) Select the product you want. 2) Set the quantity. "
        "3) Choose Cash or RFID payment. 4) Take your product from the tray.\n"
        "(Tagalog: 1) Pumili ng produkto. 2) Ilagay ang dami. 3) Pumili ng Cash o RFID. 4) Kunin ang produkto sa baba.)"
    ),
    "no product": (
        "If the slot is empty, the machine will show 'Out of Stock'. "
        "Please try another product or report the issue."
    ),
    "payment": (
        "The machine accepts coins through the physical slot, or RFID card payments. "
        "Insert your payment and the screen will update automatically."
    ),
    "change": (
        "This build runs without automatic coin hoppers, so please use exact payment when possible. "
        "If you inserted too much, please tap 'Report' on the main menu so staff can assist."
    ),
    "error": (
        "If you see an error message, try restarting your order. "
        "If the problem persists, please use the Report button to notify staff."
    ),
}

# ──────────────────────────────────────────────
#  Profanity filter (triggers a witty response)
# ──────────────────────────────────────────────
PROFANITIES = [
    "fuck", "shit", "bitch", "asshole", "cunt", "dick", "pussy",
    "puta", "gago", "tanga", "bobo", "ulol", "gaga", "putangina",
    "inamo", "hayop", "walanghiya",
]

# ──────────────────────────────────────────────
#  First aid / wound care basics
# ──────────────────────────────────────────────
FIRST_AID = {
    "wound": (
        "For minor cuts: wash with clean water, apply alcohol to the surrounding area (not inside the wound), "
        "and cover with a clean bandage. Seek medical help for deep or heavily bleeding wounds."
    ),
    "burn": (
        "For minor burns: run cool (not cold) water over the area for 10-20 minutes. "
        "Do not apply ice or butter. Cover loosely with a sterile bandage and see a doctor if it blisters."
    ),
    "nosebleed": (
        "Sit upright and lean slightly forward. Pinch the soft part of your nose for 10-15 minutes. "
        "If bleeding doesn't stop after 20 minutes, seek medical attention."
    ),
}

# ──────────────────────────────────────────────
#  Greeting / farewell patterns
# ──────────────────────────────────────────────
GREETINGS = [
    "hello", "hi", "hey", "good morning", "good afternoon",
    "good evening", "greetings", "howdy", "sup", "what's up",
    "yo", "kamusta", "musta", "hoy", "uy",
]

FAREWELLS = [
    "bye", "goodbye", "see you", "thanks", "thank you",
    "salamat", "paalam", "sige", "okay bye",
]

EMERGENCY_KEYWORDS = [
    "heart attack", "stroke", "choking", "unconscious",
    "severe bleeding", "seizure", "anaphylaxis", "can't breathe",
    "chest pain", "poisoning", "overdose",
]
