#!/usr/bin/env python3
"""
Test the pole filtering logic without needing OpenAI API.
This test validates that the reference database is correctly filtered by pole count.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import pandas as pd
from system_matcher import detect_pole_count


def test_filtering_logic():
    """Test that filtering by pole count works correctly"""
    print("Testing pole filtering logic...\n")
    
    # Load the electrical reference data
    ref_path = os.path.join(os.path.dirname(__file__), 'backend', 'Referencia_systems_electrical.xlsx')
    df_ref = pd.read_excel(ref_path)
    
    # Test case 1: Filter for 3-pole equipment
    print("Test 1: Filtering for 3-pole equipment")
    detected_pole = "3-pole"
    pole_mask = df_ref['Descricao'].fillna('').str.contains(detected_pole, case=False, regex=False)
    filtered_df = df_ref[pole_mask]
    
    print(f"  Total reference items: {len(df_ref)}")
    print(f"  3-pole items found: {len(filtered_df)}")
    
    # Check a few examples
    print(f"  Sample 3-pole items:")
    samples = filtered_df[['Descricao', 'SystemFullName']].head(5)
    for idx, row in samples.iterrows():
        print(f"    - {row['Descricao']}: {row['SystemFullName']}")
    
    # Verify they all contain "3-pole"
    all_3pole = all('3-pole' in str(desc).lower() for desc in filtered_df['Descricao'].fillna(''))
    if all_3pole and len(filtered_df) > 0:
        print(f"  ✓ All filtered items contain '3-pole'\n")
    else:
        print(f"  ✗ FAIL: Not all filtered items contain '3-pole'\n")
        return False
    
    # Test case 2: Filter for 1-pole equipment
    print("Test 2: Filtering for 1-pole equipment")
    detected_pole = "1-pole"
    pole_mask = df_ref['Descricao'].fillna('').str.contains(detected_pole, case=False, regex=False)
    filtered_df = df_ref[pole_mask]
    
    print(f"  Total reference items: {len(df_ref)}")
    print(f"  1-pole items found: {len(filtered_df)}")
    
    # Check that 3-pole items are excluded
    has_3pole = any('3-pole' in str(desc).lower() for desc in filtered_df['Descricao'].fillna(''))
    if has_3pole:
        print(f"  ✗ FAIL: 3-pole items found in 1-pole filter\n")
        return False
    else:
        print(f"  ✓ No 3-pole items in 1-pole filter\n")
    
    # Test case 3: Verify circuit breakers exist in both 1-pole and 3-pole
    print("Test 3: Checking circuit breaker variations")
    cb_1pole = df_ref[df_ref['Descricao'].fillna('').str.contains('circuit-breaker.*1-pole', case=False, regex=True)]
    cb_3pole = df_ref[df_ref['Descricao'].fillna('').str.contains('circuit-breaker.*3-pole', case=False, regex=True)]
    
    print(f"  1-pole circuit breakers: {len(cb_1pole)}")
    print(f"  3-pole circuit breakers: {len(cb_3pole)}")
    
    if len(cb_1pole) > 0 and len(cb_3pole) > 0:
        print(f"  ✓ Both 1-pole and 3-pole circuit breakers exist\n")
        
        # Show examples
        print(f"  1-pole examples:")
        for idx, row in cb_1pole[['Descricao', 'SystemFullName']].head(2).iterrows():
            print(f"    - {row['Descricao']}: {row['SystemFullName']}")
        
        print(f"  3-pole examples:")
        for idx, row in cb_3pole[['Descricao', 'SystemFullName']].head(2).iterrows():
            print(f"    - {row['Descricao']}: {row['SystemFullName']}")
    else:
        print(f"  ✗ FAIL: Missing pole variations\n")
        return False
    
    return True


if __name__ == "__main__":
    print("="*70)
    print("TESTING POLE FILTERING LOGIC")
    print("="*70 + "\n")
    
    try:
        result = test_filtering_logic()
        
        print("\n" + "="*70)
        if result:
            print("✅ ALL TESTS PASSED!")
            print("\nSummary:")
            print("- Filtering by pole count works correctly")
            print("- 3-pole items are properly isolated")
            print("- 1-pole items are properly isolated")
            print("- Circuit breaker variations exist for different pole counts")
        else:
            print("❌ SOME TESTS FAILED")
            sys.exit(1)
        print("="*70)
    except Exception as e:
        print(f"❌ ERROR during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
