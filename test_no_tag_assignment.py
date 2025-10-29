#!/usr/bin/env python3
"""
Test script to verify NO-TAG assignment functionality
"""

import sys
from typing import List, Dict, Any


def assign_no_tag_identifiers(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Assign sequential NO-TAG identifiers to equipment without valid tags.
    Equipment with tag "N/A" will be renamed to "NO-TAG1", "NO-TAG2", etc.
    """
    no_tag_counter = 1
    for item in items:
        if item.get("tag") == "N/A":
            item["tag"] = f"NO-TAG{no_tag_counter}"
            no_tag_counter += 1
    return items


def test_assign_no_tag_identifiers():
    """Test that N/A tags are replaced with sequential NO-TAG identifiers"""
    print("Testing assign_no_tag_identifiers...\n")
    
    test_cases = [
        {
            "name": "Single equipment without tag",
            "input": [
                {"tag": "N/A", "descricao": "Bomba"},
            ],
            "expected_tags": ["NO-TAG1"]
        },
        {
            "name": "Multiple equipment without tags",
            "input": [
                {"tag": "N/A", "descricao": "Bomba 1"},
                {"tag": "N/A", "descricao": "Bomba 2"},
                {"tag": "N/A", "descricao": "Válvula"},
            ],
            "expected_tags": ["NO-TAG1", "NO-TAG2", "NO-TAG3"]
        },
        {
            "name": "Mix of tagged and untagged equipment",
            "input": [
                {"tag": "P-101", "descricao": "Bomba Principal"},
                {"tag": "N/A", "descricao": "Bomba Auxiliar"},
                {"tag": "V-201", "descricao": "Válvula"},
                {"tag": "N/A", "descricao": "Tanque"},
                {"tag": "T-301", "descricao": "Torre"},
            ],
            "expected_tags": ["P-101", "NO-TAG1", "V-201", "NO-TAG2", "T-301"]
        },
        {
            "name": "No equipment without tags",
            "input": [
                {"tag": "P-101", "descricao": "Bomba"},
                {"tag": "V-201", "descricao": "Válvula"},
            ],
            "expected_tags": ["P-101", "V-201"]
        },
        {
            "name": "Ten equipment without tags",
            "input": [
                {"tag": "N/A", "descricao": f"Equipment {i}"} 
                for i in range(1, 11)
            ],
            "expected_tags": [f"NO-TAG{i}" for i in range(1, 11)]
        },
    ]
    
    all_passed = True
    for test_case in test_cases:
        result = assign_no_tag_identifiers(test_case["input"])
        actual_tags = [item["tag"] for item in result]
        expected_tags = test_case["expected_tags"]
        
        if actual_tags == expected_tags:
            print(f"✓ {test_case['name']}: PASSED")
        else:
            print(f"✗ {test_case['name']}: FAILED")
            print(f"  Expected: {expected_tags}")
            print(f"  Got:      {actual_tags}")
            all_passed = False
    
    return all_passed


if __name__ == "__main__":
    print("=" * 60)
    print("NO-TAG Assignment Tests")
    print("=" * 60 + "\n")
    
    passed = test_assign_no_tag_identifiers()
    
    print("\n" + "=" * 60)
    if passed:
        print("✓ All tests PASSED!")
        sys.exit(0)
    else:
        print("✗ Some tests FAILED!")
        sys.exit(1)
