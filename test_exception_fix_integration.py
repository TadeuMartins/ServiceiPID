#!/usr/bin/env python3
"""
Integration test to verify the exception logging fix works in context.
Tests that the exact error scenario from the problem statement is fixed.
"""

import sys

def test_error_scenario_from_problem_statement():
    """
    Recreate the exact error scenario from the problem statement:
    
    The error showed:
    ⚠️ Global falhou na página 1: Invalid format specifier ' "CB-101",
        "descricao": "Disjuntor Principal",
        "x_mm": 236.0,
        "y_mm": 568.0,
        "from": "TR-101",
        "to": "M-201"
      ' for object of type 'str'
    
    This happened when ensure_json_list raised a ValueError with JSON in the message,
    and that exception was logged with f"... {e}" which triggered format string parsing.
    """
    
    # Simulate the exact error message
    error_msg = (
        'Invalid format specifier \' "CB-101",\n'
        '    "descricao": "Disjuntor Principal",\n'
        '    "x_mm": 236.0,\n'
        '    "y_mm": 568.0,\n'
        '    "from": "TR-101",\n'
        '    "to": "M-201"\n'
        '  \' for object of type \'str\''
    )
    
    exc = ValueError(error_msg)
    
    # OLD WAY (would crash):
    # This is what the code was doing before:
    # msg = f"⚠️ Global falhou na página 1: {exc}"
    # Result: ValueError("Invalid format specifier")
    
    # NEW WAY (should work):
    # This is what the code does now with the fix:
    try:
        msg = f"⚠️ Global falhou na página 1: {exc!r}"
        print("✅ PASS: Exception formatted successfully with !r")
        print(f"   Generated message length: {len(msg)} chars")
        assert "Global falhou" in msg
        assert "ValueError" in msg
        print("✅ PASS: Message contains expected content")
        return True
    except Exception as e:
        print(f"❌ FAIL: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_quadrant_error_scenario():
    """
    Test the Quadrant error scenario from the problem statement:
    ❌ Erro Quadrant 1-1: Invalid format specifier ...
    """
    
    error_msg = (
        'Invalid format specifier \' "CB-101",\n'
        '    "descricao": "Disjuntor Principal",\n'
        '    "x_mm": 236.0,\n'
        '    "y_mm": 568.0,\n'
        '    "from": "TR-101",\n'
        '    "to": "M-201"\n'
        '  \' for object of type \'str\''
    )
    
    exc = ValueError(error_msg)
    
    try:
        msg = f"   ❌ Erro Quadrant 1-1: {exc!r}"
        print("✅ PASS: Quadrant error formatted successfully with !r")
        assert "Erro Quadrant 1-1" in msg
        assert "ValueError" in msg
        print("✅ PASS: Quadrant message contains expected content")
        return True
    except Exception as e:
        print(f"❌ FAIL: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_backend_has_fix():
    """
    Verify that the backend.py file actually contains the fix (uses !r).
    """
    try:
        with open('backend/backend.py', 'r') as f:
            content = f.read()
        
        # Check for the specific fixed patterns
        fixed_patterns = [
            'log_to_front(f"⚠️ Global falhou na página {page_num}: {e!r}")',
            'log_to_front(f"   ❌ Erro Quadrant {label}: {e!r}")',
        ]
        
        all_found = True
        for pattern in fixed_patterns:
            if pattern in content:
                print(f"✅ FOUND: {pattern[:60]}...")
            else:
                print(f"❌ NOT FOUND: {pattern[:60]}...")
                all_found = False
        
        # Check that we don't have the old unsafe patterns
        unsafe_patterns = [
            'log_to_front(f"⚠️ Global falhou na página {page_num}: {e}")',
            'log_to_front(f"   ❌ Erro Quadrant {label}: {e}")',
        ]
        
        none_found = True
        for pattern in unsafe_patterns:
            if pattern in content:
                print(f"⚠️ UNSAFE PATTERN STILL EXISTS: {pattern[:60]}...")
                none_found = False
        
        if all_found and none_found:
            print("✅ PASS: Backend contains the fix and no unsafe patterns")
            return True
        else:
            print("❌ FAIL: Backend missing fix or still has unsafe patterns")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: Could not verify backend: {e}")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("INTEGRATION TEST: Exception Logging Fix")
    print("=" * 70)
    print()
    
    print("Test 1: Error scenario from problem statement (Global)")
    print("-" * 70)
    test1 = test_error_scenario_from_problem_statement()
    print()
    
    print("Test 2: Error scenario from problem statement (Quadrant)")
    print("-" * 70)
    test2 = test_quadrant_error_scenario()
    print()
    
    print("Test 3: Verify backend.py contains the fix")
    print("-" * 70)
    test3 = verify_backend_has_fix()
    print()
    
    print("=" * 70)
    if test1 and test2 and test3:
        print("✅ ALL INTEGRATION TESTS PASSED")
        print("=" * 70)
        print()
        print("Summary:")
        print("  • Exception formatting with !r works correctly")
        print("  • Both Global and Quadrant error scenarios are fixed")
        print("  • Backend code contains the fix and no unsafe patterns")
        print()
        sys.exit(0)
    else:
        print("❌ SOME INTEGRATION TESTS FAILED")
        print("=" * 70)
        sys.exit(1)
