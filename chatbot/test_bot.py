"""Quick test for the Hygiene Hero chatbot engine."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot.engine import HygieneHeroBot

bot = HygieneHeroBot()

tests = [
    ("hello",                                    "Greeting"),
    ("what products do you sell?",                "Products"),
    ("why is 70 percent alcohol better than 40",  "70vs40"),
    ("give me a hygiene tip",                     "Tip"),
    ("how to use",                                "Troubleshoot"),
    ("I have a wound",                            "FirstAid"),
    ("who are you",                               "About"),
    ("heart attack",                              "Emergency"),
    ("bye",                                       "Farewell"),
]

all_ok = True
for msg, name in tests:
    bot_fresh = HygieneHeroBot()
    resp = bot_fresh.get_response(msg)
    ok = len(resp) > 5
    status = "PASS" if ok else "FAIL"
    if not ok:
        all_ok = False
    print(f"  {status}  {name:15s}  -> {resp[:80]}...")

print()
# Specific checks
bot2 = HygieneHeroBot()
about = bot2.get_response("who are you")
assert "Hygiene Hero" in about, f"About should contain 'Hygiene Hero', got: {about}"
print("  PASS  About contains 'Hygiene Hero'")

bot3 = HygieneHeroBot()
emerg = bot3.get_response("someone is having a heart attack")
assert "emergency" in emerg.lower(), f"Emergency should contain 'emergency', got: {emerg}"
print("  PASS  Emergency response correct")

print(f"\n{'ALL TESTS PASSED!' if all_ok else 'SOME TESTS FAILED!'}")
