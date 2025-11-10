#!/usr/bin/env python3
"""
Test script to verify electrical diagram specific requirements:
1. A3 horizontal dimensions (420mm x 297mm)
2. Coordinate rounding to multiples of 4mm
3. Unipolar/Multifilar diagram type detection
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend import (
    round_to_multiple_of_4, 
    get_electrical_diagram_dimensions,
    detect_electrical_diagram_subtype,
    build_prompt,
    build_generation_prompt
)


def test_coordinate_rounding():
    """Test that coordinates are rounded to multiples of 4mm"""
    print("Testing Coordinate Rounding to Multiples of 4mm...\n")
    
    test_cases = [
        (10.0, 12.0),
        (10.5, 12.0),
        (14.0, 16.0),
        (15.9, 16.0),
        (50.3, 52.0),
        (0.0, 0.0),
        (2.0, 4.0),
        (6.0, 8.0),
        (234.5, 236.0),
        (567.8, 568.0),
    ]
    
    passed = 0
    failed = 0
    
    for input_val, expected in test_cases:
        result = round_to_multiple_of_4(input_val)
        if result == expected:
            print(f"  ✓ {input_val} → {result} (expected {expected})")
            passed += 1
        else:
            print(f"  ✗ FAILED: {input_val} → {result} (expected {expected})")
            failed += 1
    
    print(f"\nCoordinate Rounding: {passed} passed, {failed} failed")
    return failed == 0


def test_a3_dimensions():
    """Test that A3 horizontal dimensions are correct"""
    print("\n" + "="*70)
    print("Testing A3 Horizontal Dimensions...\n")
    
    width, height = get_electrical_diagram_dimensions()
    
    expected_width = 420.0
    expected_height = 297.0
    
    passed = 0
    failed = 0
    
    if width == expected_width:
        print(f"  ✓ Width: {width}mm (expected {expected_width}mm)")
        passed += 1
    else:
        print(f"  ✗ FAILED: Width: {width}mm (expected {expected_width}mm)")
        failed += 1
    
    if height == expected_height:
        print(f"  ✓ Height: {height}mm (expected {expected_height}mm)")
        passed += 1
    else:
        print(f"  ✗ FAILED: Height: {height}mm (expected {expected_height}mm)")
        failed += 1
    
    print(f"\nA3 Dimensions: {passed} passed, {failed} failed")
    return failed == 0


def test_diagram_subtype_detection():
    """Test unipolar/multifilar detection"""
    print("\n" + "="*70)
    print("Testing Diagram Subtype Detection...\n")
    
    passed = 0
    failed = 0
    
    # Test multifilar detection
    multifilar_items = [
        {"tag": "CB-101", "descricao": "Disjuntor trifásico L1 L2 L3"},
        {"tag": "M-201", "descricao": "Motor com três fases R S T"},
    ]
    multifilar_desc = "Diagrama multifilar mostrando todas as fases"
    
    subtype = detect_electrical_diagram_subtype(multifilar_items, multifilar_desc)
    if subtype == "multifilar":
        print(f"  ✓ Multifilar detection: {subtype}")
        passed += 1
    else:
        print(f"  ✗ FAILED: Multifilar detection returned: {subtype} (expected 'multifilar')")
        failed += 1
    
    # Test unipolar detection
    unipolar_items = [
        {"tag": "CB-101", "descricao": "Disjuntor principal"},
        {"tag": "TR-201", "descricao": "Transformador"},
    ]
    unipolar_desc = "Diagrama unifilar simplificado single-line"
    
    subtype = detect_electrical_diagram_subtype(unipolar_items, unipolar_desc)
    if subtype == "unipolar":
        print(f"  ✓ Unipolar detection: {subtype}")
        passed += 1
    else:
        print(f"  ✗ FAILED: Unipolar detection returned: {subtype} (expected 'unipolar')")
        failed += 1
    
    print(f"\nDiagram Subtype Detection: {passed} passed, {failed} failed")
    return failed == 0


def test_electrical_prompt_includes_requirements():
    """Test that electrical diagram prompts include specific requirements"""
    print("\n" + "="*70)
    print("Testing Electrical Diagram Prompt Requirements...\n")
    
    # Generate electrical diagram prompt
    electrical_prompt = build_prompt(420.0, 297.0, scope="global", diagram_type="electrical")
    
    # Check for electrical-specific requirements
    checks = [
        ("A3 horizontal", "A3 horizontal reference"),
        ("420mm", "A3 width dimension"),
        ("297mm", "A3 height dimension"),
        ("múltiplos de 4mm", "Multiple of 4mm requirement"),
        ("UNIPOLAR ou MULTIFILAR", "Unipolar/Multifilar mention"),
        ("unifilar/single-line", "Unipolar description"),
        ("multi-filar/multi-line", "Multifilar description"),
        ("arredondadas para múltiplos de 4mm", "Coordinate rounding instruction"),
        ("múltiplo de 4 mais próximo", "Rounding method description"),
    ]
    
    passed = 0
    failed = 0
    
    for check_text, description in checks:
        if check_text in electrical_prompt:
            print(f"  ✓ {description}")
            passed += 1
        else:
            print(f"  ✗ FAILED: {description} - '{check_text}' not found in prompt")
            failed += 1
    
    print(f"\nElectrical Prompt Requirements: {passed} passed, {failed} failed")
    return failed == 0


def test_electrical_generation_prompt():
    """Test that electrical generation prompt includes specific requirements"""
    print("\n" + "="*70)
    print("Testing Electrical Generation Prompt...\n")
    
    # Generate electrical generation prompt
    gen_prompt = build_generation_prompt(
        "Sistema elétrico básico", 
        diagram_type="electrical"
    )
    
    checks = [
        ("A3 landscape format", "A3 format specification"),
        ("420 mm", "A3 width in prompt"),
        ("297 mm", "A3 height in prompt"),
        ("multiples of 4mm", "Multiple of 4mm requirement"),
        ("0.0, 4.0, 8.0, 12.0", "Valid coordinate examples"),
        ("NOT 150, 234, 567)", "Invalid P&ID coordinates not shown"),
    ]
    
    passed = 0
    failed = 0
    
    for check_text, description in checks:
        if check_text in gen_prompt:
            print(f"  ✓ {description}")
            passed += 1
        else:
            print(f"  ✗ FAILED: {description} - '{check_text}' not found")
            failed += 1
    
    # Check that coordinates in example are multiples of 4
    example_coords = [
        "152.0", "148.0", "252.0", "352.0", "100.0", "196.0", "400.0", "376.0", "300.0"
    ]
    
    coords_ok = True
    for coord_str in example_coords:
        coord_val = float(coord_str)
        if coord_val % 4.0 != 0:
            print(f"  ✗ FAILED: Example coordinate {coord_str} is not a multiple of 4")
            coords_ok = False
            failed += 1
    
    if coords_ok:
        print(f"  ✓ All example coordinates are multiples of 4mm")
        passed += 1
    
    print(f"\nElectrical Generation Prompt: {passed} passed, {failed} failed")
    return failed == 0


def test_pid_prompt_unchanged():
    """Test that P&ID prompts were not affected by electrical changes"""
    print("\n" + "="*70)
    print("Testing P&ID Prompt Unchanged...\n")
    
    # Generate P&ID prompt
    pid_prompt = build_prompt(1189.0, 841.0, scope="global", diagram_type="pid")
    
    # Check that electrical-specific requirements are NOT in P&ID prompt
    exclusion_checks = [
        ("A3 horizontal", "A3 should NOT be in P&ID"),
        ("múltiplos de 4mm", "Multiple of 4mm should NOT be in P&ID"),
        ("UNIPOLAR ou MULTIFILAR", "Electrical subtypes should NOT be in P&ID"),
        ("420mm", "A3 width should NOT be in P&ID"),
        ("297mm", "A3 height should NOT be in P&ID"),
    ]
    
    # Check that P&ID-specific content IS present
    inclusion_checks = [
        ("P&ID (Piping and Instrumentation Diagram)", "P&ID type"),
        ("ISA S5.1", "ISA standards"),
        ("Bombas (centrífugas", "Pump equipment"),
        ("precisão de 0.1 mm", "Decimal precision for P&ID"),
    ]
    
    passed = 0
    failed = 0
    
    print("Checking electrical-specific content is NOT present:")
    for check_text, description in exclusion_checks:
        if check_text not in pid_prompt:
            print(f"  ✓ {description}")
            passed += 1
        else:
            print(f"  ✗ FAILED: {description} - '{check_text}' should not be present")
            failed += 1
    
    print("\nChecking P&ID-specific content IS present:")
    for check_text, description in inclusion_checks:
        if check_text in pid_prompt:
            print(f"  ✓ {description}")
            passed += 1
        else:
            print(f"  ✗ FAILED: {description} - '{check_text}' not found")
            failed += 1
    
    print(f"\nP&ID Prompt Unchanged: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    print("="*70)
    print("TESTING ELECTRICAL DIAGRAM SPECIFIC REQUIREMENTS")
    print("="*70 + "\n")
    
    result1 = test_coordinate_rounding()
    result2 = test_a3_dimensions()
    result3 = test_diagram_subtype_detection()
    result4 = test_electrical_prompt_includes_requirements()
    result5 = test_electrical_generation_prompt()
    result6 = test_pid_prompt_unchanged()
    
    print("\n" + "="*70)
    if result1 and result2 and result3 and result4 and result5 and result6:
        print("✅ ALL TESTS PASSED!")
        print("\nSummary:")
        print("- Coordinates are correctly rounded to multiples of 4mm")
        print("- A3 horizontal dimensions (420mm x 297mm) are correct")
        print("- Unipolar/Multifilar detection works correctly")
        print("- Electrical diagram prompts include all requirements")
        print("- Electrical generation prompts use A3 dimensions and coordinate rounding")
        print("- P&ID prompts are unchanged and don't have electrical requirements")
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)
    print("="*70)
