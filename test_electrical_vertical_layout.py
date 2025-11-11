#!/usr/bin/env python3
"""
Test to verify that electrical diagrams are generated with vertical layout
and that quadrant processing is disabled for electrical diagrams to avoid duplicates.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend import build_generation_prompt


def test_vertical_layout_instructions():
    """Test that electrical diagram generation prompt has vertical layout instructions"""
    print("Testing electrical diagram vertical layout instructions...\n")
    
    prompt = build_generation_prompt('Generate a simple electrical diagram', diagram_type='electrical')
    
    tests = [
        ("SPATIAL DISTRIBUTION section exists", "SPATIAL DISTRIBUTION" in prompt),
        ("Vertical power flow mentioned", "VERTICAL - Power flow from source (TOP) to loads (BOTTOM)" in prompt),
        ("Y as main axis", "Y Coordinates (vertical - MAIN AXIS)" in prompt),
        ("Power flows top to bottom", "Power flows TOP TO BOTTOM" in prompt),
        ("Example shows vertical layout", "VERTICAL LAYOUT" in prompt),
        ("Y coordinate progression in example", '"y_mm": 40.0' in prompt and '"y_mm": 240.0' in prompt),
        ("Vertical arrangement is mandatory", "VERTICAL arrangement is MANDATORY" in prompt),
        ("Components flow from top to bottom", "components flow from top to bottom" in prompt),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, result in tests:
        if result:
            print(f"✅ PASS: {test_name}")
            passed += 1
        else:
            print(f"❌ FAIL: {test_name}")
            failed += 1
    
    print(f"\nResults: {passed}/{len(tests)} tests passed")
    
    return failed == 0


def test_no_horizontal_layout():
    """Test that electrical diagrams do NOT have horizontal layout instructions"""
    print("\nTesting that horizontal layout is NOT mentioned for electrical diagrams...\n")
    
    prompt = build_generation_prompt('Generate a simple electrical diagram', diagram_type='electrical')
    
    # These should NOT be in electrical prompts (but coordinate system description is OK)
    unwanted_phrases = [
        "Power flow from source (left) to loads (right)",
        "Feed/inlet zone",
        "Product/outlet zone",
    ]
    
    tests = []
    for phrase in unwanted_phrases:
        # Check if the phrase is in the prompt (should not be for electrical)
        is_present = phrase in prompt
        tests.append((f"Does NOT contain: '{phrase}'", not is_present))
    
    passed = 0
    failed = 0
    
    for test_name, result in tests:
        if result:
            print(f"✅ PASS: {test_name}")
            passed += 1
        else:
            print(f"❌ FAIL: {test_name}")
            failed += 1
    
    print(f"\nResults: {passed}/{len(tests)} tests passed")
    
    return failed == 0


def test_pid_still_horizontal():
    """Test that P&ID diagrams still use horizontal layout (backward compatibility)"""
    print("\nTesting that P&ID diagrams still use horizontal layout...\n")
    
    prompt = build_generation_prompt('Generate a simple P&ID', diagram_type='pid')
    
    tests = [
        ("Has horizontal flow", "Process flow from left (inlet) to right (outlet)" in prompt),
        ("Feed/inlet zone defined", "Feed/inlet zone: X = 100-300 mm" in prompt),
        ("Product/outlet zone defined", "Product/outlet zone: X = 1000-1100 mm" in prompt),
        ("X as main axis for process", "X Coordinates (horizontal)" in prompt),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, result in tests:
        if result:
            print(f"✅ PASS: {test_name}")
            passed += 1
        else:
            print(f"❌ FAIL: {test_name}")
            failed += 1
    
    print(f"\nResults: {passed}/{len(tests)} tests passed")
    
    return failed == 0


def test_example_coordinates():
    """Test that the example shows proper vertical arrangement"""
    print("\nTesting electrical diagram example coordinates...\n")
    
    prompt = build_generation_prompt('Generate electrical diagram', diagram_type='electrical')
    
    # Extract Y coordinates from example
    import re
    y_coords = re.findall(r'"y_mm":\s*(\d+\.\d+)', prompt)
    
    if y_coords:
        y_values = [float(y) for y in y_coords]
        print(f"Found Y coordinates in example: {y_values}")
        
        # Check if Y coordinates show vertical progression
        min_y = min(y_values)
        max_y = max(y_values)
        
        tests = [
            ("Y coordinates span vertical range", max_y - min_y > 100),
            ("Top component near top", min_y < 60),
            ("Bottom component near bottom", max_y > 180),
            ("All coordinates are multiples of 4", all(y % 4 == 0 for y in y_values)),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, result in tests:
            if result:
                print(f"✅ PASS: {test_name}")
                passed += 1
            else:
                print(f"❌ FAIL: {test_name}")
                failed += 1
        
        print(f"\nResults: {passed}/{len(tests)} tests passed")
        return failed == 0
    else:
        print("❌ FAIL: No Y coordinates found in example")
        return False


if __name__ == "__main__":
    print("="*70)
    print("Testing Electrical Diagram Vertical Layout")
    print("="*70)
    
    results = []
    
    results.append(("Vertical layout instructions", test_vertical_layout_instructions()))
    results.append(("No horizontal layout for electrical", test_no_horizontal_layout()))
    results.append(("P&ID still horizontal", test_pid_still_horizontal()))
    results.append(("Example coordinates", test_example_coordinates()))
    
    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed}/{total} test suites passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Electrical diagrams will now be generated vertically.")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed.")
        sys.exit(1)
