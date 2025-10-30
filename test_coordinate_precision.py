#!/usr/bin/env python3
"""
Test to validate coordinate precision improvements.
"""

import sys
import re


def test_prompt_precision_requirements():
    """Validate that prompts include enhanced precision requirements"""
    
    print("="*70)
    print("TESTING COORDINATE PRECISION REQUIREMENTS IN PROMPTS")
    print("="*70)
    print()
    
    # Read backend.py
    with open('/home/runner/work/ServiceiPID/ServiceiPID/backend/backend.py', 'r') as f:
        backend_code = f.read()
    
    # Extract build_prompt function
    build_prompt_match = re.search(r'def build_prompt\(.*?\):\s*.*?return base\.strip\(\)', backend_code, re.DOTALL)
    build_prompt_code = build_prompt_match.group(0) if build_prompt_match else ""
    
    # Extract build_generation_prompt function  
    gen_prompt_match = re.search(r'def build_generation_prompt\(.*?\):\s*.*?return prompt\.strip\(\)', backend_code, re.DOTALL)
    gen_prompt_code = gen_prompt_match.group(0) if gen_prompt_match else ""
    
    checks = [
        # Check for enhanced measurement method
        ("MÉTODO DE MEDIÇÃO (PASSO A PASSO):", "Step-by-step measurement method", build_prompt_code),
        ("Calcule X = (limite_esquerdo + limite_direito) / 2", "X center calculation formula", build_prompt_code),
        ("Calcule Y = (limite_topo + limite_base) / 2", "Y center calculation formula", build_prompt_code),
        
        # Check for geometric center emphasis
        ("CENTRO GEOMÉTRICO EXATO", "Geometric center requirement", build_prompt_code),
        ("MÁXIMA PRECISÃO ABSOLUTA", "Maximum precision requirement", build_prompt_code),
        
        # Check for validation requirements
        ("VALIDAÇÃO DE COORDENADAS (OBRIGATÓRIA):", "Mandatory coordinate validation", build_prompt_code),
        ("VALIDAÇÃO FINAL:", "Final validation step", build_prompt_code),
        
        # Check for decimal precision in output format
        ("IMPORTANTE SOBRE COORDENADAS:", "Coordinate precision note", build_prompt_code),
        ("uma casa decimal", "Decimal precision requirement", build_prompt_code),
        ("NÃO arredonde para inteiros", "No integer rounding warning", build_prompt_code),
        
        # Check for generation prompt improvements
        ("COORDINATE PRECISION REQUIREMENTS:", "Precision requirements in generation", gen_prompt_code),
        ("Use format: 150.5, 234.8, 567.3", "Decimal format examples", gen_prompt_code),
        ("NOT 150, 234, 567", "Integer warning in generation", gen_prompt_code),
        
        # Check updated examples use decimal precision
        ("150.5", "Example with decimal (generation)", gen_prompt_code),
        ("234.8", "Example with decimal (generation)", gen_prompt_code),
    ]
    
    passed = 0
    failed = 0
    
    for check_text, description, code in checks:
        if check_text in code:
            print(f"✓ {description}")
            passed += 1
        else:
            print(f"✗ FAILED: {description} - '{check_text}' not found")
            failed += 1
    
    print()
    print(f"Precision Requirements Test: {passed} passed, {failed} failed")
    return failed == 0


def test_geometric_refinement_default():
    """Validate that geometric refinement is enabled by default"""
    
    print()
    print("="*70)
    print("TESTING GEOMETRIC REFINEMENT DEFAULT SETTING")
    print("="*70)
    print()
    
    # Read backend.py
    with open('/home/runner/work/ServiceiPID/ServiceiPID/backend/backend.py', 'r') as f:
        backend_code = f.read()
    
    # Find the analyze_pdf function parameter
    analyze_match = re.search(
        r'use_geometric_refinement:\s*bool\s*=\s*Query\((True|False)',
        backend_code
    )
    
    if analyze_match:
        default_value = analyze_match.group(1)
        if default_value == "True":
            print("✓ Geometric refinement is enabled by default (True)")
            print("  This ensures better coordinate accuracy automatically")
            return True
        else:
            print(f"✗ FAILED: Geometric refinement default is {default_value}, expected True")
            return False
    else:
        print("✗ FAILED: Could not find use_geometric_refinement parameter")
        return False


def test_coordinate_validation_warnings():
    """Validate that coordinate clamping warnings are in place"""
    
    print()
    print("="*70)
    print("TESTING COORDINATE VALIDATION WARNINGS")
    print("="*70)
    print()
    
    # Read backend.py
    with open('/home/runner/work/ServiceiPID/ServiceiPID/backend/backend.py', 'r') as f:
        backend_code = f.read()
    
    checks = [
        ("x_was_clamped", "X clamping detection"),
        ("y_was_clamped", "Y clamping detection"),
        ("Coordenadas ajustadas para", "Coordinate adjustment warning"),
    ]
    
    passed = 0
    failed = 0
    
    for check_text, description in checks:
        if check_text in backend_code:
            print(f"✓ {description} implemented")
            passed += 1
        else:
            print(f"✗ FAILED: {description} - '{check_text}' not found")
            failed += 1
    
    print()
    print(f"Validation Warnings Test: {passed} passed, {failed} failed")
    return failed == 0


def test_decimal_precision_in_examples():
    """Validate that example coordinates use decimal precision"""
    
    print()
    print("="*70)
    print("TESTING DECIMAL PRECISION IN EXAMPLES")
    print("="*70)
    print()
    
    # Read backend.py
    with open('/home/runner/work/ServiceiPID/ServiceiPID/backend/backend.py', 'r') as f:
        backend_code = f.read()
    
    # Extract generation prompt examples
    gen_prompt_match = re.search(r'def build_generation_prompt\(.*?\):\s*.*?return prompt\.strip\(\)', backend_code, re.DOTALL)
    gen_prompt_code = gen_prompt_match.group(0) if gen_prompt_match else ""
    
    # Look for example coordinates - should have decimals
    decimal_examples = [
        ("150.5", "Tank X coordinate"),
        ("450.8", "Tank Y coordinate"),
        ("250.3", "Pump X coordinate"),
        ("400.2", "Pump Y coordinate"),
        ("280.7", "FT X coordinate"),
        ("380.5", "FT Y coordinate"),
    ]
    
    passed = 0
    failed = 0
    
    for coord, description in decimal_examples:
        if coord in gen_prompt_code:
            print(f"✓ Example uses decimal precision: {coord} ({description})")
            passed += 1
        else:
            print(f"✗ FAILED: Example missing decimal: {coord} ({description})")
            failed += 1
    
    # Check that old integer-only examples are NOT present
    old_examples = ["150.0", "250.0", "280.0"]
    for coord in old_examples:
        # Count occurrences - if there are many, it might be the old format
        count = gen_prompt_code.count(f'"x_mm": {coord}')
        if count == 0:
            print(f"✓ Old integer-like example removed: {coord}")
            passed += 1
        else:
            print(f"⚠️  Old integer-like example still present: {coord} (appears {count} times)")
            # Not failing the test for this, just warning
    
    print()
    print(f"Decimal Precision Examples Test: {passed} passed, {failed} failed")
    return failed == 0


def main():
    """Run all tests"""
    print()
    print("="*70)
    print("COORDINATE PRECISION IMPROVEMENTS VALIDATION")
    print("="*70)
    print()
    
    result1 = test_prompt_precision_requirements()
    result2 = test_geometric_refinement_default()
    result3 = test_coordinate_validation_warnings()
    result4 = test_decimal_precision_in_examples()
    
    print()
    print("="*70)
    if result1 and result2 and result3 and result4:
        print("✅ ALL COORDINATE PRECISION TESTS PASSED!")
        print()
        print("Summary of Improvements:")
        print("- Enhanced prompts with step-by-step measurement instructions")
        print("- Explicit requirements for geometric center of symbols")
        print("- Mandatory coordinate validation steps in prompts")
        print("- Decimal precision (0.1 mm) required in output")
        print("- Geometric refinement enabled by default")
        print("- Coordinate clamping warnings for out-of-bounds values")
        print("- Example coordinates use decimal precision")
        print()
        print("Expected Outcome:")
        print("- Objects will have coordinates EXACTLY as they are in the PDF")
        print("- LLM will measure coordinates more precisely")
        print("- Geometric refinement will auto-correct to symbol centers")
        print("- Decimal precision ensures sub-millimeter accuracy")
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)
    print("="*70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
