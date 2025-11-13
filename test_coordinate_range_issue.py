#!/usr/bin/env python3
"""
Test to reproduce the coordinate range issue reported by the user.
Objects are being drawn in a range of approximately 190 x 90mm instead of
spreading across the full A3 sheet (420 x 297mm).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))


def test_coordinate_conversion_with_different_page_sizes():
    """
    Test coordinate conversion when actual PDF page size differs from A3.
    This simulates the reported issue.
    """
    print("\n=== Testing coordinate conversion with different page sizes ===")
    
    # Fixed A3 dimensions (what we're forcing)
    W_mm_target = 420.0
    H_mm_target = 297.0
    
    # Simulate different actual PDF page sizes
    test_cases = [
        ("A3 (420x297mm)", 420.0, 297.0),
        ("A4 (297x210mm)", 297.0, 210.0),
        ("A0 (1189x841mm)", 1189.0, 841.0),
        ("Letter (279x216mm)", 279.0, 216.0),
    ]
    
    dpi_tiles = 300
    
    for page_name, actual_w_mm, actual_h_mm in test_cases:
        # Calculate actual page dimensions in pixels at dpi_tiles
        W_px_at_tiles = int((actual_w_mm / 25.4) * dpi_tiles)
        H_px_at_tiles = int((actual_h_mm / 25.4) * dpi_tiles)
        
        print(f"\n{page_name}:")
        print(f"  Actual page: {actual_w_mm}mm x {actual_h_mm}mm")
        print(f"  Rendered at {dpi_tiles} DPI: {W_px_at_tiles}px x {H_px_at_tiles}px")
        
        # Test conversion for a point in the center of the page
        center_px_x = W_px_at_tiles / 2
        center_px_y = H_px_at_tiles / 2
        
        # CURRENT (BUGGY) conversion formula from the code
        x_mm_buggy = (center_px_x / W_px_at_tiles) * W_mm_target
        y_mm_buggy = (center_px_y / H_px_at_tiles) * H_mm_target
        
        print(f"  Center pixel: ({center_px_x:.0f}px, {center_px_y:.0f}px)")
        print(f"  CURRENT conversion → ({x_mm_buggy:.1f}mm, {y_mm_buggy:.1f}mm)")
        print(f"  Expected center: (210.0mm, 148.5mm) for A3")
        
        # Test conversion for a point near the bottom-right
        br_px_x = W_px_at_tiles * 0.9
        br_px_y = H_px_at_tiles * 0.9
        
        x_mm_br = (br_px_x / W_px_at_tiles) * W_mm_target
        y_mm_br = (br_px_y / H_px_at_tiles) * H_mm_target
        
        print(f"  Bottom-right (90%): ({br_px_x:.0f}px, {br_px_y:.0f}px)")
        print(f"  CURRENT conversion → ({x_mm_br:.1f}mm, {y_mm_br:.1f}mm)")
        
        # Calculate the actual range being used
        max_x = (W_px_at_tiles / W_px_at_tiles) * W_mm_target
        max_y = (H_px_at_tiles / H_px_at_tiles) * H_mm_target
        print(f"  Coordinate range: 0-{max_x:.1f}mm x 0-{max_y:.1f}mm")
        
        # The ISSUE: all conversions give correct results because the formula
        # is actually normalizing correctly! So the bug must be elsewhere...


def test_actual_vs_target_dimensions():
    """
    The REAL issue: we're telling the AI the page is 420x297mm, but if we
    render a larger page (e.g., A0), the pixel coordinates from the AI will
    be relative to what IT SEES, not the actual page size.
    """
    print("\n=== Understanding the REAL issue ===")
    print("\nScenario: User has an A0 PDF (1189x841mm) but we're forcing A3 (420x297mm)")
    print()
    
    # What we tell the AI
    W_mm_told = 420.0
    H_mm_told = 297.0
    
    # What the actual PDF is
    actual_w_mm = 1189.0
    actual_h_mm = 841.0
    
    dpi = 300
    W_px_actual = int((actual_w_mm / 25.4) * dpi)
    H_px_actual = int((actual_h_mm / 25.4) * dpi)
    
    print(f"We tell AI: page is {W_mm_told}mm x {H_mm_told}mm")
    print(f"Actual PDF rendered: {W_px_actual}px x {H_px_actual}px")
    print()
    
    # The AI sees a large image but thinks it's 420x297mm
    # So when it places an object at the center of what it sees:
    center_px_x = W_px_actual / 2
    center_px_y = H_px_actual / 2
    
    # It might return coordinates thinking the full width is 420mm
    # But the pixel position is at the center of the ACTUAL page
    
    # When we convert back:
    x_mm = (center_px_x / W_px_actual) * W_mm_told
    y_mm = (center_px_y / H_px_actual) * H_mm_told
    
    print(f"AI places object at center of image: ({center_px_x:.0f}px, {center_px_y:.0f}px)")
    print(f"Our conversion: ({x_mm:.1f}mm, {y_mm:.1f}mm)")
    print(f"✓ This is CORRECT - center of A3 is (210, 148.5)")
    print()
    
    # But here's the REAL problem:
    # The AI is told the image is 420x297mm, so it returns pixel coordinates
    # proportional to that. But the image is actually much larger!
    
    # Let's say AI wants to place something at X=210mm (center of 420mm)
    # It sees an image that's 14016px wide
    # If it thinks the image is 420mm wide, it calculates:
    # 210mm / 420mm * 14016px = 7008px
    
    # But then we convert back:
    # 7008px / 14016px * 420mm = 210mm ✓ CORRECT!
    
    print("Wait... the math actually works out correctly!")
    print("The normalization handles the size difference.")
    print()
    print("So the bug must be in the PROMPT or in how AI interprets dimensions...")


if __name__ == "__main__":
    test_coordinate_conversion_with_different_page_sizes()
    test_actual_vs_target_dimensions()
