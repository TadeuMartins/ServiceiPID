#!/usr/bin/env python3
"""
Test script to verify the JSON output requirements in the generation prompt.
This test ensures that the prompt properly emphasizes JSON-only output for both
P&ID and electrical diagrams.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend import build_generation_prompt


def test_json_requirement_emphasis():
    """Test that JSON-only output is emphasized in the prompt"""
    print("Testing JSON Output Requirement Emphasis...\n")
    
    passed = 0
    failed = 0
    
    # Test both diagram types
    for diagram_type in ["pid", "electrical"]:
        print(f"Testing {diagram_type.upper()} diagram type:")
        prompt = build_generation_prompt(
            "Test process description",
            width_mm=1189.0,
            height_mm=841.0,
            diagram_type=diagram_type
        )
        
        # Check for critical JSON-only output requirements
        checks = [
            ("CRITICAL OUTPUT REQUIREMENT", "Critical output requirement section"),
            ("You MUST respond with ONLY a valid JSON array", "JSON-only requirement statement"),
            ("NO additional text, explanations, markdown, or descriptions", "No additional text warning"),
            ("Start your response directly with '['", "Start with bracket instruction"),
            ("end with ']'", "End with bracket instruction"),
            ("OUTPUT FORMAT - CRITICAL", "Critical output format section"),
            ("YOU MUST RESPOND WITH ONLY A JSON ARRAY", "Uppercase JSON-only emphasis"),
            ("NO MARKDOWN, NO EXPLANATIONS, NO ADDITIONAL TEXT", "Uppercase no-extra-text warning"),
            ("CRITICAL REMINDERS", "Critical reminders section"),
            ("Return ONLY the JSON array shown above, no other text", "Return only JSON reminder"),
            ("NO explanations, NO markdown formatting (no ```json)", "No markdown formatting warning"),
            ("Start directly with '['", "Start directly with bracket reminder"),
        ]
        
        type_passed = 0
        type_failed = 0
        
        for check_text, description in checks:
            if check_text in prompt:
                print(f"  ✓ {description}")
                type_passed += 1
            else:
                print(f"  ✗ FAILED: {description} - '{check_text}' not found")
                type_failed += 1
        
        print(f"  {diagram_type.upper()}: {type_passed} passed, {type_failed} failed\n")
        passed += type_passed
        failed += type_failed
    
    return failed == 0, passed, failed


def test_electrical_diagram_example():
    """Test that electrical diagrams have proper examples"""
    print("Testing Electrical Diagram Examples...\n")
    
    prompt = build_generation_prompt(
        "Star-delta starter",
        width_mm=1189.0,
        height_mm=841.0,
        diagram_type="electrical"
    )
    
    # Check for electrical-specific elements
    checks = [
        ("EXAMPLE OUTPUT FOR ELECTRICAL DIAGRAM", "Electrical diagram example header"),
        ("Star-Delta Starter", "Star-delta starter reference"),
        ('"tag": "CB-101"', "Circuit breaker example"),
        ('"tag": "C-101"', "Contactor example"),
        ('"tag": "M-101"', "Motor example"),
        ('"descricao": "Main Circuit Breaker"', "Circuit breaker description"),
        ('"descricao": "Star Contactor"', "Star contactor description"),
        ('"descricao": "Delta Contactor"', "Delta contactor description"),
        ('"descricao": "Three-Phase Motor"', "Motor description"),
        ('"descricao": "Overload Relay"', "Relay description"),
        ("electrical diagram concepts", "Electrical diagram concepts reference"),
        ("protection devices, controls", "Protection devices reference"),
        ("Use standard electrical nomenclature", "Electrical nomenclature instruction"),
    ]
    
    passed = 0
    failed = 0
    
    for check_text, description in checks:
        if check_text in prompt:
            print(f"  ✓ {description}")
            passed += 1
        else:
            print(f"  ✗ FAILED: {description} - '{check_text}' not found")
            failed += 1
    
    print(f"\nElectrical Diagram Examples: {passed} passed, {failed} failed\n")
    return failed == 0, passed, failed


def test_pid_diagram_example():
    """Test that P&ID diagrams have proper examples"""
    print("Testing P&ID Diagram Examples...\n")
    
    prompt = build_generation_prompt(
        "Water treatment process",
        width_mm=1189.0,
        height_mm=841.0,
        diagram_type="pid"
    )
    
    # Check for P&ID-specific elements
    checks = [
        ("EXAMPLE OUTPUT FOR P&ID", "P&ID example header"),
        ('"tag": "T-101"', "Tank example"),
        ('"tag": "P-101"', "Pump example"),
        ('"tag": "FT-101"', "Flow transmitter example"),
        ('"descricao": "Feed Tank"', "Tank description"),
        ('"descricao": "Centrifugal Feed Pump"', "Pump description"),
        ("P&ID concepts and ISA standards", "P&ID concepts reference"),
        ("valves, controls", "Valves and controls reference"),
        ("Strictly follow ISA S5.1 standards", "ISA standards instruction"),
    ]
    
    passed = 0
    failed = 0
    
    for check_text, description in checks:
        if check_text in prompt:
            print(f"  ✓ {description}")
            passed += 1
        else:
            print(f"  ✗ FAILED: {description} - '{check_text}' not found")
            failed += 1
    
    print(f"\nP&ID Diagram Examples: {passed} passed, {failed} failed\n")
    return failed == 0, passed, failed


def test_no_pid_examples_in_electrical():
    """Test that electrical diagrams don't show P&ID examples as primary"""
    print("Testing Separation of Examples...\n")
    
    electrical_prompt = build_generation_prompt(
        "Star-delta starter",
        width_mm=1189.0,
        height_mm=841.0,
        diagram_type="electrical"
    )
    
    pid_prompt = build_generation_prompt(
        "Water treatment",
        width_mm=1189.0,
        height_mm=841.0,
        diagram_type="pid"
    )
    
    # Electrical prompt should have electrical examples, not P&ID
    has_electrical_example = "EXAMPLE OUTPUT FOR ELECTRICAL DIAGRAM" in electrical_prompt
    has_pid_example_in_electrical = "EXAMPLE OUTPUT FOR P&ID" in electrical_prompt
    
    # P&ID prompt should have P&ID examples, not electrical
    has_pid_example = "EXAMPLE OUTPUT FOR P&ID" in pid_prompt
    has_electrical_example_in_pid = "EXAMPLE OUTPUT FOR ELECTRICAL DIAGRAM" in pid_prompt
    
    print(f"  Electrical prompt has electrical example: {has_electrical_example}")
    print(f"  Electrical prompt has P&ID example: {has_pid_example_in_electrical}")
    print(f"  P&ID prompt has P&ID example: {has_pid_example}")
    print(f"  P&ID prompt has electrical example: {has_electrical_example_in_pid}")
    
    success = (has_electrical_example and not has_pid_example_in_electrical and 
               has_pid_example and not has_electrical_example_in_pid)
    
    if success:
        print("\n✓ Examples are properly separated by diagram type")
        return True, 4, 0
    else:
        print("\n✗ FAILED: Examples are not properly separated")
        return False, 0, 4


if __name__ == "__main__":
    print("=" * 60)
    print("TESTING JSON OUTPUT REQUIREMENT IN GENERATION PROMPT")
    print("=" * 60 + "\n")
    
    result1, passed1, failed1 = test_json_requirement_emphasis()
    result2, passed2, failed2 = test_electrical_diagram_example()
    result3, passed3, failed3 = test_pid_diagram_example()
    result4, passed4, failed4 = test_no_pid_examples_in_electrical()
    
    total_passed = passed1 + passed2 + passed3 + passed4
    total_failed = failed1 + failed2 + failed3 + failed4
    
    print("=" * 60)
    if result1 and result2 and result3 and result4:
        print("✅ ALL TESTS PASSED!")
        print(f"\nTotal: {total_passed} checks passed, {total_failed} checks failed")
        print("\nSummary:")
        print("- JSON-only output requirement is properly emphasized")
        print("- Electrical diagrams have star-delta starter example")
        print("- P&ID diagrams have process equipment example")
        print("- Examples are diagram-type specific")
        print("- Multiple reminders throughout the prompt")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        print(f"\nTotal: {total_passed} checks passed, {total_failed} checks failed")
        sys.exit(1)
    print("=" * 60)
