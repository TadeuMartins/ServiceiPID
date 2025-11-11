#!/usr/bin/env python3
"""
Test the improved equipment type extraction logic.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from system_matcher import extract_equipment_type_keywords

def test_equipment_type_extraction():
    """Test that equipment type extraction correctly identifies equipment types."""
    
    test_cases = [
        # Test motor vs motor protection switch distinction
        {
            'text': 'Motor trifásico AC 75,0 cv',
            'expected': ['motor'],
            'not_expected': ['protection-switch']
        },
        {
            'text': 'Motor protection switch, 3-pole',
            'expected': ['protection-switch'],
            'not_expected': ['motor']  # Should not extract 'motor' from 'motor protection switch'
        },
        {
            'text': 'Disjuntor-motor trifásico',
            'expected': ['protection-switch'],
            'not_expected': ['motor']  # 'disjuntor-motor' is a protection switch
        },
        
        # Test drives and starters
        {
            'text': 'Acionamento eletrônico de motor trifásico (VFD/soft-starter)',
            'expected': ['drive'],
            'not_expected': ['motor']  # Drive is the primary equipment, not the motor
        },
        {
            'text': 'Motor starter, general',
            'expected': ['motor-starter'],
            'not_expected': ['motor']
        },
        
        # Test cables and connection points
        {
            'text': 'Ponto de conexão/cabo trifásico (lado de entrada do acionamento)',
            'expected': ['cable', 'connection-point'],
            'not_expected': []
        },
        {
            'text': 'Cable, unspecified',
            'expected': ['cable'],
            'not_expected': []
        },
        
        # Test that compound terms take priority
        {
            'text': 'Three-phase motor, single speed',
            'expected': ['motor'],
            'not_expected': []
        },
        
        # Test circuit breaker
        {
            'text': 'Disjuntor trifásico',
            'expected': ['circuit-breaker'],
            'not_expected': []
        },
    ]
    
    print("Testing equipment type extraction...")
    print("=" * 80)
    
    all_passed = True
    
    for i, test in enumerate(test_cases, 1):
        text = test['text']
        expected = test['expected']
        not_expected = test['not_expected']
        
        result = extract_equipment_type_keywords(text)
        
        print(f"\nTest {i}: {text}")
        print(f"  Extracted: {result}")
        print(f"  Expected: {expected}")
        
        # Check that all expected types are found
        missing = [e for e in expected if e not in result]
        # Check that none of the not_expected types are found
        unexpected = [n for n in not_expected if n in result]
        
        if missing or unexpected:
            all_passed = False
            print(f"  ❌ FAIL")
            if missing:
                print(f"     Missing: {missing}")
            if unexpected:
                print(f"     Unexpected: {unexpected}")
        else:
            print(f"  ✅ PASS")
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ All tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False

if __name__ == '__main__':
    passed = test_equipment_type_extraction()
    sys.exit(0 if passed else 1)
