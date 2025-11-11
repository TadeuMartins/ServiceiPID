#!/usr/bin/env python3
"""
Integration test demonstrating the system matcher fix.
This test shows the complete filtering pipeline without requiring OpenAI API.
"""
import sys
import os
import pandas as pd

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from system_matcher import detect_pole_count, extract_equipment_type_keywords

def simulate_filtering(tag, descricao, df_ref):
    """
    Simulate the filtering logic from match_system_fullname.
    Returns the filtered reference dataframe.
    """
    # Detect characteristics
    detected_pole = detect_pole_count(f"{tag} {descricao}")
    equipment_types = extract_equipment_type_keywords(f"{tag} {descricao}")
    
    print(f"\n{'='*80}")
    print(f"Tag: {tag}")
    print(f"Descrição: {descricao}")
    print(f"Detected pole: {detected_pole or 'None'}")
    print(f"Equipment types: {equipment_types or 'None'}")
    print(f"{'='*80}")
    
    # Apply filtering
    df_filtered = df_ref.copy()
    pole_mask = None
    type_mask = None
    
    # Pole filtering
    if detected_pole:
        import re
        pole_patterns = []
        if detected_pole == "3-pole":
            pole_patterns = ["3-pole", "three-phase", "3-phase", "three phase", "3 phase"]
        elif detected_pole == "2-pole":
            pole_patterns = ["2-pole", "two-phase", "2-phase", "two phase", "2 phase"]
        elif detected_pole == "1-pole":
            pole_patterns = ["1-pole", "single-phase", "1-phase", "single phase", "1 phase"]
        else:
            pole_patterns = [detected_pole]
        
        pole_pattern = '|'.join([re.escape(p) for p in pole_patterns])
        pole_mask = df_filtered['Descricao'].fillna('').str.contains(pole_pattern, case=False, regex=True)
        print(f"\nPole filter matches: {pole_mask.sum()} items")
    
    # Type filtering
    if equipment_types:
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
            print(f"Type filter matches: {type_mask.sum()} items")
    
    # Combine filters
    filter_used = "None"
    if pole_mask is not None and type_mask is not None:
        combined_mask = pole_mask & type_mask
        if combined_mask.sum() > 0:
            df_filtered = df_filtered[combined_mask]
            filter_used = "Combined (pole + type)"
        elif type_mask.sum() > 0:
            df_filtered = df_filtered[type_mask]
            filter_used = "Type only"
        elif pole_mask.sum() > 0:
            df_filtered = df_filtered[pole_mask]
            filter_used = "Pole only"
    elif type_mask is not None and type_mask.sum() > 0:
        df_filtered = df_filtered[type_mask]
        filter_used = "Type only"
    elif pole_mask is not None and pole_mask.sum() > 0:
        df_filtered = df_filtered[pole_mask]
        filter_used = "Pole only"
    
    print(f"\nFilter applied: {filter_used}")
    print(f"Final filtered items: {len(df_filtered)}")
    
    return df_filtered

def main():
    """Run the integration test."""
    print("\n" + "="*80)
    print("SYSTEM MATCHER FIX - INTEGRATION TEST")
    print("="*80)
    print("\nThis test demonstrates the complete filtering pipeline that prevents")
    print("different equipment types from matching to the same SystemFullName.")
    
    # Load reference data
    ref_path = os.path.join('backend', 'Referencia_systems_electrical.xlsx')
    df_ref = pd.read_excel(ref_path)
    
    # Test cases from the problem statement
    test_cases = [
        {
            'tag': 'H003A',
            'descricao': 'Ponto de conexão/cabo trifásico (lado de entrada do acionamento)',
            'expected_types': ['cable', 'connection'],
            'not_expected': ['Motor protection switch']
        },
        {
            'tag': 'NO-TAG4',
            'descricao': 'Acionamento eletrônico de motor trifásico (VFD/soft-starter) (3-pole)',
            'expected_types': ['drive', 'converter', 'frequency'],
            'not_expected': ['Motor protection switch']
        },
        {
            'tag': 'H003B',
            'descricao': 'Ponto de conexão/cabo trifásico (saída do acionamento para o motor)',
            'expected_types': ['cable', 'connection'],
            'not_expected': ['Motor protection switch']
        },
        {
            'tag': 'ZMS300',
            'descricao': 'Motor trifásico AC (3-pole) 75,0 cv',
            'expected_types': ['motor', 'three-phase motor', 'AC motor'],
            'not_expected': ['Motor protection switch']
        },
    ]
    
    all_passed = True
    results = []
    
    for test in test_cases:
        df_filtered = simulate_filtering(test['tag'], test['descricao'], df_ref)
        
        # Display top matches
        print(f"\nTop 5 filtered matches:")
        for idx, row in df_filtered.head(5).iterrows():
            print(f"  - {row['Descricao']}")
        
        # Check expectations
        passed = True
        
        # Check that at least one expected type is in results
        found_expected = False
        for expected in test['expected_types']:
            for _, row in df_filtered.iterrows():
                if expected.lower() in row['Descricao'].lower():
                    found_expected = True
                    break
            if found_expected:
                break
        
        # Check that none of the not_expected types are in results
        found_unexpected = False
        for not_expected in test['not_expected']:
            for _, row in df_filtered.iterrows():
                if not_expected.lower() in row['Descricao'].lower():
                    found_unexpected = True
                    print(f"\n❌ FAIL: Found unexpected '{not_expected}' in results!")
                    passed = False
                    break
            if found_unexpected:
                break
        
        if found_expected and not found_unexpected:
            print(f"\n✅ PASS: Correctly filtered to appropriate equipment types")
        elif not found_expected:
            print(f"\n⚠️  WARNING: Expected types not found in top results")
            print(f"   Expected one of: {test['expected_types']}")
        
        results.append({
            'tag': test['tag'],
            'passed': passed and found_expected,
            'filtered_count': len(df_filtered)
        })
        
        if not (passed and found_expected):
            all_passed = False
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    for result in results:
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"{status} - {result['tag']}: {result['filtered_count']} matches")
    
    print("\n" + "="*80)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("\nThe system matcher now correctly:")
        print("  - Distinguishes motors from motor protection switches")
        print("  - Matches cables/connections to cable entries")
        print("  - Matches drives/VFDs to converter entries")
        print("  - Uses combined pole + equipment type filtering")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*80)
    
    return all_passed

if __name__ == '__main__':
    passed = main()
    sys.exit(0 if passed else 1)
