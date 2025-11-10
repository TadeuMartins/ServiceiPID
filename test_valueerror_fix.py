#!/usr/bin/env python3
"""
Comprehensive test demonstrating that the ValueError fix works correctly.
This test simulates the exact scenario from the problem statement.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_no_valueerror():
    """Test that build_prompt no longer raises ValueError"""
    from backend import build_prompt
    
    print("=" * 70)
    print("TESTING FIX FOR: ValueError('Invalid format specifier ...')")
    print("=" * 70)
    
    test_cases = [
        {
            'name': 'Electrical Diagram - Global',
            'width': 420.0,
            'height': 297.0,
            'scope': 'global',
            'diagram_type': 'electrical',
            'expected_content': [
                '"tag": "CB-101"',
                '"descricao": "Disjuntor Principal"',
                '"x_mm": 236.0',
                '"y_mm": 568.0',
                '"from": "TR-101"',
                '"to": "M-201"'
            ]
        },
        {
            'name': 'Electrical Diagram - Quadrant',
            'width': 140.0,
            'height': 99.0,
            'scope': 'quadrant',
            'origin': (0.0, 0.0),
            'quad_label': '1-1',
            'diagram_type': 'electrical',
            'expected_content': [
                '"tag": "CB-101"',
                'VOCÊ ESTÁ ANALISANDO APENAS O QUADRANTE 1-1'
            ]
        },
        {
            'name': 'P&ID - Global',
            'width': 1189.0,
            'height': 841.0,
            'scope': 'global',
            'diagram_type': 'pid',
            'expected_content': [
                '"tag": "P-101"',
                '"descricao": "Bomba Centrífuga"',
                '"x_mm": 234.5',
                '"y_mm": 567.8'
            ]
        },
        {
            'name': 'P&ID - Quadrant',
            'width': 396.3,
            'height': 280.3,
            'scope': 'quadrant',
            'origin': (0.0, 0.0),
            'quad_label': '1-1',
            'diagram_type': 'pid',
            'expected_content': [
                '"tag": "P-101"',
                'VOCÊ ESTÁ ANALISANDO APENAS O QUADRANTE 1-1'
            ]
        }
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        print(f"\n📋 Test: {test['name']}")
        print("-" * 70)
        
        try:
            # Call build_prompt - this is where the ValueError was occurring
            if test['scope'] == 'global':
                prompt = build_prompt(
                    test['width'],
                    test['height'],
                    scope=test['scope'],
                    diagram_type=test['diagram_type']
                )
            else:
                prompt = build_prompt(
                    test['width'],
                    test['height'],
                    scope=test['scope'],
                    origin=test['origin'],
                    quad_label=test['quad_label'],
                    diagram_type=test['diagram_type']
                )
            
            # Check that expected content is present
            all_present = True
            for expected in test['expected_content']:
                if expected not in prompt:
                    print(f"   ❌ Expected content not found: {expected}")
                    all_present = False
            
            if all_present:
                print(f"   ✅ PASSED: No ValueError raised")
                print(f"   ✅ PASSED: All expected content present")
                passed += 1
            else:
                print(f"   ❌ FAILED: Some expected content missing")
                failed += 1
                
        except ValueError as e:
            print(f"   ❌ FAILED: ValueError raised: {str(e)[:100]}...")
            failed += 1
        except Exception as e:
            print(f"   ❌ FAILED: Unexpected error: {type(e).__name__}: {str(e)[:100]}")
            failed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print("=" * 70)
    
    if failed > 0:
        print("\n❌ Some tests failed")
        return False
    else:
        print("\n✅ ALL TESTS PASSED")
        print("\n📝 What was fixed:")
        print("   - JSON examples in f-strings now use escaped braces {{...}}")
        print("   - This produces literal braces {...} in the output")
        print("   - No more ValueError: Invalid format specifier errors")
        print("\n📊 Impact:")
        print("   - The error from the problem statement is resolved:")
        print("     ❌ Before: ValueError('Invalid format specifier \\' \"CB-101\",...")
        print("     ✅ After:  No error, prompt generated successfully")
        return True

if __name__ == "__main__":
    success = test_no_valueerror()
    sys.exit(0 if success else 1)
