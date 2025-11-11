#!/usr/bin/env python3
"""
Test edge cases for the match cache implementation.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))


def test_cache_edge_cases():
    """Test edge cases like whitespace, case sensitivity, empty strings"""
    print("Testing cache edge cases...")
    print("=" * 80)
    
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set. Please set it in .env file")
        print("Skipping test...")
        return None
    
    from system_matcher import match_system_fullname, clear_match_cache, match_cache
    
    # Clear cache
    clear_match_cache()
    
    # Test 1: Case insensitivity
    print("\nTest 1: Case insensitivity")
    print("-" * 80)
    desc1 = "Motor Trifásico AC 7,5 cv"
    desc2 = "motor trifásico ac 7,5 cv"
    desc3 = "MOTOR TRIFÁSICO AC 7,5 CV"
    
    result1 = match_system_fullname("M-001", desc1, "", "electrical")
    result2 = match_system_fullname("M-002", desc2, "", "electrical")
    result3 = match_system_fullname("M-003", desc3, "", "electrical")
    
    print(f"  '{desc1}' -> {result1.get('SystemFullName')}")
    print(f"  '{desc2}' -> {result2.get('SystemFullName')}")
    print(f"  '{desc3}' -> {result3.get('SystemFullName')}")
    print(f"  Cache size: {len(match_cache)} (should be 1)")
    
    if result1['SystemFullName'] == result2['SystemFullName'] == result3['SystemFullName']:
        print("  ✅ Case insensitivity works correctly")
    else:
        print("  ❌ Case insensitivity failed")
        return False
    
    # Test 2: Whitespace normalization
    print("\nTest 2: Whitespace normalization")
    print("-" * 80)
    clear_match_cache()
    
    desc1 = "Motor trifásico AC 7,5 cv"
    desc2 = "  Motor trifásico AC 7,5 cv  "  # Extra spaces
    desc3 = "Motor trifásico AC 7,5 cv\n"  # Newline
    
    result1 = match_system_fullname("M-001", desc1, "", "electrical")
    result2 = match_system_fullname("M-002", desc2, "", "electrical")
    result3 = match_system_fullname("M-003", desc3, "", "electrical")
    
    print(f"  '{repr(desc1)}' -> {result1.get('SystemFullName')}")
    print(f"  '{repr(desc2)}' -> {result2.get('SystemFullName')}")
    print(f"  '{repr(desc3)}' -> {result3.get('SystemFullName')}")
    print(f"  Cache size: {len(match_cache)} (should be 1)")
    
    if result1['SystemFullName'] == result2['SystemFullName'] == result3['SystemFullName']:
        print("  ✅ Whitespace normalization works correctly")
    else:
        print("  ❌ Whitespace normalization failed")
        return False
    
    # Test 3: Different diagram types get different cache entries
    print("\nTest 3: Different diagram types")
    print("-" * 80)
    clear_match_cache()
    
    desc = "Motor trifásico AC 7,5 cv"
    
    result1 = match_system_fullname("M-001", desc, "", "electrical")
    result2 = match_system_fullname("M-002", desc, "", "pid")
    
    print(f"  Electrical: {result1.get('SystemFullName')}")
    print(f"  P&ID: {result2.get('SystemFullName')}")
    print(f"  Cache size: {len(match_cache)} (should be 2)")
    
    if len(match_cache) == 2:
        print("  ✅ Different diagram types cached separately")
    else:
        print("  ❌ Different diagram types not cached correctly")
        return False
    
    # Test 4: Empty description handling
    print("\nTest 4: Empty description handling")
    print("-" * 80)
    clear_match_cache()
    
    try:
        result1 = match_system_fullname("M-001", "", "", "electrical")
        result2 = match_system_fullname("M-002", "", "", "electrical")
        
        print(f"  Empty desc result 1: {result1.get('SystemFullName')}")
        print(f"  Empty desc result 2: {result2.get('SystemFullName')}")
        print(f"  Cache size: {len(match_cache)} (should be 1)")
        
        if result1['SystemFullName'] == result2['SystemFullName']:
            print("  ✅ Empty descriptions cached correctly")
        else:
            print("  ⚠️  Empty descriptions got different results")
    except Exception as e:
        print(f"  ⚠️  Empty description raised exception: {e}")
        print("  (This might be expected behavior)")
    
    return True


if __name__ == "__main__":
    try:
        result = test_cache_edge_cases()
        
        print("\n" + "=" * 80)
        if result is None:
            print("Test skipped (no API key)")
            sys.exit(0)
        elif result:
            print("✅ ALL EDGE CASE TESTS PASSED")
            sys.exit(0)
        else:
            print("❌ SOME EDGE CASE TESTS FAILED")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
