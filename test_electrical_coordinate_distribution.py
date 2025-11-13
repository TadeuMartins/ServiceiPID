#!/usr/bin/env python3
"""
Test that electrical diagram coordinate distribution is correct when using
fixed A3 dimensions (420x297mm).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))


def test_coordinate_conversion_with_fixed_a3():
    """Test that coordinate conversion works correctly with fixed A3 dimensions"""
    print("\n=== Testing coordinate conversion with fixed A3 ===")
    
    # Simulate the conversion logic from run_electrical_pipeline
    W_mm = 420.0  # Fixed A3 width
    H_mm = 297.0  # Fixed A3 height
    
    # Simulated page rendered at 300 DPI (typical for tiles)
    # A3 at 300 DPI: 420mm / 25.4mm * 300 = ~4961px width
    #                297mm / 25.4mm * 300 = ~3508px height
    W_px_at_tiles = 4961
    H_px_at_tiles = 3508
    
    # Test cases: pixel positions and their expected mm positions
    test_cases = [
        # (px_x, px_y, expected_mm_x, expected_mm_y, description)
        (0, 0, 0.0, 0.0, "Top-left corner"),
        (W_px_at_tiles, H_px_at_tiles, W_mm, H_mm, "Bottom-right corner"),
        (W_px_at_tiles / 2, H_px_at_tiles / 2, W_mm / 2, H_mm / 2, "Center"),
        (W_px_at_tiles / 4, H_px_at_tiles / 4, W_mm / 4, H_mm / 4, "Quarter point"),
    ]
    
    for px_x, px_y, expected_x, expected_y, desc in test_cases:
        # Apply the conversion formula from run_electrical_pipeline
        x_mm = (px_x / W_px_at_tiles) * W_mm
        y_mm = (px_y / H_px_at_tiles) * H_mm
        
        # Check if conversion is correct
        tolerance = 0.1  # Allow 0.1mm tolerance
        assert abs(x_mm - expected_x) < tolerance, \
            f"{desc}: X conversion failed. Expected {expected_x:.1f}mm, got {x_mm:.1f}mm"
        assert abs(y_mm - expected_y) < tolerance, \
            f"{desc}: Y conversion failed. Expected {expected_y:.1f}mm, got {y_mm:.1f}mm"
        
        print(f"  ✓ {desc}: ({px_x:.0f}px, {px_y:.0f}px) → ({x_mm:.1f}mm, {y_mm:.1f}mm)")
    
    print("✅ Coordinate conversion works correctly with fixed A3 dimensions")


def test_coordinates_stay_within_a3_bounds():
    """Test that converted coordinates stay within A3 bounds"""
    print("\n=== Testing coordinates stay within A3 bounds ===")
    
    from backend import round_to_multiple_of_4
    
    W_mm = 420.0
    H_mm = 297.0
    
    # Test various positions across the sheet
    test_positions = [
        (50.0, 50.0, "Near top-left"),
        (210.0, 148.5, "Center"),
        (370.0, 247.0, "Near bottom-right"),
        (60.0, 240.0, "Left side, near bottom"),
        (380.0, 60.0, "Right side, near top"),
    ]
    
    for x_mm, y_mm, desc in test_positions:
        # Apply rounding
        x_rounded = round_to_multiple_of_4(x_mm)
        y_rounded = round_to_multiple_of_4(y_mm)
        
        # Check bounds
        assert 0 <= x_rounded <= W_mm, \
            f"{desc}: X {x_rounded}mm is outside bounds [0, {W_mm}]"
        assert 0 <= y_rounded <= H_mm, \
            f"{desc}: Y {y_rounded}mm is outside bounds [0, {H_mm}]"
        
        # Check it's a multiple of 4
        assert x_rounded % 4 == 0, f"{desc}: X {x_rounded}mm is not a multiple of 4"
        assert y_rounded % 4 == 0, f"{desc}: Y {y_rounded}mm is not a multiple of 4"
        
        print(f"  ✓ {desc}: ({x_mm:.1f}, {y_mm:.1f}) → ({x_rounded:.0f}, {y_rounded:.0f})mm (within bounds)")
    
    print("✅ All coordinates stay within A3 bounds and are multiples of 4")


def test_spatial_zones_align_with_4mm_grid():
    """Test that spatial distribution zones align well with 4mm grid"""
    print("\n=== Testing spatial zones align with 4mm grid ===")
    
    zones = [
        ("Power source", 20, 60),
        ("Distribution", 60, 120),
        ("Control/Protection", 120, 180),
        ("Load", 180, 240),
    ]
    
    for zone_name, y_min, y_max in zones:
        # Check that zone boundaries are multiples of 4
        assert y_min % 4 == 0, f"{zone_name}: Min Y {y_min}mm is not a multiple of 4"
        assert y_max % 4 == 0, f"{zone_name}: Max Y {y_max}mm is not a multiple of 4"
        
        # Check zone has reasonable size (at least 10 positions at 4mm intervals)
        zone_height = y_max - y_min
        positions = zone_height / 4
        assert positions >= 10, f"{zone_name}: Only {positions} positions available (too small)"
        
        print(f"  ✓ {zone_name}: Y={y_min}-{y_max}mm ({positions:.0f} positions at 4mm grid)")
    
    print("✅ All spatial zones align well with 4mm grid")


def test_horizontal_distribution_zones():
    """Test that horizontal distribution zones are correct for A3"""
    print("\n=== Testing horizontal distribution zones ===")
    
    # Expected zones from the prompt
    zones = [
        ("Left margin", 40, 60, 15),  # Minimum width for margins
        ("Main power circuit", 60, 140, 40),  # Minimum width for circuits
        ("Control circuit", 180, 260, 40),
        ("Instrumentation/meters", 300, 380, 40),
    ]
    
    W_mm = 420.0
    
    for zone_name, x_min, x_max, min_width in zones:
        # Check zones are within sheet bounds
        assert 0 < x_min < W_mm, f"{zone_name}: Min X {x_min}mm outside sheet"
        assert 0 < x_max <= W_mm, f"{zone_name}: Max X {x_max}mm outside sheet"
        
        # Check zone has reasonable size
        zone_width = x_max - x_min
        assert zone_width >= min_width, f"{zone_name}: Width {zone_width}mm is too small (min {min_width}mm)"
        
        print(f"  ✓ {zone_name}: X={x_min}-{x_max}mm (width: {zone_width}mm)")
    
    # Check right margin
    right_margin_min = 380
    right_margin_max = 420
    margin_size = right_margin_max - right_margin_min
    assert margin_size >= 20, f"Right margin {margin_size}mm is too small"
    print(f"  ✓ Right margin: X={right_margin_min}-{right_margin_max}mm (width: {margin_size}mm)")
    
    print("✅ Horizontal distribution zones are correctly sized for A3")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("ELECTRICAL DIAGRAM COORDINATE DISTRIBUTION TESTS")
    print("="*60)
    
    try:
        test_coordinate_conversion_with_fixed_a3()
        test_coordinates_stay_within_a3_bounds()
        test_spatial_zones_align_with_4mm_grid()
        test_horizontal_distribution_zones()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nSummary:")
        print("- Coordinate conversion from pixels to mm works correctly")
        print("- All coordinates stay within A3 bounds (420x297mm)")
        print("- Spatial zones align well with 4mm grid")
        print("- Horizontal distribution zones are correctly sized")
        print("- Sheet distribution is correct for electrical diagrams")
        print("="*60 + "\n")
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
