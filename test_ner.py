"""
Test script for EntityRecognizer.
"""
from src.entity_recognizer import EntityRecognizer
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)

def test_ner():
    print("Initializing EntityRecognizer...")
    ner = EntityRecognizer()

    test_cases = [
        ("Prime Minister Narendra Modi visited the new temple in Ayodhya.", "Narendra Modi", True),
        ("CR Patil announced a new scheme for farmers in Gujarat.", "CR Patil", True),
        ("Modi Toys are popular in the market.", "Narendra Modi", False), # Ambiguous/Not Person
        ("The patrol team secured the border.", "CR Patil", False),
        ("Rahul Gandhi criticized the government policy.", "Narendra Modi", False),
        ("PM Modi addressed the nation.", "Narendra Modi", True) # Should detect partially
    ]

    print("\nRunning NER Tests:\n")
    passed = 0
    for text, person, expected in test_cases:
        # Debug: show what entities Spacy finds
        entities = ner.extract_entities(text)
        print(f"DEBUG: Text='{text}' -> Entities={entities}")

        result = ner.verify_person(text, person)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        if result == expected:
            passed += 1
        print(f"[{status}] Person: '{person}' | Text: '{text[:50]}...' | Found: {result}")

    print(f"\nResult: {passed}/{len(test_cases)} passed.")

if __name__ == "__main__":
    test_ner()
