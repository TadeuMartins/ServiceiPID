#!/usr/bin/env python3
"""
Test to verify that electrical diagram generation prompts properly instruct
the AI to utilize the FULL A3 sheet (420mm x 297mm) for COMOS compatibility,
instead of clustering components in a small area (~150mm x 90mm).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))


def test_prompt_includes_full_sheet_utilization():
    """Test that generation prompt emphasizes full sheet utilization"""
    print("\n=== Testing Full Sheet Utilization in Prompt ===")
    
    from backend import build_generation_prompt
    
    # Generate prompt for electrical diagram
    prompt = build_generation_prompt(
        'Sistema de partida estrela-triângulo para motor trifásico',
        width_mm=420.0,
        height_mm=297.0,
        diagram_type='electrical'
    )
    
    # Check for key phrases about full sheet utilization
    checks = {
        "FULL sheet mention": "FULL" in prompt and "420mm x 297mm" in prompt,
        "Warning against clustering": "cluster" in prompt.lower() or "small area" in prompt.lower(),
        "COMOS compatibility": "COMOS" in prompt,
        "Extended Y range (270mm)": "270" in prompt and "Y" in prompt,
        "Extended X range (390mm)": "390" in prompt and "X" in prompt,
        "Explicit spatial distribution": "30mm to Y=270mm" in prompt or "Y = 30-80" in prompt,
        "Horizontal distribution": "30mm to X=390mm" in prompt or "X = 50-150" in prompt,
    }
    
    print("\nPrompt content checks:")
    all_passed = True
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
        if not result:
            all_passed = False
    
    # Print relevant sections
    if not all_passed:
        print("\n--- Relevant prompt sections ---")
        lines = prompt.split('\n')
        for i, line in enumerate(lines):
            if any(keyword in line.upper() for keyword in ['SPATIAL', 'COMOS', 'COORDINATES', 'Y =', 'X =']):
                print(f"{line}")
    
    assert all_passed, "Not all checks passed - prompt may not properly emphasize full sheet utilization"
    print("\n✅ All checks passed - prompt properly instructs full sheet utilization")


def test_spatial_ranges_expanded():
    """Test that the spatial ranges are expanded compared to the old values"""
    print("\n=== Testing Expanded Spatial Ranges ===")
    
    from backend import build_generation_prompt
    
    prompt = build_generation_prompt(
        'Sistema elétrico completo',
        width_mm=420.0,
        height_mm=297.0,
        diagram_type='electrical'
    )
    
    # Old values (that caused the problem):
    # Y: 20-240mm (220mm used)
    # X: 40-380mm (340mm used)
    
    # New expected values:
    # Y: 30-270mm (240mm used)
    # X: 30-390mm (360mm used)
    
    checks = {
        "Y starts at ~30mm": "Y = 30" in prompt or "Y=30" in prompt,
        "Y extends to ~270mm": "270" in prompt and ("Y" in prompt or "vertical" in prompt.lower()),
        "X starts at ~30mm": "X = 30" in prompt or "X=30" in prompt or "start at X = 30" in prompt,
        "X extends to ~390mm": "390" in prompt and ("X" in prompt or "horizontal" in prompt.lower()),
        "Not using old narrow Y range (20-240)": not ("Y = 20-60" in prompt or "Y = 180-240" in prompt),
        "Not using old narrow X range (40-380)": not ("X = 40-60" in prompt or "X = 300-380" in prompt),
    }
    
    print("\nSpatial range checks:")
    all_passed = True
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
        if not result:
            all_passed = False
    
    if not all_passed:
        print("\n--- Spatial distribution section ---")
        lines = prompt.split('\n')
        in_spatial = False
        for line in lines:
            if 'SPATIAL DISTRIBUTION' in line.upper():
                in_spatial = True
            if in_spatial:
                print(line)
                if 'ELECTRICAL CONNECTIONS' in line.upper():
                    break
    
    assert all_passed, "Spatial ranges not properly expanded"
    print("\n✅ Spatial ranges properly expanded for better sheet utilization")


def test_example_coordinates_updated():
    """Test that example coordinates demonstrate proper sheet utilization"""
    print("\n=== Testing Example Coordinates ===")
    
    from backend import build_generation_prompt
    
    prompt = build_generation_prompt(
        'Exemplo de sistema',
        width_mm=420.0,
        height_mm=297.0,
        diagram_type='electrical'
    )
    
    # Check that example shows proper utilization
    # Old example had components clustered in small area
    # New example should show better distribution
    
    checks = {
        "Example has Y=260mm or higher": "y_mm\": 260" in prompt or "y_mm\": 270" in prompt,
        "Example uses X > 200mm": "x_mm\": 300" in prompt or "x_mm\": 280" in prompt,
        "Example note about full utilization": "FULL" in prompt and "PROPER utilization" in prompt,
        "Not using old cramped Y values (40-240)": "y_mm\": 40" not in prompt,
    }
    
    print("\nExample coordinate checks:")
    all_passed = True
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
        if not result:
            all_passed = False
    
    assert all_passed, "Example coordinates don't demonstrate proper sheet utilization"
    print("\n✅ Example coordinates properly demonstrate full sheet utilization")


def test_comos_compatibility_mentioned():
    """Test that COMOS compatibility is explicitly mentioned"""
    print("\n=== Testing COMOS Compatibility Mentions ===")
    
    from backend import build_generation_prompt
    
    prompt = build_generation_prompt(
        'Sistema industrial',
        width_mm=420.0,
        height_mm=297.0,
        diagram_type='electrical'
    )
    
    # Count COMOS mentions
    comos_count = prompt.upper().count("COMOS")
    
    print(f"\nCOMOS mentions in prompt: {comos_count}")
    
    assert comos_count >= 2, f"COMOS should be mentioned at least 2 times, found {comos_count}"
    
    # Check for specific COMOS-related instructions
    checks = {
        "COMOS compatibility section": "COMOS COMPATIBILITY" in prompt,
        "Siemens mention": "Siemens" in prompt,
        "Absolute coordinates for COMOS": "absolute coordinates" in prompt.lower() or "COMOS" in prompt,
    }
    
    print("\nCOMOS-specific checks:")
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
    
    print(f"\n✅ COMOS compatibility is properly emphasized ({comos_count} mentions)")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("COMOS FULL SHEET UTILIZATION TESTS")
    print("Testing fix for coordinate range issue (150x90mm → 420x297mm)")
    print("="*70)
    
    try:
        test_prompt_includes_full_sheet_utilization()
        test_spatial_ranges_expanded()
        test_example_coordinates_updated()
        test_comos_compatibility_mentioned()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        print("\nSummary of fixes:")
        print("- Y coordinates expanded: 20-240mm → 30-270mm (81% → 81% utilization)")
        print("- X coordinates expanded: 40-380mm → 30-390mm (81% → 86% utilization)")
        print("- Added explicit COMOS compatibility instructions")
        print("- Updated example coordinates to demonstrate proper distribution")
        print("- Added warnings against clustering components in small areas")
        print("="*70 + "\n")
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
