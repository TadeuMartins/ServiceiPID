#!/usr/bin/env python3
"""
Test to verify that electrical equipment pole matching works correctly.
This test ensures that when equipment is described as multipolar (e.g., "trifásico"),
the system matcher returns the correct pole count in SystemFullName.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from system_matcher import match_system_fullname


def test_triphasic_circuit_breaker():
    """Test that 'Disjuntor trifásico' matches to 3-pole circuit breaker"""
    print("Testing triphasic circuit breaker matching...\n")
    
    # Real example from problem statement
    result = match_system_fullname(
        tag="A-Q1",
        descricao="Disjuntor trifásico 250A",
        tipo="",
        diagram_type="electrical",
        diagram_subtype="multifilar"
    )
    
    print(f"  Tag: A-Q1")
    print(f"  Description: Disjuntor trifásico 250A")
    print(f"  Matched SystemFullName: {result.get('SystemFullName')}")
    print(f"  Confidence: {result.get('Confiança')}")
    print(f"  Reference Type: {result.get('Tipo_ref')}")
    print(f"  Reference Description: {result.get('Descricao_ref')}")
    
    # Should match 3-pole, not 1-pole
    # Expected: Circuit-breaker with 3-pole
    # SystemFullName should end with A30 (3-pole) not A10 (1-pole)
    system_name = result.get('SystemFullName', '')
    ref_desc = result.get('Descricao_ref', '')
    
    # Check that it's a 3-pole match
    is_3_pole = '3-pole' in ref_desc.lower()
    is_not_1_pole = '1-pole' not in ref_desc.lower()
    
    if is_3_pole and is_not_1_pole:
        print(f"  ✓ PASS: Correctly matched to 3-pole equipment\n")
        return True
    else:
        print(f"  ✗ FAIL: Incorrectly matched to non-3-pole equipment")
        print(f"         Expected: 3-pole circuit breaker")
        print(f"         Got: {ref_desc}\n")
        return False


def test_triphasic_contactor():
    """Test that 'Contator trifásico' matches appropriately"""
    print("Testing triphasic contactor matching...\n")
    
    # Real example from problem statement
    result = match_system_fullname(
        tag="A-K1",
        descricao="Contator trifásico 115A",
        tipo="",
        diagram_type="electrical",
        diagram_subtype="multifilar"
    )
    
    print(f"  Tag: A-K1")
    print(f"  Description: Contator trifásico 115A")
    print(f"  Matched SystemFullName: {result.get('SystemFullName')}")
    print(f"  Confidence: {result.get('Confiança')}")
    print(f"  Reference Type: {result.get('Tipo_ref')}")
    print(f"  Reference Description: {result.get('Descricao_ref')}")
    
    # Contactors in reference don't have pole variants, but should still match contactor
    ref_desc = result.get('Descricao_ref', '').lower()
    
    # Check that it matched to a contactor (not circuit breaker or fuse)
    is_contactor = 'contactor' in ref_desc
    is_not_breaker = 'breaker' not in ref_desc and 'disjuntor' not in ref_desc
    is_not_fuse = 'fuse' not in ref_desc
    
    if is_contactor and is_not_breaker and is_not_fuse:
        print(f"  ✓ PASS: Correctly matched to contactor\n")
        return True
    else:
        print(f"  ✗ FAIL: Did not match to contactor")
        print(f"         Expected: contactor")
        print(f"         Got: {ref_desc}\n")
        return False


def test_single_pole_equipment():
    """Test that single-pole equipment matches to 1-pole"""
    print("Testing single-pole equipment matching...\n")
    
    result = match_system_fullname(
        tag="Q1",
        descricao="Disjuntor monopolar 16A",
        tipo="",
        diagram_type="electrical",
        diagram_subtype="multifilar"
    )
    
    print(f"  Tag: Q1")
    print(f"  Description: Disjuntor monopolar 16A")
    print(f"  Matched SystemFullName: {result.get('SystemFullName')}")
    print(f"  Confidence: {result.get('Confiança')}")
    print(f"  Reference Description: {result.get('Descricao_ref')}")
    
    ref_desc = result.get('Descricao_ref', '')
    
    # Should match to 1-pole
    is_1_pole = '1-pole' in ref_desc.lower()
    is_not_3_pole = '3-pole' not in ref_desc.lower()
    
    if is_1_pole and is_not_3_pole:
        print(f"  ✓ PASS: Correctly matched to 1-pole equipment\n")
        return True
    else:
        print(f"  ✗ FAIL: Did not match to 1-pole equipment")
        print(f"         Expected: 1-pole")
        print(f"         Got: {ref_desc}\n")
        return False


def test_three_phase_motor():
    """Test that three-phase motor matches appropriately"""
    print("Testing three-phase motor matching...\n")
    
    result = match_system_fullname(
        tag="M1",
        descricao="Motor trifásico 5HP",
        tipo="",
        diagram_type="electrical",
        diagram_subtype="multifilar"
    )
    
    print(f"  Tag: M1")
    print(f"  Description: Motor trifásico 5HP")
    print(f"  Matched SystemFullName: {result.get('SystemFullName')}")
    print(f"  Confidence: {result.get('Confiança')}")
    print(f"  Reference Description: {result.get('Descricao_ref')}")
    
    ref_desc = result.get('Descricao_ref', '').lower()
    
    # Should match to motor (not circuit breaker or other equipment)
    is_motor = 'motor' in ref_desc
    
    if is_motor:
        print(f"  ✓ PASS: Correctly matched to motor\n")
        return True
    else:
        print(f"  ✗ FAIL: Did not match to motor")
        print(f"         Expected: motor")
        print(f"         Got: {ref_desc}\n")
        return False


if __name__ == "__main__":
    print("="*70)
    print("TESTING ELECTRICAL EQUIPMENT POLE MATCHING")
    print("="*70 + "\n")
    
    try:
        result1 = test_triphasic_circuit_breaker()
        result2 = test_triphasic_contactor()
        result3 = test_single_pole_equipment()
        result4 = test_three_phase_motor()
        
        print("="*70)
        if result1 and result2 and result3 and result4:
            print("✅ ALL TESTS PASSED!")
            print("\nSummary:")
            print("- Triphasic circuit breakers match to 3-pole")
            print("- Triphasic contactors match correctly")
            print("- Single-pole equipment matches to 1-pole")
            print("- Three-phase motors match to motors")
        else:
            print("❌ SOME TESTS FAILED")
            sys.exit(1)
        print("="*70)
    except Exception as e:
        print(f"❌ ERROR during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
