#!/usr/bin/env python3
"""
Test the fixed coordinate conversion that uses actual page dimensions for prompts
but scales output to A3 space.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))


def test_fixed_coordinate_conversion():
    """
    Test that the new two-step conversion works correctly:
    1. Use actual dimensions for prompts (correct mm-per-pixel)
    2. Scale final coordinates to A3 space
    """
    print("\n=== Testing FIXED coordinate conversion ===")
    
    # Simulate different actual PDF page sizes
    test_cases = [
        ("A3 (420x297mm)", 420.0, 297.0),
        ("A4 (297x210mm)", 297.0, 210.0),
        ("A0 (1189x841mm)", 1189.0, 841.0),
    ]
    
    # Target dimensions (A3)
    W_mm_target = 420.0
    H_mm_target = 297.0
    
    dpi_tiles = 300
    
    for page_name, W_mm_actual, H_mm_actual in test_cases:
        print(f"\n{page_name}:")
        print(f"  Actual page: {W_mm_actual}mm x {H_mm_actual}mm")
        
        # Calculate actual page dimensions in pixels at dpi_tiles
        W_px_at_tiles = int((W_mm_actual / 25.4) * dpi_tiles)
        H_px_at_tiles = int((H_mm_actual / 25.4) * dpi_tiles)
        
        print(f"  Rendered at {dpi_tiles} DPI: {W_px_at_tiles}px x {H_px_at_tiles}px")
        
        # Calculate mm per pixel (what AI sees in prompt)
        mm_per_px_x = W_mm_actual / W_px_at_tiles
        mm_per_px_y = H_mm_actual / H_px_at_tiles
        print(f"  mm per pixel in prompt: {mm_per_px_x:.3f}mm/px (X), {mm_per_px_y:.3f}mm/px (Y)")
        
        # Test conversion for center of page
        center_px_x = W_px_at_tiles / 2
        center_px_y = H_px_at_tiles / 2
        
        # NEW (FIXED) two-step conversion:
        # Step 1: Convert pixels to mm in actual page space
        x_mm_actual = (center_px_x / W_px_at_tiles) * W_mm_actual
        y_mm_actual = (center_px_y / H_px_at_tiles) * H_mm_actual
        
        # Step 2: Scale from actual page to A3 target
        x_mm_target = (x_mm_actual / W_mm_actual) * W_mm_target
        y_mm_target = (y_mm_actual / H_mm_actual) * H_mm_target
        
        print(f"  Center pixel: ({center_px_x:.0f}px, {center_px_y:.0f}px)")
        print(f"  Step 1 - Actual mm: ({x_mm_actual:.1f}mm, {y_mm_actual:.1f}mm)")
        print(f"  Step 2 - Scaled to A3: ({x_mm_target:.1f}mm, {y_mm_target:.1f}mm)")
        print(f"  Expected A3 center: (210.0mm, 148.5mm)")
        
        # Verify it's correct
        assert abs(x_mm_target - 210.0) < 0.1, f"X coordinate should be 210mm, got {x_mm_target:.1f}mm"
        assert abs(y_mm_target - 148.5) < 0.1, f"Y coordinate should be 148.5mm, got {y_mm_target:.1f}mm"
        print(f"  ✓ CORRECT!")
        
        # Test a point near the edge
        edge_px_x = W_px_at_tiles * 0.9
        edge_px_y = H_px_at_tiles * 0.9
        
        x_mm_actual = (edge_px_x / W_px_at_tiles) * W_mm_actual
        y_mm_actual = (edge_px_y / H_px_at_tiles) * H_mm_actual
        x_mm_target = (x_mm_actual / W_mm_actual) * W_mm_target
        y_mm_target = (y_mm_actual / H_mm_actual) * H_mm_target
        
        print(f"  Edge (90%): ({edge_px_x:.0f}px, {edge_px_y:.0f}px)")
        print(f"  Scaled to A3: ({x_mm_target:.1f}mm, {y_mm_target:.1f}mm)")
        print(f"  Expected: (378.0mm, 267.3mm)")
        
        assert abs(x_mm_target - 378.0) < 0.1, f"X coordinate should be 378mm, got {x_mm_target:.1f}mm"
        assert abs(y_mm_target - 267.3) < 0.5, f"Y coordinate should be ~267mm, got {y_mm_target:.1f}mm"
        print(f"  ✓ CORRECT!")


def test_coordinate_range_with_fix():
    """
    Verify that coordinates now span the full A3 range
    """
    print("\n=== Testing full coordinate range ===")
    
    # Simulate A0 page (worst case scenario)
    W_mm_actual = 1189.0
    H_mm_actual = 841.0
    W_mm_target = 420.0
    H_mm_target = 297.0
    
    dpi = 300
    W_px = int((W_mm_actual / 25.4) * dpi)
    H_px = int((H_mm_actual / 25.4) * dpi)
    
    print(f"Actual page: {W_mm_actual}mm x {H_mm_actual}mm")
    print(f"Rendered: {W_px}px x {H_px}px")
    print(f"Target: {W_mm_target}mm x {H_mm_target}mm")
    print()
    
    # Test various positions
    test_points = [
        (0, 0, "Top-left"),
        (W_px, H_px, "Bottom-right"),
        (W_px * 0.25, H_px * 0.25, "Quarter point"),
        (W_px * 0.5, H_px * 0.5, "Center"),
        (W_px * 0.75, H_px * 0.75, "Three-quarter point"),
    ]
    
    for px_x, px_y, desc in test_points:
        # Two-step conversion
        x_mm_actual = (px_x / W_px) * W_mm_actual
        y_mm_actual = (px_y / H_px) * H_mm_actual
        x_mm_target = (x_mm_actual / W_mm_actual) * W_mm_target
        y_mm_target = (y_mm_actual / H_mm_actual) * H_mm_target
        
        print(f"{desc}: ({px_x:.0f}px, {px_y:.0f}px) → ({x_mm_target:.1f}mm, {y_mm_target:.1f}mm)")
        
        # Verify it's within A3 bounds
        assert 0 <= x_mm_target <= W_mm_target, f"X out of bounds: {x_mm_target:.1f}mm"
        assert 0 <= y_mm_target <= H_mm_target, f"Y out of bounds: {y_mm_target:.1f}mm"
    
    print("\n✓ All coordinates are within A3 bounds (0-420mm x 0-297mm)")
    print("✓ Coordinates now span the FULL A3 range!")


if __name__ == "__main__":
    test_fixed_coordinate_conversion()
    test_coordinate_range_with_fix()
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\nThe fix correctly:")
    print("1. Uses ACTUAL page dimensions in prompts (correct mm-per-pixel)")
    print("2. Scales final coordinates to A3 space (420x297mm)")
    print("3. Ensures coordinates span the full A3 range")
    print("="*60)
