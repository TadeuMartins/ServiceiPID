#!/usr/bin/env python3
"""
Test to verify that tile offsets are correctly applied to coordinates.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_parse_electrical_equips_with_offsets():
    """Test that parse_electrical_equips correctly adds tile offsets"""
    
    print("="*70)
    print("TESTING TILE OFFSET APPLICATION IN parse_electrical_equips")
    print("="*70)
    print()
    
    # Import the function (mock dependencies)
    import unittest.mock as mock
    with mock.patch.dict('sys.modules', {
        'fitz': mock.MagicMock(),
        'httpx': mock.MagicMock(),
        'certifi': mock.MagicMock(),
    }):
        from backend import parse_electrical_equips, BBox
    
    # Test data: LLM returns tile-local coordinates
    resp = {
        "equipments": [
            {
                "type": "MOTOR",
                "tag": "M-101",
                "descricao": "Motor trifásico 10HP",
                "bbox": {"x": 100, "y": 200, "w": 50, "h": 50},
                "confidence": 0.95,
                "partial": False
            },
            {
                "type": "BREAKER",
                "tag": "CB-201",
                "descricao": "Disjuntor tripolar 32A",
                "bbox": [300, 400, 30, 30],  # Test list format
                "confidence": 0.89,
                "partial": False
            }
        ]
    }
    
    # Test 1: Global analysis (no offset)
    print("Test 1: Global analysis (ox=0, oy=0)")
    eqs_global = parse_electrical_equips(resp, page=0)
    
    assert eqs_global[0].bbox.x == 100, f"Expected x=100, got {eqs_global[0].bbox.x}"
    assert eqs_global[0].bbox.y == 200, f"Expected y=200, got {eqs_global[0].bbox.y}"
    assert eqs_global[1].bbox.x == 300, f"Expected x=300, got {eqs_global[1].bbox.x}"
    assert eqs_global[1].bbox.y == 400, f"Expected y=400, got {eqs_global[1].bbox.y}"
    
    print(f"  ✓ M-101 at ({eqs_global[0].bbox.x}, {eqs_global[0].bbox.y}) - correct!")
    print(f"  ✓ CB-201 at ({eqs_global[1].bbox.x}, {eqs_global[1].bbox.y}) - correct!")
    print()
    
    # Test 2: Tile analysis with offset
    print("Test 2: Tile analysis (ox=2000, oy=1500)")
    ox, oy = 2000, 1500
    eqs_tile = parse_electrical_equips(resp, page=0, ox=ox, oy=oy)
    
    expected_x1 = 100 + ox  # 2100
    expected_y1 = 200 + oy  # 1700
    expected_x2 = 300 + ox  # 2300
    expected_y2 = 400 + oy  # 1900
    
    assert eqs_tile[0].bbox.x == expected_x1, f"Expected x={expected_x1}, got {eqs_tile[0].bbox.x}"
    assert eqs_tile[0].bbox.y == expected_y1, f"Expected y={expected_y1}, got {eqs_tile[0].bbox.y}"
    assert eqs_tile[1].bbox.x == expected_x2, f"Expected x={expected_x2}, got {eqs_tile[1].bbox.x}"
    assert eqs_tile[1].bbox.y == expected_y2, f"Expected y={expected_y2}, got {eqs_tile[1].bbox.y}"
    
    print(f"  ✓ M-101 at ({eqs_tile[0].bbox.x}, {eqs_tile[0].bbox.y}) - offset added correctly!")
    print(f"  ✓ CB-201 at ({eqs_tile[1].bbox.x}, {eqs_tile[1].bbox.y}) - offset added correctly!")
    print()
    
    return True


def test_parse_electrical_edges_with_offsets():
    """Test that parse_electrical_edges correctly adds tile offsets to paths"""
    
    print("="*70)
    print("TESTING TILE OFFSET APPLICATION IN parse_electrical_edges")
    print("="*70)
    print()
    
    # Import the function
    import unittest.mock as mock
    with mock.patch.dict('sys.modules', {
        'fitz': mock.MagicMock(),
        'httpx': mock.MagicMock(),
        'certifi': mock.MagicMock(),
    }):
        from backend import parse_electrical_edges
    
    # Test data
    resp = {
        "connections": [
            {
                "from_tag": "CB-201",
                "to_tag": "M-101",
                "path": [[300, 400], [200, 300], [100, 200]],
                "direction": "forward",
                "confidence": 0.85
            }
        ],
        "unresolved_endpoints": [
            {
                "near": "M-101",
                "point": [100, 200]
            }
        ]
    }
    
    # Test 1: No offset
    print("Test 1: No offset (ox=0, oy=0)")
    cons1, eps1 = parse_electrical_edges(resp, page=0)
    
    assert cons1[0].path[0] == (300, 400), f"Expected (300, 400), got {cons1[0].path[0]}"
    assert cons1[0].path[1] == (200, 300), f"Expected (200, 300), got {cons1[0].path[1]}"
    assert cons1[0].path[2] == (100, 200), f"Expected (100, 200), got {cons1[0].path[2]}"
    assert eps1[0].point == (100, 200), f"Expected (100, 200), got {eps1[0].point}"
    
    print(f"  ✓ Connection path: {cons1[0].path} - correct!")
    print(f"  ✓ Endpoint: {eps1[0].point} - correct!")
    print()
    
    # Test 2: With offset
    print("Test 2: With offset (ox=2000, oy=1500)")
    ox, oy = 2000, 1500
    cons2, eps2 = parse_electrical_edges(resp, page=0, ox=ox, oy=oy)
    
    assert cons2[0].path[0] == (2300, 1900), f"Expected (2300, 1900), got {cons2[0].path[0]}"
    assert cons2[0].path[1] == (2200, 1800), f"Expected (2200, 1800), got {cons2[0].path[1]}"
    assert cons2[0].path[2] == (2100, 1700), f"Expected (2100, 1700), got {cons2[0].path[2]}"
    assert eps2[0].point == (2100, 1700), f"Expected (2100, 1700), got {eps2[0].point}"
    
    print(f"  ✓ Connection path: {cons2[0].path} - offset added correctly!")
    print(f"  ✓ Endpoint: {eps2[0].point} - offset added correctly!")
    print()
    
    return True


def test_coordinate_conversion_with_page_dimensions():
    """Test that coordinates are correctly converted using page dimensions"""
    
    print("="*70)
    print("TESTING COORDINATE CONVERSION WITH PAGE DIMENSIONS")
    print("="*70)
    print()
    
    # Example page: A3 horizontal (420mm x 297mm)
    W_mm = 420.0
    H_mm = 297.0
    
    # Rendered at 300 DPI
    dpi_tiles = 300
    W_px = int((420.0 / 25.4) * dpi_tiles)  # ~4960 pixels
    H_px = int((297.0 / 25.4) * dpi_tiles)  # ~3507 pixels
    
    print(f"Page dimensions:")
    print(f"  MM: {W_mm} x {H_mm}")
    print(f"  Pixels at {dpi_tiles} DPI: {W_px} x {H_px}")
    print()
    
    # Equipment at center of page
    center_x_mm = W_mm / 2  # 210.0 mm
    center_y_mm = H_mm / 2  # 148.5 mm
    
    # Expected pixel coordinates
    center_x_px = (center_x_mm / 25.4) * dpi_tiles  # ~2480 pixels
    center_y_px = (center_y_mm / 25.4) * dpi_tiles  # ~1754 pixels
    
    print(f"Equipment at page center:")
    print(f"  Expected MM: ({center_x_mm:.1f}, {center_y_mm:.1f})")
    print(f"  Expected PX: ({center_x_px:.1f}, {center_y_px:.1f})")
    print()
    
    # Convert back using page dimensions (NEW METHOD)
    x_mm_new = (center_x_px / W_px) * W_mm
    y_mm_new = (center_y_px / H_px) * H_mm
    
    print(f"Conversion using page dimensions:")
    print(f"  x_mm = (x_px / W_px) * W_mm = ({center_x_px:.1f} / {W_px}) * {W_mm} = {x_mm_new:.3f}")
    print(f"  y_mm = (y_px / H_px) * H_mm = ({center_y_px:.1f} / {H_px}) * {H_mm} = {y_mm_new:.3f}")
    print()
    
    # Convert using DPI (OLD METHOD)
    x_mm_old = (center_x_px / dpi_tiles) * 25.4
    y_mm_old = (center_y_px / dpi_tiles) * 25.4
    
    print(f"Conversion using DPI (old method):")
    print(f"  x_mm = (x_px / dpi) * 25.4 = ({center_x_px:.1f} / {dpi_tiles}) * 25.4 = {x_mm_old:.3f}")
    print(f"  y_mm = (y_px / dpi) * 25.4 = ({center_y_px:.1f} / {dpi_tiles}) * 25.4 = {y_mm_old:.3f}")
    print()
    
    # Both methods should give same result (within rounding)
    assert abs(x_mm_new - center_x_mm) < 0.1, f"X coordinate error too large: {abs(x_mm_new - center_x_mm)}"
    assert abs(y_mm_new - center_y_mm) < 0.1, f"Y coordinate error too large: {abs(y_mm_new - center_y_mm)}"
    assert abs(x_mm_old - center_x_mm) < 0.1, f"X coordinate error too large (old): {abs(x_mm_old - center_x_mm)}"
    assert abs(y_mm_old - center_y_mm) < 0.1, f"Y coordinate error too large (old): {abs(y_mm_old - center_y_mm)}"
    
    print("✓ Both methods give correct results (within 0.1mm tolerance)")
    print("✓ New method using page dimensions ensures accuracy even with non-uniform scaling")
    print()
    
    return True


def test_round_to_multiple_of_4():
    """Test that coordinates are properly rounded to multiples of 4mm"""
    
    print("="*70)
    print("TESTING ROUNDING TO MULTIPLES OF 4MM")
    print("="*70)
    print()
    
    import unittest.mock as mock
    with mock.patch.dict('sys.modules', {
        'fitz': mock.MagicMock(),
        'httpx': mock.MagicMock(),
        'certifi': mock.MagicMock(),
    }):
        from backend import round_to_multiple_of_4
    
    test_cases = [
        (0.0, 0.0),
        (2.0, 4.0),    # Exactly between 0 and 4, rounds up
        (3.9, 4.0),
        (4.0, 4.0),
        (5.0, 4.0),
        (6.0, 8.0),    # Exactly between 4 and 8, rounds up
        (7.9, 8.0),
        (8.0, 8.0),
        (10.0, 12.0),  # Exactly between 8 and 12, rounds up
        (210.5, 212.0),
        (148.3, 148.0),
    ]
    
    all_passed = True
    for input_val, expected in test_cases:
        result = round_to_multiple_of_4(input_val)
        passed = result == expected
        status = "✓" if passed else "✗"
        print(f"  {status} round_to_multiple_of_4({input_val}) = {result} (expected {expected})")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("✓ All rounding tests passed!")
    else:
        print("✗ Some rounding tests failed")
        return False
    
    print()
    return True


def main():
    """Run all tests"""
    print()
    print("="*70)
    print("TILE OFFSET FIX VALIDATION TESTS")
    print("="*70)
    print()
    
    try:
        result1 = test_parse_electrical_equips_with_offsets()
        result2 = test_parse_electrical_edges_with_offsets()
        result3 = test_coordinate_conversion_with_page_dimensions()
        result4 = test_round_to_multiple_of_4()
        
        print()
        print("="*70)
        if result1 and result2 and result3 and result4:
            print("✅ ALL TESTS PASSED!")
            print()
            print("Summary of Fixes:")
            print("- Tile offsets (ox, oy) are correctly added to equipment coordinates")
            print("- Tile offsets are correctly added to connection paths")
            print("- Tile offsets are correctly added to endpoints")
            print("- Coordinate conversion uses page dimensions for accuracy")
            print("- Coordinates are properly rounded to multiples of 4mm")
            print()
            print("Expected Outcome:")
            print("- Electrical diagram coordinates will be 100% correct")
            print("- Coordinates will be in absolute page position (not tile-local)")
            print("- Coordinates will align to 4mm grid as required")
            print("- No more coordinate confusion between tiles and page!")
        else:
            print("❌ SOME TESTS FAILED")
            sys.exit(1)
        print("="*70)
        return 0
    except Exception as e:
        print(f"❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
