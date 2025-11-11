#!/usr/bin/env python3
"""
Test script to verify that cables and busbars are excluded from electrical diagram analysis.
This test ensures the AI receives the instruction to ignore cables and busbars.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend import build_prompt


def test_electrical_cable_busbar_exclusion():
    """Test that electrical diagram prompts explicitly exclude cables and busbars"""
    print("Testing Electrical Diagram Cable and Busbar Exclusion...\n")
    
    # Generate electrical diagram prompt
    electrical_prompt = build_prompt(420.0, 297.0, scope="global", diagram_type="electrical")
    
    # Check for exclusion instruction
    exclusion_checks = [
        ("⚠️ IMPORTANTE - FOCO EM OBJETOS PRINCIPAIS:", "Warning header present"),
        ("NÃO extraia cabos", "Instruction to not extract cables"),
        ("linhas de potência", "Mentions power lines to exclude"),
        ("barramentos", "Mentions busbars to exclude"),
        ("DESCONSIDERADOS na extração", "Clear statement to disregard"),
        ("Foque SOMENTE nos componentes principais", "Focus on main components"),
    ]
    
    # Check that cables and busbars are NOT in the equipment list
    equipment_exclusion_checks = [
        ("Barramentos (busbars): BB-XXX, BUS-XXX", "Busbars should NOT be in equipment list"),
        ("4. Cabos e conexões:", "Cables section should NOT exist"),
        ("Linhas de potência (power lines)", "Power lines should NOT be in equipment list"),
        ("Cabos de controle", "Control cables should NOT be in equipment list"),
    ]
    
    # Check that main components are still present
    component_checks = [
        ("Transformadores", "Transformers still in list"),
        ("Motores elétricos", "Electric motors still in list"),
        ("Disjuntores", "Circuit breakers still in list"),
        ("Relés de proteção", "Protection relays still in list"),
        ("Contatores", "Contactors still in list"),
    ]
    
    passed = 0
    failed = 0
    
    print("Checking exclusion instruction IS present:")
    for check_text, description in exclusion_checks:
        if check_text in electrical_prompt:
            print(f"  ✓ {description}")
            passed += 1
        else:
            print(f"  ✗ FAILED: {description} - '{check_text}' not found")
            failed += 1
    
    print("\nChecking cables and busbars are NOT in equipment list:")
    for check_text, description in equipment_exclusion_checks:
        if check_text not in electrical_prompt:
            print(f"  ✓ {description}")
            passed += 1
        else:
            print(f"  ✗ FAILED: {description} - '{check_text}' should not be present")
            failed += 1
    
    print("\nChecking main components are still present:")
    for check_text, description in component_checks:
        if check_text in electrical_prompt:
            print(f"  ✓ {description}")
            passed += 1
        else:
            print(f"  ✗ FAILED: {description} - '{check_text}' not found")
            failed += 1
    
    print(f"\nElectrical Cable/Busbar Exclusion Test: {passed} passed, {failed} failed")
    return failed == 0


def test_pid_still_has_piping():
    """Test that P&ID prompts still include piping and connections"""
    print("\n" + "="*70)
    print("Testing P&ID Still Has Piping Section...\n")
    
    # Generate P&ID prompt
    pid_prompt = build_prompt(1189.0, 841.0, scope="global", diagram_type="pid")
    
    # Check that P&ID still has piping/connections section
    pid_checks = [
        ("4. Tubulações e conexões:", "Piping section still exists for P&ID"),
        ("Linhas de processo", "Process lines still in P&ID list"),
        ("flanges, uniões, derivações", "Pipe connections still in P&ID list"),
    ]
    
    # Check that electrical exclusion is NOT in P&ID
    exclusion_checks = [
        ("NÃO extraia cabos", "Cable exclusion should NOT be in P&ID"),
        ("barramentos", "Busbar mention should NOT be in P&ID"),
    ]
    
    passed = 0
    failed = 0
    
    print("Checking P&ID still has piping section:")
    for check_text, description in pid_checks:
        if check_text in pid_prompt:
            print(f"  ✓ {description}")
            passed += 1
        else:
            print(f"  ✗ FAILED: {description} - '{check_text}' not found")
            failed += 1
    
    print("\nChecking electrical exclusion is NOT in P&ID:")
    for check_text, description in exclusion_checks:
        if check_text not in pid_prompt:
            print(f"  ✓ {description}")
            passed += 1
        else:
            print(f"  ✗ FAILED: {description} - should not be in P&ID prompt")
            failed += 1
    
    print(f"\nP&ID Piping Section Test: {passed} passed, {failed} failed")
    return failed == 0


def test_quadrant_mode_has_exclusion():
    """Test that quadrant mode also has cable/busbar exclusion for electrical"""
    print("\n" + "="*70)
    print("Testing Electrical Quadrant Mode Has Exclusion...\n")
    
    # Generate electrical diagram prompt in quadrant mode
    electrical_quad_prompt = build_prompt(
        140.0, 99.0, 
        scope="quadrant", 
        origin=(100, 50), 
        quad_label="Q1",
        diagram_type="electrical"
    )
    
    # Check for exclusion instruction in quadrant mode
    checks = [
        ("⚠️ IMPORTANTE - FOCO EM OBJETOS PRINCIPAIS:", "Exclusion warning in quadrant"),
        ("NÃO extraia cabos", "Cable exclusion in quadrant"),
        ("barramentos", "Busbar exclusion in quadrant"),
    ]
    
    passed = 0
    failed = 0
    
    for check_text, description in checks:
        if check_text in electrical_quad_prompt:
            print(f"  ✓ {description}")
            passed += 1
        else:
            print(f"  ✗ FAILED: {description} - '{check_text}' not found")
            failed += 1
    
    print(f"\nElectrical Quadrant Exclusion Test: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    print("="*70)
    print("TESTING CABLE AND BUSBAR EXCLUSION FOR ELECTRICAL DIAGRAMS")
    print("="*70 + "\n")
    
    result1 = test_electrical_cable_busbar_exclusion()
    result2 = test_pid_still_has_piping()
    result3 = test_quadrant_mode_has_exclusion()
    
    print("\n" + "="*70)
    if result1 and result2 and result3:
        print("✅ ALL TESTS PASSED!")
        print("\nSummary:")
        print("- Electrical diagrams now explicitly exclude cables and busbars")
        print("- Exclusion instruction is prominent and clear")
        print("- Main electrical components are still identified")
        print("- P&ID diagrams still include piping/connections (no change)")
        print("- Exclusion works in both global and quadrant modes")
        print("- AI will now focus only on main objects in electrical diagrams")
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)
    print("="*70)
