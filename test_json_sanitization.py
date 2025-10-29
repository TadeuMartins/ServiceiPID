#!/usr/bin/env python3
"""
Test script to verify JSON sanitization fixes for NaN/Infinity values
"""

import sys
import os
import math
import numpy as np

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend import sanitize_for_json
from system_matcher import cosine_similarity


def test_sanitize_for_json():
    """Test that sanitize_for_json properly handles NaN and Infinity values"""
    print("Testing sanitize_for_json...\n")
    
    # Test cases with problematic float values
    test_cases = [
        {
            "name": "Simple dict with NaN",
            "input": {"value": float('nan'), "name": "test"},
            "expected_value": 0.0
        },
        {
            "name": "Simple dict with Infinity",
            "input": {"value": float('inf'), "name": "test"},
            "expected_value": 0.0
        },
        {
            "name": "Nested dict with NaN",
            "input": {"nested": {"value": float('nan')}},
            "expected_nested_value": 0.0
        },
        {
            "name": "List with NaN values",
            "input": [{"value": float('nan')}, {"value": 1.5}],
            "expected_list_values": [0.0, 1.5]
        },
        {
            "name": "Normal values unchanged",
            "input": {"value": 1.5, "name": "test"},
            "expected_value": 1.5
        },
    ]
    
    all_passed = True
    for test_case in test_cases:
        result = sanitize_for_json(test_case["input"])
        
        if "expected_value" in test_case:
            actual = result["value"]
            expected = test_case["expected_value"]
            if actual == expected:
                print(f"✓ {test_case['name']}: PASSED")
            else:
                print(f"✗ {test_case['name']}: FAILED (expected {expected}, got {actual})")
                all_passed = False
        
        elif "expected_nested_value" in test_case:
            actual = result["nested"]["value"]
            expected = test_case["expected_nested_value"]
            if actual == expected:
                print(f"✓ {test_case['name']}: PASSED")
            else:
                print(f"✗ {test_case['name']}: FAILED (expected {expected}, got {actual})")
                all_passed = False
        
        elif "expected_list_values" in test_case:
            actual_values = [item["value"] for item in result]
            expected_values = test_case["expected_list_values"]
            if actual_values == expected_values:
                print(f"✓ {test_case['name']}: PASSED")
            else:
                print(f"✗ {test_case['name']}: FAILED (expected {expected_values}, got {actual_values})")
                all_passed = False
    
    return all_passed


def test_cosine_similarity():
    """Test that cosine_similarity handles edge cases properly"""
    print("\n\nTesting cosine_similarity...\n")
    
    test_cases = [
        {
            "name": "Normal vectors",
            "a": [1.0, 0.0, 0.0],
            "b": [1.0, 0.0, 0.0],
            "expected": 1.0
        },
        {
            "name": "Orthogonal vectors",
            "a": [1.0, 0.0, 0.0],
            "b": [0.0, 1.0, 0.0],
            "expected": 0.0
        },
        {
            "name": "Zero vector (should return 0.0, not NaN)",
            "a": [0.0, 0.0, 0.0],
            "b": [1.0, 0.0, 0.0],
            "expected": 0.0
        },
        {
            "name": "Both zero vectors",
            "a": [0.0, 0.0, 0.0],
            "b": [0.0, 0.0, 0.0],
            "expected": 0.0
        },
    ]
    
    all_passed = True
    for test_case in test_cases:
        result = cosine_similarity(test_case["a"], test_case["b"])
        expected = test_case["expected"]
        
        # Check that result is finite
        if not math.isfinite(result):
            print(f"✗ {test_case['name']}: FAILED (result is not finite: {result})")
            all_passed = False
        elif abs(result - expected) < 1e-6:
            print(f"✓ {test_case['name']}: PASSED (result: {result})")
        else:
            print(f"✗ {test_case['name']}: FAILED (expected {expected}, got {result})")
            all_passed = False
    
    return all_passed


def test_json_serialization():
    """Test that sanitized data can be serialized to JSON"""
    print("\n\nTesting JSON serialization...\n")
    
    import json
    
    # Create data with NaN/Infinity values
    problematic_data = {
        "items": [
            {"name": "A", "value": float('nan')},
            {"name": "B", "value": float('inf')},
            {"name": "C", "value": 1.5}
        ]
    }
    
    # Sanitize and try to serialize
    try:
        sanitized = sanitize_for_json(problematic_data)
        json_str = json.dumps(sanitized)
        print(f"✓ JSON serialization: PASSED")
        print(f"  Serialized: {json_str[:100]}...")
        return True
    except Exception as e:
        print(f"✗ JSON serialization: FAILED")
        print(f"  Error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("JSON Sanitization and NaN/Infinity Handling Tests")
    print("=" * 60 + "\n")
    
    results = []
    results.append(("sanitize_for_json", test_sanitize_for_json()))
    results.append(("cosine_similarity", test_cosine_similarity()))
    results.append(("JSON serialization", test_json_serialization()))
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    all_passed = all(passed for _, passed in results)
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name}: {status}")
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All tests PASSED!")
        sys.exit(0)
    else:
        print("\n✗ Some tests FAILED!")
        sys.exit(1)
