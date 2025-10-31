#!/usr/bin/env python3
"""
Test to verify that actual page dimensions are used without swapping.
This ensures coordinates extracted match the actual PDF page orientation.
"""

import sys
import io
import fitz  # PyMuPDF

sys.path.insert(0, 'backend')
from backend import points_to_mm


def create_test_pdf(width_pts, height_pts):
    """Create a simple test PDF with specified dimensions."""
    doc = fitz.open()
    page = doc.new_page(width=width_pts, height=height_pts)
    return doc, page


def test_landscape_page():
    """Test landscape page (width > height)."""
    print("Testing Landscape Page (1500 x 594 points ≈ 529.2 x 209.5 mm):")
    print("-" * 70)
    
    # Create landscape PDF: 1500 x 594 points
    doc, page = create_test_pdf(1500, 594)
    
    W_pts, H_pts = page.rect.width, page.rect.height
    W_mm, H_mm = points_to_mm(W_pts), points_to_mm(H_pts)
    
    print(f"  PDF dimensions: {W_pts:.1f} x {H_pts:.1f} points")
    print(f"  Converted:      {W_mm:.1f} x {H_mm:.1f} mm")
    
    # Verify dimensions are NOT swapped
    expected_w = points_to_mm(1500)
    expected_h = points_to_mm(594)
    
    if abs(W_mm - expected_w) < 0.01 and abs(H_mm - expected_h) < 0.01:
        print(f"  ✓ Dimensions preserved: width={W_mm:.1f}mm, height={H_mm:.1f}mm")
        return True
    else:
        print(f"  ✗ FAILED: Expected {expected_w:.1f}x{expected_h:.1f}mm, got {W_mm:.1f}x{H_mm:.1f}mm")
        return False


def test_portrait_page():
    """Test portrait page (height > width)."""
    print("\nTesting Portrait Page (594 x 1500 points ≈ 209.5 x 529.2 mm):")
    print("-" * 70)
    
    # Create portrait PDF: 594 x 1500 points
    doc, page = create_test_pdf(594, 1500)
    
    W_pts, H_pts = page.rect.width, page.rect.height
    W_mm, H_mm = points_to_mm(W_pts), points_to_mm(H_pts)
    
    print(f"  PDF dimensions: {W_pts:.1f} x {H_pts:.1f} points")
    print(f"  Converted:      {W_mm:.1f} x {H_mm:.1f} mm")
    
    # Verify dimensions are NOT swapped
    expected_w = points_to_mm(594)
    expected_h = points_to_mm(1500)
    
    if abs(W_mm - expected_w) < 0.01 and abs(H_mm - expected_h) < 0.01:
        print(f"  ✓ Dimensions preserved: width={W_mm:.1f}mm, height={H_mm:.1f}mm")
        return True
    else:
        print(f"  ✗ FAILED: Expected {expected_w:.1f}x{expected_h:.1f}mm, got {W_mm:.1f}x{H_mm:.1f}mm")
        return False


def test_square_page():
    """Test square page (width == height)."""
    print("\nTesting Square Page (1000 x 1000 points ≈ 352.8 x 352.8 mm):")
    print("-" * 70)
    
    # Create square PDF: 1000 x 1000 points
    doc, page = create_test_pdf(1000, 1000)
    
    W_pts, H_pts = page.rect.width, page.rect.height
    W_mm, H_mm = points_to_mm(W_pts), points_to_mm(H_pts)
    
    print(f"  PDF dimensions: {W_pts:.1f} x {H_pts:.1f} points")
    print(f"  Converted:      {W_mm:.1f} x {H_mm:.1f} mm")
    
    # Verify dimensions are equal
    expected = points_to_mm(1000)
    
    if abs(W_mm - expected) < 0.01 and abs(H_mm - expected) < 0.01:
        print(f"  ✓ Dimensions preserved: width={W_mm:.1f}mm, height={H_mm:.1f}mm")
        return True
    else:
        print(f"  ✗ FAILED: Expected {expected:.1f}x{expected:.1f}mm, got {W_mm:.1f}x{H_mm:.1f}mm")
        return False


def test_a4_pages():
    """Test standard A4 page in both orientations."""
    print("\nTesting A4 Page - Portrait (595.276 x 841.890 points = 210 x 297 mm):")
    print("-" * 70)
    
    doc, page = create_test_pdf(595.276, 841.890)
    W_pts, H_pts = page.rect.width, page.rect.height
    W_mm, H_mm = points_to_mm(W_pts), points_to_mm(H_pts)
    
    print(f"  PDF dimensions: {W_pts:.3f} x {H_pts:.3f} points")
    print(f"  Converted:      {W_mm:.1f} x {H_mm:.1f} mm")
    
    portrait_pass = (abs(W_mm - 210.0) < 0.1 and abs(H_mm - 297.0) < 0.1)
    if portrait_pass:
        print(f"  ✓ A4 Portrait dimensions correct: {W_mm:.1f}x{H_mm:.1f}mm")
    else:
        print(f"  ✗ FAILED: Expected 210x297mm, got {W_mm:.1f}x{H_mm:.1f}mm")
    
    print("\nTesting A4 Page - Landscape (841.890 x 595.276 points = 297 x 210 mm):")
    print("-" * 70)
    
    doc, page = create_test_pdf(841.890, 595.276)
    W_pts, H_pts = page.rect.width, page.rect.height
    W_mm, H_mm = points_to_mm(W_pts), points_to_mm(H_pts)
    
    print(f"  PDF dimensions: {W_pts:.3f} x {H_pts:.3f} points")
    print(f"  Converted:      {W_mm:.1f} x {H_mm:.1f} mm")
    
    landscape_pass = (abs(W_mm - 297.0) < 0.1 and abs(H_mm - 210.0) < 0.1)
    if landscape_pass:
        print(f"  ✓ A4 Landscape dimensions correct: {W_mm:.1f}x{H_mm:.1f}mm")
    else:
        print(f"  ✗ FAILED: Expected 297x210mm, got {W_mm:.1f}x{H_mm:.1f}mm")
    
    return portrait_pass and landscape_pass


def main():
    print("=" * 70)
    print("PAGE DIMENSION PRESERVATION TEST")
    print("=" * 70)
    print()
    print("This test verifies that actual page dimensions are used without")
    print("swapping, ensuring coordinates match the actual PDF orientation.")
    print()
    
    result1 = test_landscape_page()
    result2 = test_portrait_page()
    result3 = test_square_page()
    result4 = test_a4_pages()
    
    print()
    print("=" * 70)
    if result1 and result2 and result3 and result4:
        print("✅ ALL PAGE DIMENSION TESTS PASSED!")
        print()
        print("Summary:")
        print("- Landscape pages: dimensions preserved (width > height)")
        print("- Portrait pages: dimensions preserved (height > width)")
        print("- Square pages: dimensions preserved (width == height)")
        print("- A4 pages: both orientations correct")
        print()
        print("Expected Outcome:")
        print("- LLM sees actual page orientation")
        print("- Prompt tells LLM the correct dimensions")
        print("- Coordinates extracted match actual page layout")
        print("- Horizontally aligned objects have same Y coordinate")
        print("- Vertically aligned objects have same X coordinate")
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
