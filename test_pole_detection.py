#!/usr/bin/env python3
"""
Test the pole detection function without needing OpenAI API.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from system_matcher import detect_pole_count


def test_pole_detection():
    """Test pole count detection from various descriptions"""
    print("Testing pole count detection...\n")
    
    test_cases = [
        # (description, expected_result)
        ("Disjuntor trifásico 250A", "3-pole"),
        ("Contator trifásico 115A", "3-pole"),
        ("Circuit-breaker 3-pole 100A", "3-pole"),
        ("Three-phase motor", "3-pole"),
        ("Disjuntor monopolar 16A", "1-pole"),
        ("Circuit-breaker 1-pole", "1-pole"),
        ("Single-pole switch", "1-pole"),
        ("Disjuntor bipolar", "2-pole"),
        ("2-pole circuit breaker", "2-pole"),
        ("Motor trifásico 5HP", "3-pole"),
        ("Tripolar contactor", "3-pole"),
        ("Unipolar fuse", "1-pole"),
        ("Disjuntor", ""),  # No pole info
        ("Generic equipment", ""),  # No pole info
    ]
    
    passed = 0
    failed = 0
    
    for description, expected in test_cases:
        result = detect_pole_count(description)
        if result == expected:
            print(f"  ✓ '{description}' -> '{result}'")
            passed += 1
        else:
            print(f"  ✗ FAIL: '{description}' -> '{result}' (expected '{expected}')")
            failed += 1
    
    print(f"\nPole Detection: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    print("="*70)
    print("TESTING POLE COUNT DETECTION")
    print("="*70 + "\n")
    
    result = test_pole_detection()
    
    print("\n" + "="*70)
    if result:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)
    print("="*70)
