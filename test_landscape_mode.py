#!/usr/bin/env python3
"""
Test to verify that PDF pages are correctly rotated to landscape mode.
"""

import fitz
import tempfile
import os


def test_portrait_to_landscape_rotation():
    """Test that portrait pages are rotated to landscape"""
    
    print("="*60)
    print("LANDSCAPE MODE ROTATION TEST")
    print("="*60)
    print()
    
    # Create a test PDF with portrait page (A4: 595 x 842 points)
    doc = fitz.open()
    portrait_page = doc.new_page(width=595, height=842)
    
    # Add some text to make it visible
    portrait_page.insert_text((50, 50), "Portrait Page Test", fontsize=20)
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp_path = tmp.name
        doc.save(tmp_path)
    doc.close()
    
    try:
        # Re-open the PDF to test the rotation logic
        doc = fitz.open(tmp_path)
        page = doc[0]
        
        print(f"Original page dimensions: {page.rect.width:.1f} x {page.rect.height:.1f} points")
        print(f"Original orientation: {'Portrait' if page.rect.height > page.rect.width else 'Landscape'}")
        print()
        
        # Apply the rotation logic from backend.py
        W_pts, H_pts = page.rect.width, page.rect.height
        
        if H_pts > W_pts:
            print(f"✓ Portrait detected, rotating to landscape...")
            page.set_rotation(90)
            W_pts, H_pts = page.rect.width, page.rect.height
            print(f"  After rotation: {W_pts:.1f} x {H_pts:.1f} points")
        
        # Verify the page is now in landscape
        is_landscape = W_pts > H_pts
        print()
        print(f"Final orientation: {'Landscape ✓' if is_landscape else 'Portrait ✗'}")
        print(f"Final dimensions: {W_pts:.1f} x {H_pts:.1f} points")
        
        # Test pixmap rendering
        pix = page.get_pixmap(dpi=100)
        print(f"Rendered image size: {pix.width} x {pix.height} pixels")
        print(f"Image orientation: {'Landscape ✓' if pix.width > pix.height else 'Portrait ✗'}")
        
        doc.close()
        
        # Cleanup
        os.unlink(tmp_path)
        
        print()
        print("="*60)
        
        if is_landscape and pix.width > pix.height:
            print("✅ TEST PASSED: Page correctly rotated to landscape")
            return True
        else:
            print("❌ TEST FAILED: Page not in landscape orientation")
            return False
            
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_landscape_unchanged():
    """Test that landscape pages remain unchanged"""
    
    print()
    print("="*60)
    print("LANDSCAPE PRESERVATION TEST")
    print("="*60)
    print()
    
    # Create a test PDF with landscape page (A4 rotated: 842 x 595 points)
    doc = fitz.open()
    landscape_page = doc.new_page(width=842, height=595)
    
    # Add some text
    landscape_page.insert_text((50, 50), "Landscape Page Test", fontsize=20)
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp_path = tmp.name
        doc.save(tmp_path)
    doc.close()
    
    try:
        # Re-open the PDF
        doc = fitz.open(tmp_path)
        page = doc[0]
        
        print(f"Original page dimensions: {page.rect.width:.1f} x {page.rect.height:.1f} points")
        print(f"Original orientation: {'Landscape' if page.rect.width > page.rect.height else 'Portrait'}")
        print()
        
        # Apply the rotation logic from backend.py
        W_pts, H_pts = page.rect.width, page.rect.height
        original_rotation = page.rotation
        
        if H_pts > W_pts:
            print(f"Portrait detected, rotating to landscape...")
            page.set_rotation(90)
            W_pts, H_pts = page.rect.width, page.rect.height
        else:
            print(f"✓ Already in landscape, no rotation needed")
        
        # Verify rotation was not applied
        is_landscape = W_pts > H_pts
        rotation_unchanged = page.rotation == original_rotation
        
        print()
        print(f"Final orientation: {'Landscape ✓' if is_landscape else 'Portrait ✗'}")
        print(f"Rotation applied: {'No ✓' if rotation_unchanged else 'Yes ✗'}")
        
        doc.close()
        
        # Cleanup
        os.unlink(tmp_path)
        
        print()
        print("="*60)
        
        if is_landscape and rotation_unchanged:
            print("✅ TEST PASSED: Landscape page preserved")
            return True
        else:
            print("❌ TEST FAILED: Landscape page was modified")
            return False
            
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_a0_dimensions():
    """Test with A0 dimensions (typical P&ID size)"""
    
    print()
    print("="*60)
    print("A0 SHEET DIMENSIONS TEST")
    print("="*60)
    print()
    
    # A0 in portrait: 841 x 1189 mm = 2384 x 3370 points
    # A0 in landscape: 1189 x 841 mm = 3370 x 2384 points
    
    def points_to_mm(pts):
        return pts * 25.4 / 72.0
    
    doc = fitz.open()
    # Create A0 portrait
    a0_portrait = doc.new_page(width=2384, height=3370)
    
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp_path = tmp.name
        doc.save(tmp_path)
    doc.close()
    
    try:
        doc = fitz.open(tmp_path)
        page = doc[0]
        
        print(f"Original A0 page: {points_to_mm(page.rect.width):.1f} x {points_to_mm(page.rect.height):.1f} mm")
        
        # Apply rotation logic
        W_pts, H_pts = page.rect.width, page.rect.height
        if H_pts > W_pts:
            print(f"Rotating A0 portrait to landscape...")
            page.set_rotation(90)
            W_pts, H_pts = page.rect.width, page.rect.height
        
        W_mm, H_mm = points_to_mm(W_pts), points_to_mm(H_pts)
        print(f"Final A0 page: {W_mm:.1f} x {H_mm:.1f} mm")
        
        # Check if dimensions match expected A0 landscape (1189 x 841 mm)
        expected_w, expected_h = 1189.0, 841.0
        tolerance = 5.0  # 5mm tolerance
        
        w_ok = abs(W_mm - expected_w) < tolerance
        h_ok = abs(H_mm - expected_h) < tolerance
        
        print()
        print(f"Expected: {expected_w} x {expected_h} mm")
        print(f"Width match: {'✓' if w_ok else '✗'}")
        print(f"Height match: {'✓' if h_ok else '✗'}")
        
        doc.close()
        os.unlink(tmp_path)
        
        print()
        print("="*60)
        
        if w_ok and h_ok:
            print("✅ TEST PASSED: A0 dimensions correct")
            return True
        else:
            print("❌ TEST FAILED: A0 dimensions incorrect")
            return False
            
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    
    results = [
        test_portrait_to_landscape_rotation(),
        test_landscape_unchanged(),
        test_a0_dimensions()
    ]
    
    print()
    print("="*60)
    if all(results):
        print("✅ ALL TESTS PASSED!")
        print()
        print("Summary:")
        print("- Portrait pages are rotated to landscape")
        print("- Landscape pages are preserved")
        print("- A0 dimensions are correct")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)
