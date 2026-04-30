"""
Offline knowledge base for the Hygiene Hero chatbot.
All data is embedded directly — no internet connection required.
"""

# ──────────────────────────────────────────────
#  Product catalogue (matches the vending machine)
# ──────────────────────────────────────────────
PRODUCTS = {
    # --- Real machine catalog (synonyms map to same intent) ---
    "alcohol": {
        "name": "Alcohol (70%)",
        "benefits": (
            "70% isopropyl alcohol helps kill most germs on hands and small surfaces when soap and water aren’t available."
        ),
        "tip": "Rub until dry (~20 seconds). Cover palms, between fingers, and fingertips.",
        "extra": {
            "why_70": (
                "70% alcohol works better than 40% because the water slows evaporation, giving more contact time to kill germs."
            ),
        },
    },
    "soap": {
        "name": "Antibacterial Soap",
        "benefits": "Soap lifts dirt and germs off skin so they rinse away with water.",
        "tip": "Lather for at least 20 seconds (palms, back of hands, between fingers, nails).",
    },
    "deodorant": {
        "name": "Deodorant",
        "benefits": "Helps reduce body odor and keeps you feeling fresh through the day.",
        "tip": "Apply to clean, dry underarms. Reapply after heavy sweating if needed.",
    },
    "deo": {
        "name": "Deodorant",
        "benefits": "Helps reduce body odor and keeps you feeling fresh through the day.",
        "tip": "Apply to clean, dry underarms. Reapply after heavy sweating if needed.",
    },
    "mouthwash": {
        "name": "Mouthwash",
        "benefits": "Freshens breath and helps reduce odor-causing bacteria in the mouth.",
        "tip": "Swish for 30 seconds, then spit out (do not swallow).",
    },
    "mouth wash": {
        "name": "Mouthwash",
        "benefits": "Freshens breath and helps reduce odor-causing bacteria in the mouth.",
        "tip": "Swish for 30 seconds, then spit out (do not swallow).",
    },
    "wet wipes": {
        "name": "Wet Wipes",
        "benefits": "Quick clean-up on the go when you don’t have soap and water.",
        "tip": "Great for hands and small spills; wash with soap later when possible.",
    },
    "wipes": {
        "name": "Wet Wipes",
        "benefits": "Quick clean-up on the go when you don’t have soap and water.",
        "tip": "Great for hands and small spills; wash with soap later when possible.",
    },
    "tissues": {
        "name": "Tissues",
        "benefits": "Helps you cover coughs/sneezes and keep hands clean.",
        "tip": "Throw used tissues away right away and sanitize hands.",
    },
    "tissue": {
        "name": "Tissues",
        "benefits": "Helps you cover coughs/sneezes and keep hands clean.",
        "tip": "Throw used tissues away right away and sanitize hands.",
    },
    "panty liner": {
        "name": "Panty Liners",
        "benefits": "Light protection for daily freshness, discharge, or very light days.",
        "tip": "Change regularly to stay comfortable and reduce odor.",
    },
    "panty liners": {
        "name": "Panty Liners",
        "benefits": "Light protection for daily freshness, discharge, or very light days.",
        "tip": "Change regularly to stay comfortable and reduce odor.",
    },
    "all night pads": {
        "name": "All Night Pads",
        "benefits": "Extra coverage designed for overnight use and heavier flow.",
        "tip": "Change in the morning and whenever it feels damp for comfort.",
    },
    "regular w/ wings": {
        "name": "Regular Pads (With Wings)",
        "benefits": "Everyday protection with wings for a more secure fit.",
        "tip": "Wings help prevent shifting—press firmly to keep it in place.",
    },
    "regular with wings": {
        "name": "Regular Pads (With Wings)",
        "benefits": "Everyday protection with wings for a more secure fit.",
        "tip": "Wings help prevent shifting—press firmly to keep it in place.",
    },
    "regular w wings": {
        "name": "Regular Pads (With Wings)",
        "benefits": "Everyday protection with wings for a more secure fit.",
        "tip": "Wings help prevent shifting—press firmly to keep it in place.",
    },
    "non-wing pads": {
        "name": "Non-wing Pads",
        "benefits": "Simple everyday protection without wings.",
        "tip": "If you move a lot, consider wings for extra hold.",
    },
    "non wing pad": {
        "name": "Non-wing Pads",
        "benefits": "Simple everyday protection without wings.",
        "tip": "If you move a lot, consider wings for extra hold.",
    },
    # Legacy keys below (keep only ones not already defined above)
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
    "If you have a small cut, clean it with water first, then apply alcohol around (not deep inside) and cover with a clean bandage.",
    "Don’t share towels, deodorant, or toothbrushes—this helps prevent skin infections and germs spreading.",
    "After using wet wipes, still wash with soap when you can—wipes are a quick clean, not a full wash.",
    "Mouthwash is a helper, not a replacement—brush 2 minutes and floss, then mouthwash after.",
    "Change pads/liners regularly to avoid irritation and odor—especially during heavy flow or hot days.",
    "Wear breathable underwear and change after sweating to reduce odor and skin irritation.",
    "If you’re sick, dispose tissues properly and sanitize your hands after coughing/sneezing.",
    "Tagalog: Maghugas ng kamay ng 20 segundo gamit ang sabon bago kumain at pagkatapos mag-CR.",
    "Tagalog: Iwasang hawakan ang mukha (mata, ilong, bibig) kapag hindi pa naghuhugas ng kamay.",
    "Tagalog: Magpalit ng napkin/liner nang regular para iwas amoy at iritasyon.",
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
        "This machine cannot dispense new RFID cards right now. "
        "Please buy a new card at the office."
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
