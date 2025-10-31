#!/usr/bin/env python3
"""
Test script to verify that ensure_json_list can extract JSON from various formats.
This validates that the parsing logic will work with LLM responses.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend import ensure_json_list

def test_valid_json_array():
    """Test extraction of a valid JSON array"""
    test = """[
  {
    "tag": "CB-101",
    "descricao": "Main Circuit Breaker",
    "x_mm": 150.5,
    "y_mm": 400.0,
    "from": "N/A",
    "to": "C-101"
  },
  {
    "tag": "M-101",
    "descricao": "Motor",
    "x_mm": 500.5,
    "y_mm": 400.0,
    "from": "C-101",
    "to": "N/A"
  }
]"""
    
    result = ensure_json_list(test)
    assert len(result) == 2, f"Expected 2 items, got {len(result)}"
    assert result[0]["tag"] == "CB-101", f"Expected CB-101, got {result[0]['tag']}"
    print("✓ Test 1 passed: Valid JSON array extraction")
    return True


def test_json_with_markdown():
    """Test extraction of JSON with markdown fences"""
    test = """```json
[
  {
    "tag": "CB-101",
    "descricao": "Main Circuit Breaker",
    "x_mm": 150.5,
    "y_mm": 400.0,
    "from": "N/A",
    "to": "C-101"
  }
]
```"""
    
    result = ensure_json_list(test)
    assert len(result) == 1, f"Expected 1 item, got {len(result)}"
    assert result[0]["tag"] == "CB-101", f"Expected CB-101, got {result[0]['tag']}"
    print("✓ Test 2 passed: JSON with markdown fences")
    return True


def test_json_embedded_in_text():
    """Test extraction of JSON embedded in text"""
    test = """Here is the electrical diagram:

[
  {
    "tag": "CB-101",
    "descricao": "Main Circuit Breaker",
    "x_mm": 150.5,
    "y_mm": 400.0,
    "from": "N/A",
    "to": "C-101"
  }
]

That's the complete diagram."""
    
    result = ensure_json_list(test)
    assert len(result) == 1, f"Expected 1 item, got {len(result)}"
    assert result[0]["tag"] == "CB-101", f"Expected CB-101, got {result[0]['tag']}"
    print("✓ Test 3 passed: JSON embedded in text")
    return True


def test_no_json():
    """Test that function returns empty list when no JSON is found"""
    test = """Creating an electrical diagram for a star-delta starter is a classic example for educational purposes. Below, I will describe how the diagram will be structured."""
    
    result = ensure_json_list(test)
    assert len(result) == 0, f"Expected 0 items, got {len(result)}"
    print("✓ Test 4 passed: No JSON returns empty list")
    return True


if __name__ == "__main__":
    print("Testing JSON extraction logic...")
    print()
    
    all_passed = True
    try:
        all_passed = all_passed and test_valid_json_array()
        all_passed = all_passed and test_json_with_markdown()
        all_passed = all_passed and test_json_embedded_in_text()
        all_passed = all_passed and test_no_json()
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        all_passed = False
    
    print()
    if all_passed:
        print("✅ All JSON extraction tests passed!")
        sys.exit(0)
    else:
        print("❌ Some JSON extraction tests failed!")
        sys.exit(1)
