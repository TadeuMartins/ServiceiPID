#!/usr/bin/env python3
"""
Test the improved filtering logic in system matcher.
This test verifies that the filtering correctly combines pole count and equipment type.
"""
import sys
import os
import pandas as pd
import numpy as np

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from system_matcher import detect_pole_count, extract_equipment_type_keywords

def test_filtering_logic():
    """Test that the filtering logic correctly combines pole count and equipment type."""
    
    # Load the electrical reference data
    ref_path = os.path.join('backend', 'Referencia_systems_electrical.xlsx')
    df_ref = pd.read_excel(ref_path)
    
    print("Testing filtering logic...")
    print("=" * 80)
    
    test_cases = [
        {
            'tag': 'ZMS300',
            'descricao': 'Motor trifásico AC (3-pole) 75,0 cv',
            'expected_in_results': ['Three-phase motor', 'motor', 'AC motor'],
            'not_expected': ['Motor protection switch']
        },
        {
            'tag': 'H003A',
            'descricao': 'Ponto de conexão/cabo trifásico (lado de entrada do acionamento)',
            'expected_in_results': ['Cable', 'connection'],
            'not_expected': ['Motor protection switch', 'protection switch']
        },
        {
            'tag': 'NO-TAG4',
            'descricao': 'Acionamento eletrônico de motor trifásico (VFD/soft-starter) (3-pole)',
            'expected_in_results': ['drive', 'Converter', 'starter'],
            'not_expected': ['Motor protection switch']
        },
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        tag = test_case['tag']
        descricao = test_case['descricao']
        
        print(f"\nTest {i}: {tag} - {descricao}")
        
        # Simulate the filtering logic from match_system_fullname
        detected_pole = detect_pole_count(f"{tag} {descricao}")
        equipment_types = extract_equipment_type_keywords(f"{tag} {descricao}")
        
        print(f"  Detected pole: {detected_pole}")
        print(f"  Equipment types: {equipment_types}")
        
        # Apply the filtering logic
        df_filtered = df_ref.copy()
        pole_mask = None
        type_mask = None
        
        if detected_pole:
            pole_mask = df_filtered['Descricao'].fillna('').str.contains(detected_pole, case=False, regex=False)
            print(f"  Pole matches: {pole_mask.sum()} entries")
        
        if equipment_types:
            # Build type patterns
            type_patterns = []
            for eq_type in equipment_types:
                if eq_type == 'motor':
                    type_patterns.append(r'(?!.*motor\s+(protection|starter)).*\bmotor\b')
                elif eq_type == 'protection-switch':
                    type_patterns.append(r'protection.*switch|motor.*protection')
                elif eq_type == 'motor-starter':
                    type_patterns.append(r'motor.*starter|starter')
                elif eq_type == 'drive':
                    type_patterns.append(r'drive|converter|inverter|frequency')
                elif eq_type == 'cable':
                    type_patterns.append(r'\bcable\b')
                elif eq_type == 'connection-point':
                    type_patterns.append(r'connection|terminal|point')
                else:
                    type_patterns.append(eq_type.replace('-', '.*'))
            
            if type_patterns:
                combined_pattern = '|'.join(type_patterns)
                type_mask = df_filtered['Descricao'].fillna('').str.contains(combined_pattern, case=False, regex=True)
                print(f"  Type matches: {type_mask.sum()} entries")
        
        # Combine filters
        if pole_mask is not None and type_mask is not None:
            combined_mask = pole_mask & type_mask
            if combined_mask.sum() > 0:
                df_filtered = df_filtered[combined_mask]
                print(f"  Combined (pole + type): {len(df_filtered)} entries")
            elif type_mask.sum() > 0:
                df_filtered = df_filtered[type_mask]
                print(f"  Using type only: {len(df_filtered)} entries")
            elif pole_mask.sum() > 0:
                df_filtered = df_filtered[pole_mask]
                print(f"  Using pole only: {len(df_filtered)} entries")
        elif type_mask is not None and type_mask.sum() > 0:
            df_filtered = df_filtered[type_mask]
            print(f"  Using type only: {len(df_filtered)} entries")
        elif pole_mask is not None and pole_mask.sum() > 0:
            df_filtered = df_filtered[pole_mask]
            print(f"  Using pole only: {len(df_filtered)} entries")
        
        # Check results
        print(f"\n  Filtered entries (showing first 10):")
        for idx, row in df_filtered.head(10).iterrows():
            print(f"    - {row['Descricao']}")
        
        # Verify expectations
        passed = True
        
        # Check that at least one expected term is in the results
        found_expected = False
        for expected in test_case['expected_in_results']:
            for _, row in df_filtered.iterrows():
                if expected.lower() in row['Descricao'].lower():
                    found_expected = True
                    break
            if found_expected:
                break
        
        if not found_expected:
            print(f"  ⚠️  WARNING: None of the expected terms found: {test_case['expected_in_results']}")
            passed = False
        
        # Check that none of the not_expected terms are in the results
        for not_expected in test_case['not_expected']:
            for _, row in df_filtered.iterrows():
                if not_expected.lower() in row['Descricao'].lower():
                    print(f"  ❌ FAIL: Found unexpected term '{not_expected}' in results")
                    passed = False
                    break
        
        if passed and found_expected:
            print(f"  ✅ PASS")
        else:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ All filtering tests passed!")
        return True
    else:
        print("❌ Some filtering tests failed")
        return False

if __name__ == '__main__':
    passed = test_filtering_logic()
    sys.exit(0 if passed else 1)
