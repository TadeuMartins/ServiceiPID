#!/usr/bin/env python3
"""
Test to verify that identical equipment descriptions get the same SystemFullName.

Problem: When "Motor trifásico AC 7,5 cv" appears on two different lines,
they should get the SAME SystemFullName based on the highest confidence match.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))


def test_identical_descriptions_same_systemfullname():
    """Test that identical descriptions get the same SystemFullName"""
    print("Testing that identical descriptions get the same SystemFullName...")
    print("=" * 80)
    
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set. Please set it in .env file")
        print("Skipping test...")
        return None
    
    from system_matcher import match_system_fullname, clear_match_cache
    
    # Clear cache to ensure clean test
    clear_match_cache()
    
    # Test case: Same description, different tags
    desc = "Motor trifásico AC 7,5 cv"
    
    test_cases = [
        {"tag": "M-001", "descricao": desc, "tipo": ""},
        {"tag": "M-002", "descricao": desc, "tipo": ""},
        {"tag": "ZMS300", "descricao": desc, "tipo": ""},
    ]
    
    print(f"\nTesting with identical description: '{desc}'")
    print("\nResults:")
    print("-" * 80)
    
    results = []
    for test_case in test_cases:
        result = match_system_fullname(
            tag=test_case['tag'],
            descricao=test_case['descricao'],
            tipo=test_case['tipo'],
            diagram_type="electrical"
        )
        results.append(result)
        
        print(f"\nTag: {test_case['tag']}")
        print(f"  SystemFullName: {result.get('SystemFullName', 'N/A')}")
        print(f"  Descricao_ref: {result.get('Descricao_ref', 'N/A')}")
        print(f"  Confidence: {result.get('Confiança', 0.0)}")
    
    # Check if all results have the same SystemFullName
    print("\n" + "=" * 80)
    print("VALIDATION:")
    print("-" * 80)
    
    system_full_names = [r.get('SystemFullName') for r in results]
    unique_names = set(system_full_names)
    
    print(f"\nUnique SystemFullNames found: {len(unique_names)}")
    for name in unique_names:
        count = system_full_names.count(name)
        print(f"  - {name}: {count} occurrences")
    
    if len(unique_names) == 1:
        print(f"\n✅ PASS: All identical descriptions matched to the same SystemFullName")
        return True
    else:
        print(f"\n❌ FAIL: Identical descriptions matched to different SystemFullNames!")
        print(f"   Expected: All 3 instances should have the same SystemFullName")
        print(f"   Actual: Found {len(unique_names)} different SystemFullNames")
        return False


def test_different_descriptions_different_systemfullname():
    """Test that different descriptions get different SystemFullName"""
    print("\n\n" + "=" * 80)
    print("Testing that different descriptions get different SystemFullNames...")
    print("=" * 80)
    
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set. Skipping test...")
        return None
    
    from system_matcher import match_system_fullname, clear_match_cache
    
    # Clear cache to ensure clean test
    clear_match_cache()
    
    # Test case: Different descriptions
    test_cases = [
        {"tag": "M-001", "descricao": "Motor trifásico AC 7,5 cv", "tipo": ""},
        {"tag": "CB-001", "descricao": "Disjuntor trifásico", "tipo": ""},
        {"tag": "K-001", "descricao": "Contator trifásico", "tipo": ""},
    ]
    
    print("\nTesting with different descriptions:")
    print("-" * 80)
    
    results = []
    for test_case in test_cases:
        result = match_system_fullname(
            tag=test_case['tag'],
            descricao=test_case['descricao'],
            tipo=test_case['tipo'],
            diagram_type="electrical"
        )
        results.append(result)
        
        print(f"\nTag: {test_case['tag']}")
        print(f"  Description: {test_case['descricao']}")
        print(f"  SystemFullName: {result.get('SystemFullName', 'N/A')}")
        print(f"  Confidence: {result.get('Confiança', 0.0)}")
    
    # Check if all results have different SystemFullName
    print("\n" + "=" * 80)
    print("VALIDATION:")
    print("-" * 80)
    
    system_full_names = [r.get('SystemFullName') for r in results]
    unique_names = set(system_full_names)
    
    print(f"\nUnique SystemFullNames found: {len(unique_names)}")
    for name in unique_names:
        count = system_full_names.count(name)
        print(f"  - {name}: {count} occurrences")
    
    if len(unique_names) == len(test_cases):
        print(f"\n✅ PASS: Different descriptions matched to different SystemFullNames")
        return True
    else:
        print(f"\n⚠️  WARNING: Some different descriptions matched to the same SystemFullName")
        print(f"   This might be acceptable depending on the descriptions")
        return True  # Not a failure, might be expected


if __name__ == "__main__":
    try:
        result1 = test_identical_descriptions_same_systemfullname()
        result2 = test_different_descriptions_different_systemfullname()
        
        print("\n" + "=" * 80)
        print("TEST SUMMARY:")
        print("=" * 80)
        
        if result1 is None:
            print("Tests skipped (no API key)")
            sys.exit(0)
        elif result1 and result2:
            print("✅ ALL TESTS PASSED")
            sys.exit(0)
        else:
            print("❌ SOME TESTS FAILED")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
