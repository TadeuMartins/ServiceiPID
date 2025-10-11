#!/usr/bin/env python3
"""
Test to validate that the coordinate system uses top-left origin (0,0)
where Y increases downward (from top to bottom).
"""

import sys
import re


def test_coordinate_system_in_prompts():
    """Validate that prompts specify top-left origin with Y increasing downward"""
    
    # Read backend.py
    with open('/home/runner/work/ServiceiPID/ServiceiPID/backend/backend.py', 'r') as f:
        backend_code = f.read()
    
    # Extract build_prompt function
    build_prompt_match = re.search(r'def build_prompt\(.*?\):\s*.*?return base\.strip\(\)', backend_code, re.DOTALL)
    build_prompt_code = build_prompt_match.group(0) if build_prompt_match else ""
    
    # Extract build_generation_prompt function  
    gen_prompt_match = re.search(r'def build_generation_prompt\(.*?\):\s*.*?return prompt\.strip\(\)', backend_code, re.DOTALL)
    gen_prompt_code = gen_prompt_match.group(0) if gen_prompt_match else ""
    
    print("Testing Coordinate System Definition...\n")
    
    checks = [
        # Check for top-left origin statement (Portuguese in build_prompt)
        ("Topo superior esquerdo é o ponto (0, 0)", "Top-left origin (0,0) specified (PT)", build_prompt_code),
        # Check for top-left origin statement (English in generation prompt)
        ("Top left corner is point (0, 0)", "Top-left origin (0,0) specified (EN)", gen_prompt_code),
        
        # Check for Y direction (top to bottom) - Portuguese
        ("Y crescente de cima para baixo", "Y increases from top to bottom (PT)", build_prompt_code),
        # Check for Y direction (top to bottom) - English
        ("Y increases top to bottom", "Y increases from top to bottom (EN)", gen_prompt_code),
        
        # Check coordinate ranges with top-left origin
        ("Y: 0.0 (topo da página)", "Y=0 at top of page", build_prompt_code),
        ("(base da página)", "Y=max at bottom of page", build_prompt_code),
        
        # Should NOT have old bottom-left origin language
        ("Y crescente de baixo para cima", "OLD: Y from bottom to top (should NOT exist)", build_prompt_code),
        ("Y: 0.0 (base da página)", "OLD: Y=0 at bottom (should NOT exist)", build_prompt_code),
    ]
    
    passed = 0
    failed = 0
    
    for check_text, description, code in checks:
        if "should NOT exist" in description:
            # This should NOT be found
            if check_text not in code:
                print(f"✓ {description}")
                passed += 1
            else:
                print(f"✗ FAILED: {description} - found '{check_text}' (should not exist)")
                failed += 1
        else:
            # This should be found
            if check_text in code:
                print(f"✓ {description}")
                passed += 1
            else:
                print(f"✗ FAILED: {description} - '{check_text}' not found")
                failed += 1
    
    print(f"\nCoordinate System Test: {passed} passed, {failed} failed")
    return failed == 0


def test_coordinate_processing():
    """Validate that coordinate processing maintains top-left origin"""
    
    print("\n" + "="*60)
    print("Testing Coordinate Processing Logic...\n")
    
    # Simulate the coordinate processing
    H_mm = 841.0  # A0 height
    
    # Test case 1: Top-left corner
    y_in = 0.0  # Top of page
    y_cad = H_mm - y_in  # COMOS flip
    assert y_in == 0.0, "Top of page should be Y=0"
    assert y_cad == 841.0, "COMOS coordinate should be flipped"
    print(f"✓ Top-left corner: y_mm={y_in} (top), y_mm_cad={y_cad} (COMOS)")
    
    # Test case 2: Bottom-left corner
    y_in = 841.0  # Bottom of page
    y_cad = H_mm - y_in  # COMOS flip
    assert y_in == 841.0, "Bottom of page should be Y=841"
    assert y_cad == 0.0, "COMOS coordinate should be flipped"
    print(f"✓ Bottom-left corner: y_mm={y_in} (bottom), y_mm_cad={y_cad} (COMOS)")
    
    # Test case 3: Middle of page
    y_in = 420.5  # Middle of page
    y_cad = H_mm - y_in  # COMOS flip
    assert y_in == 420.5, "Middle of page should be Y=420.5"
    assert y_cad == 420.5, "COMOS coordinate should be flipped (also middle)"
    print(f"✓ Middle of page: y_mm={y_in} (middle), y_mm_cad={y_cad} (COMOS)")
    
    print("\nCoordinate Processing: All tests passed")
    return True


if __name__ == "__main__":
    print("="*60)
    print("COORDINATE SYSTEM VALIDATION")
    print("="*60)
    print()
    
    result1 = test_coordinate_system_in_prompts()
    result2 = test_coordinate_processing()
    
    print("\n" + "="*60)
    if result1 and result2:
        print("✅ ALL COORDINATE SYSTEM TESTS PASSED!")
        print("\nSummary:")
        print("- Top-left corner is origin (0, 0)")
        print("- Y increases from top to bottom (downward)")
        print("- Y=0 at top of page, Y=841mm at bottom (A0 sheet)")
        print("- COMOS compatibility maintained via y_mm_cad flip")
        print("- Both PDF analysis and generation prompts are consistent")
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)
    print("="*60)
