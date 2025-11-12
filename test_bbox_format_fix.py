#!/usr/bin/env python3
"""
Test the bbox format fix for parse_electrical_equips.
Verifies that the function can handle both list and dict bbox formats.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend import parse_electrical_equips, BBox


def test_bbox_as_dict():
    """Test that dict bbox format works correctly"""
    print("\n=== Testing bbox as dict format ===")
    
    resp = {
        "equipments": [
            {
                "type": "MOTOR",
                "tag": "M-101",
                "bbox": {"x": 100, "y": 200, "w": 50, "h": 60},
                "confidence": 0.95,
                "partial": False
            }
        ]
    }
    
    result = parse_electrical_equips(resp, 0)
    
    assert len(result) == 1, f"Expected 1 equipment, got {len(result)}"
    eq = result[0]
    assert eq.type == "MOTOR", f"Expected type MOTOR, got {eq.type}"
    assert eq.tag == "M-101", f"Expected tag M-101, got {eq.tag}"
    assert eq.bbox.x == 100, f"Expected x=100, got {eq.bbox.x}"
    assert eq.bbox.y == 200, f"Expected y=200, got {eq.bbox.y}"
    assert eq.bbox.w == 50, f"Expected w=50, got {eq.bbox.w}"
    assert eq.bbox.h == 60, f"Expected h=60, got {eq.bbox.h}"
    assert eq.page == 1, f"Expected page=1, got {eq.page}"
    assert eq.confidence == 0.95, f"Expected confidence=0.95, got {eq.confidence}"
    assert eq.partial == False, f"Expected partial=False, got {eq.partial}"
    
    print("✅ Dict bbox format works correctly")


def test_bbox_as_list():
    """Test that list bbox format works correctly (this was the bug)"""
    print("\n=== Testing bbox as list format ===")
    
    resp = {
        "equipments": [
            {
                "type": "BREAKER",
                "tag": "CB-201",
                "bbox": [150, 250, 40, 45],
                "confidence": 0.88,
                "partial": True
            }
        ]
    }
    
    result = parse_electrical_equips(resp, 1)
    
    assert len(result) == 1, f"Expected 1 equipment, got {len(result)}"
    eq = result[0]
    assert eq.type == "BREAKER", f"Expected type BREAKER, got {eq.type}"
    assert eq.tag == "CB-201", f"Expected tag CB-201, got {eq.tag}"
    assert eq.bbox.x == 150, f"Expected x=150, got {eq.bbox.x}"
    assert eq.bbox.y == 250, f"Expected y=250, got {eq.bbox.y}"
    assert eq.bbox.w == 40, f"Expected w=40, got {eq.bbox.w}"
    assert eq.bbox.h == 45, f"Expected h=45, got {eq.bbox.h}"
    assert eq.page == 2, f"Expected page=2, got {eq.page}"
    assert eq.confidence == 0.88, f"Expected confidence=0.88, got {eq.confidence}"
    assert eq.partial == True, f"Expected partial=True, got {eq.partial}"
    
    print("✅ List bbox format works correctly")


def test_bbox_incomplete_list():
    """Test that incomplete list bbox format is handled gracefully"""
    print("\n=== Testing incomplete list bbox format ===")
    
    resp = {
        "equipments": [
            {
                "type": "RELAY",
                "tag": "R-301",
                "bbox": [100, 200],  # incomplete: missing w and h
                "confidence": 0.75,
                "partial": False
            }
        ]
    }
    
    result = parse_electrical_equips(resp, 2)
    
    assert len(result) == 1, f"Expected 1 equipment, got {len(result)}"
    eq = result[0]
    assert eq.type == "RELAY", f"Expected type RELAY, got {eq.type}"
    assert eq.bbox.x == 100, f"Expected x=100, got {eq.bbox.x}"
    assert eq.bbox.y == 200, f"Expected y=200, got {eq.bbox.y}"
    assert eq.bbox.w == 0, f"Expected w=0 (default), got {eq.bbox.w}"
    assert eq.bbox.h == 0, f"Expected h=0 (default), got {eq.bbox.h}"
    
    print("✅ Incomplete list bbox format handled gracefully")


def test_bbox_empty_dict():
    """Test that empty dict bbox format is handled gracefully"""
    print("\n=== Testing empty dict bbox format ===")
    
    resp = {
        "equipments": [
            {
                "type": "TERMINAL",
                "tag": None,
                "bbox": {},  # empty dict
                "confidence": 0.5,
                "partial": False
            }
        ]
    }
    
    result = parse_electrical_equips(resp, 3)
    
    assert len(result) == 1, f"Expected 1 equipment, got {len(result)}"
    eq = result[0]
    assert eq.type == "TERMINAL", f"Expected type TERMINAL, got {eq.type}"
    assert eq.bbox.x == 0, f"Expected x=0 (default), got {eq.bbox.x}"
    assert eq.bbox.y == 0, f"Expected y=0 (default), got {eq.bbox.y}"
    assert eq.bbox.w == 0, f"Expected w=0 (default), got {eq.bbox.w}"
    assert eq.bbox.h == 0, f"Expected h=0 (default), got {eq.bbox.h}"
    
    print("✅ Empty dict bbox format handled gracefully")


def test_mixed_bbox_formats():
    """Test that mixed bbox formats in the same response work correctly"""
    print("\n=== Testing mixed bbox formats ===")
    
    resp = {
        "equipments": [
            {
                "type": "MOTOR",
                "tag": "M-401",
                "bbox": {"x": 100, "y": 200, "w": 50, "h": 60},
                "confidence": 0.95,
                "partial": False
            },
            {
                "type": "BREAKER",
                "tag": "CB-402",
                "bbox": [150, 250, 40, 45],
                "confidence": 0.88,
                "partial": True
            }
        ]
    }
    
    result = parse_electrical_equips(resp, 4)
    
    assert len(result) == 2, f"Expected 2 equipment, got {len(result)}"
    
    # Verify first equipment (dict format)
    eq1 = result[0]
    assert eq1.type == "MOTOR", f"Expected type MOTOR, got {eq1.type}"
    assert eq1.bbox.x == 100, f"Expected x=100, got {eq1.bbox.x}"
    
    # Verify second equipment (list format)
    eq2 = result[1]
    assert eq2.type == "BREAKER", f"Expected type BREAKER, got {eq2.type}"
    assert eq2.bbox.x == 150, f"Expected x=150, got {eq2.bbox.x}"
    
    print("✅ Mixed bbox formats work correctly")


if __name__ == "__main__":
    try:
        test_bbox_as_dict()
        test_bbox_as_list()
        test_bbox_incomplete_list()
        test_bbox_empty_dict()
        test_mixed_bbox_formats()
        
        print("\n" + "="*50)
        print("✅ All tests passed!")
        print("="*50)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
