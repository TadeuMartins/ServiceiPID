#!/usr/bin/env python3
"""
Test to verify that the match cache works correctly.

This test demonstrates that:
1. Identical descriptions get cached and return the same result
2. The cache key is based on description + tipo + diagram_type (NOT tag)
3. Different descriptions get different matches
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))


def test_cache_mechanism():
    """Test the cache mechanism directly"""
    print("Testing match cache mechanism...")
    print("=" * 80)
    
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set. Please set it in .env file")
        print("Skipping test...")
        return None
    
    from system_matcher import match_system_fullname, clear_match_cache, match_cache
    
    # Clear cache to start fresh
    clear_match_cache()
    print("\n1. Cache cleared")
    print(f"   Cache size: {len(match_cache)}")
    
    # First call with a specific description
    desc1 = "Motor trifásico AC 7,5 cv"
    tag1 = "M-001"
    
    print(f"\n2. First call: tag={tag1}, desc='{desc1}'")
    result1 = match_system_fullname(tag1, desc1, "", "electrical")
    print(f"   SystemFullName: {result1.get('SystemFullName')}")
    print(f"   Confidence: {result1.get('Confiança')}")
    print(f"   Cache size after call: {len(match_cache)}")
    
    # Second call with SAME description but DIFFERENT tag
    tag2 = "M-002"
    print(f"\n3. Second call: tag={tag2}, desc='{desc1}' (SAME description)")
    result2 = match_system_fullname(tag2, desc1, "", "electrical")
    print(f"   SystemFullName: {result2.get('SystemFullName')}")
    print(f"   Confidence: {result2.get('Confiança')}")
    print(f"   Cache size after call: {len(match_cache)} (should still be 1)")
    
    # Verify they match
    if result1.get('SystemFullName') == result2.get('SystemFullName'):
        print(f"\n   ✅ Results match! Both got: {result1.get('SystemFullName')}")
    else:
        print(f"\n   ❌ Results differ!")
        print(f"      First:  {result1.get('SystemFullName')}")
        print(f"      Second: {result2.get('SystemFullName')}")
        return False
    
    # Third call with DIFFERENT description
    desc2 = "Disjuntor trifásico"
    tag3 = "CB-001"
    print(f"\n4. Third call: tag={tag3}, desc='{desc2}' (DIFFERENT description)")
    result3 = match_system_fullname(tag3, desc2, "", "electrical")
    print(f"   SystemFullName: {result3.get('SystemFullName')}")
    print(f"   Confidence: {result3.get('Confiança')}")
    print(f"   Cache size after call: {len(match_cache)} (should be 2)")
    
    # Verify it's different from the motor
    if result3.get('SystemFullName') != result1.get('SystemFullName'):
        print(f"\n   ✅ Correctly got different SystemFullName for different description")
    else:
        print(f"\n   ⚠️  WARNING: Got same SystemFullName for different descriptions")
        print(f"      (This might be acceptable depending on the match)")
    
    # Fourth call - same as first (to verify cache hit)
    tag4 = "ZMS300"
    print(f"\n5. Fourth call: tag={tag4}, desc='{desc1}' (SAME as first)")
    result4 = match_system_fullname(tag4, desc1, "", "electrical")
    print(f"   SystemFullName: {result4.get('SystemFullName')}")
    print(f"   Confidence: {result4.get('Confiança')}")
    print(f"   Cache size after call: {len(match_cache)} (should still be 2)")
    
    # Verify cache hit
    if result4.get('SystemFullName') == result1.get('SystemFullName'):
        print(f"\n   ✅ Cache hit! All motor descriptions got: {result1.get('SystemFullName')}")
    else:
        print(f"\n   ❌ Cache miss! Results differ")
        return False
    
    print("\n" + "=" * 80)
    print("CACHE BEHAVIOR SUMMARY:")
    print("-" * 80)
    print(f"Total cache entries: {len(match_cache)}")
    print(f"Cache keys: {list(match_cache.keys())}")
    
    return True


if __name__ == "__main__":
    try:
        result = test_cache_mechanism()
        
        print("\n" + "=" * 80)
        if result is None:
            print("Test skipped (no API key)")
            sys.exit(0)
        elif result:
            print("✅ CACHE TEST PASSED")
            sys.exit(0)
        else:
            print("❌ CACHE TEST FAILED")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
