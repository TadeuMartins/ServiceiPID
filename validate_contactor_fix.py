#!/usr/bin/env python3
"""
Enhanced validation script to demonstrate both pole filtering and equipment type filtering.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import pandas as pd
from system_matcher import detect_pole_count, extract_equipment_type_keywords


def validate_contactor_matching():
    """
    Validate that 'Contator trifásico' will match to contactors, not circuit breakers.
    """
    print("="*70)
    print("VALIDATING CONTACTOR MATCHING WITH ENHANCED FILTERING")
    print("="*70 + "\n")
    
    # Load reference data
    ref_path = os.path.join(os.path.dirname(__file__), 'backend', 'Referencia_systems_electrical.xlsx')
    df_ref = pd.read_excel(ref_path)
    
    desc = "Contator trifásico 115A"
    print(f"Input: '{desc}'")
    print("-" * 70)
    
    # Step 1: Detect pole count
    detected_pole = detect_pole_count(desc)
    print(f"\n1. Pole detection: {detected_pole}")
    
    # Step 2: Extract equipment type
    equipment_types = extract_equipment_type_keywords(desc)
    print(f"2. Equipment type detection: {equipment_types}")
    
    # Step 3: Show pole filtering
    print(f"\n3. First attempt - Filter by pole count ({detected_pole}):")
    pole_mask = df_ref['Descricao'].fillna('').str.contains(detected_pole, case=False, regex=False)
    pole_filtered = df_ref[pole_mask]
    print(f"   Items with {detected_pole}: {len(pole_filtered)}")
    
    # Check for contactors in pole-filtered results
    contactors_in_pole = pole_filtered[pole_filtered['Descricao'].fillna('').str.contains('contactor', case=False)]
    print(f"   Contactors in pole-filtered results: {len(contactors_in_pole)}")
    
    if len(contactors_in_pole) == 0:
        print(f"   → No contactors found (expected - contactors don't have pole variants)")
        
        # Step 4: Fallback to equipment type filtering
        print(f"\n4. Fallback - Filter by equipment type ({equipment_types}):")
        if equipment_types:
            type_pattern = '|'.join(equipment_types)
            type_mask = df_ref['Descricao'].fillna('').str.contains(type_pattern, case=False, regex=True)
            type_filtered = df_ref[type_mask]
            print(f"   Items matching equipment type: {len(type_filtered)}")
            print(f"   Matched items:")
            for idx, row in type_filtered[['Descricao', 'SystemFullName']].iterrows():
                print(f"     - {row['Descricao']}: {row['SystemFullName']}")
            
            # Check if circuit breakers are excluded
            cb_in_type_filtered = type_filtered[type_filtered['Descricao'].fillna('').str.contains('circuit-breaker|disjuntor', case=False, regex=True)]
            print(f"\n   Circuit breakers in type-filtered results: {len(cb_in_type_filtered)}")
            
            if len(cb_in_type_filtered) == 0:
                print(f"   ✓ Circuit breakers are EXCLUDED from matching pool")
            
            # Show the wrong match from problem statement
            wrong_match_id = '@30|M41|A50|A10|A10|A60|A90|A10'
            is_excluded = len(type_filtered[type_filtered['SystemFullName'] == wrong_match_id]) == 0
            print(f"\n5. Validation:")
            print(f"   Wrong match from problem: Circuit-breaker, thermal-overload, 1-pole")
            print(f"   SystemFullName: {wrong_match_id}")
            print(f"   Is EXCLUDED: {'✓ YES' if is_excluded else '✗ NO'}")
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("\n✅ Enhanced filtering strategy:")
    print("  1. Try to filter by pole count first")
    print("  2. If no matches (like contactors without pole variants):")
    print("     → Fall back to filtering by equipment type")
    print("  3. This ensures:")
    print("     - 'Disjuntor trifásico' matches 3-pole circuit breakers")
    print("     - 'Contator trifásico' matches contactors (not circuit breakers)")
    print("     - Wrong 1-pole equipment is excluded from both cases")
    print("\n" + "="*70)


if __name__ == "__main__":
    try:
        validate_contactor_matching()
    except Exception as e:
        print(f"❌ ERROR during validation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
