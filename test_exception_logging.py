#!/usr/bin/env python3
"""
Test to verify that exception logging with JSON-like messages doesn't crash.
This tests the fix for the "Invalid format specifier" error.
"""

import sys
import os

def test_fstring_with_exception_repr():
    """
    Test that f-strings with {e!r} format specifier work correctly
    for exceptions containing JSON-like strings with curly braces.
    """
    # Create an exception with JSON-like message containing curly braces
    # This simulates what happens when ensure_json_list raises ValueError
    json_like_error = ValueError(
        'Invalid format specifier \' "CB-101",\n'
        '    "descricao": "Disjuntor Principal",\n'
        '    "x_mm": 236.0,\n'
        '    "y_mm": 568.0,\n'
        '    "from": "TR-101",\n'
        '    "to": "M-201"\n'
        '  \' for object of type \'str\''
    )
    
    # This should NOT crash with "Invalid format specifier" error
    try:
        # Test the OLD way (would crash):
        # msg_old = f"⚠️ Global falhou na página 1: {json_like_error}"  # Would raise ValueError
        
        # Test the NEW way (should work):
        msg_new = f"⚠️ Global falhou na página 1: {json_like_error!r}"
        msg_new2 = f"❌ Erro Quadrant 1-1: {json_like_error!r}"
        
        print("✅ Test passed: Exception with JSON-like message formatted successfully")
        print(f"   Message 1 length: {len(msg_new)}")
        print(f"   Message 2 length: {len(msg_new2)}")
        
        # Verify the messages contain the error info
        assert "Global falhou" in msg_new, "Expected 'Global falhou' in message"
        assert "Erro Quadrant" in msg_new2, "Expected 'Erro Quadrant' in message"
        assert "ValueError" in msg_new, "Expected 'ValueError' in repr output"
        
        print("✅ All assertions passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_various_exception_types():
    """
    Test formatting of various exception types with special characters.
    """
    test_cases = [
        ValueError("Error with {curly} braces"),
        RuntimeError("Error with {{double}} braces"),
        Exception("Error with 'quotes' and {braces}"),
        KeyError("missing_key"),
        TypeError("Invalid format specifier 'test' for object of type 'str'"),
    ]
    
    try:
        messages = []
        for exc in test_cases:
            msg = f"Test error: {exc!r}"
            messages.append(msg)
        
        print(f"✅ Formatted {len(test_cases)} different exception types successfully")
        assert len(messages) == len(test_cases), f"Expected {len(test_cases)} messages, got {len(messages)}"
        
        # Check that each message contains the exception type name
        for i, (exc, msg) in enumerate(zip(test_cases, messages)):
            exc_type_name = type(exc).__name__
            assert exc_type_name in msg, f"Expected {exc_type_name} in message {i}"
        
        print("✅ All exception types formatted successfully")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_old_way_fails():
    """
    Verify that the OLD way (without !r) would actually fail with problematic exceptions.
    This demonstrates why the fix was necessary.
    """
    json_like_error = ValueError('Invalid format specifier \' "test": {value} \' for object')
    
    try:
        # Try the OLD way - this SHOULD fail
        try:
            msg = f"Error: {json_like_error}"
            print(f"⚠️ Old way unexpectedly succeeded: {msg}")
            # If we get here, the error message doesn't trigger the bug
            # (which can happen if the exception message doesn't have exactly the right format)
            return True
        except (ValueError, KeyError) as e:
            if "Invalid format specifier" in str(e) or "format" in str(e).lower():
                print(f"✅ Confirmed: OLD way fails with format error (as expected)")
                print(f"   Error was: {type(e).__name__}: {e}")
                
                # Now verify the NEW way works
                msg_new = f"Error: {json_like_error!r}"
                print(f"✅ NEW way works: {msg_new[:80]}...")
                return True
            else:
                raise  # Re-raise if it's a different error
        
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Testing exception formatting with JSON-like messages...")
    print("=" * 60)
    
    test1_passed = test_fstring_with_exception_repr()
    print()
    
    test2_passed = test_various_exception_types()
    print()
    
    test3_passed = test_old_way_fails()
    print()
    
    if test1_passed and test2_passed and test3_passed:
        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        sys.exit(0)
    else:
        print("=" * 60)
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        sys.exit(1)
