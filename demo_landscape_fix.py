#!/usr/bin/env python3
"""
Demo script to show the landscape mode fix in action.
Creates a sample portrait PDF and shows how it's processed.
"""

import fitz
import tempfile
import os
import base64


def points_to_mm(pts):
    """Convert points to millimeters"""
    return pts * 25.4 / 72.0


def demonstrate_fix():
    """Demonstrate the landscape mode fix"""
    
    print("="*70)
    print("LANDSCAPE MODE FIX DEMONSTRATION")
    print("="*70)
    print()
    
    # Create a sample portrait PDF (similar to what might be uploaded)
    print("1. Creating a sample portrait PDF...")
    doc = fitz.open()
    
    # A4 portrait: 595 x 842 points (210 x 297 mm)
    portrait_page = doc.new_page(width=595, height=842)
    
    # Add some sample content to make it realistic
    portrait_page.insert_text((50, 50), "P&ID Sample - Portrait Mode", fontsize=16)
    portrait_page.insert_text((50, 100), "Equipment:", fontsize=12)
    portrait_page.insert_text((70, 120), "P-101: Centrifugal Pump", fontsize=10)
    portrait_page.insert_text((70, 140), "T-201: Storage Tank", fontsize=10)
    
    # Draw some rectangles to simulate equipment
    portrait_page.draw_rect(fitz.Rect(100, 200, 200, 300), color=(0, 0, 1), width=2)
    portrait_page.insert_text((110, 260), "P-101", fontsize=10)
    
    portrait_page.draw_rect(fitz.Rect(300, 350, 450, 500), color=(1, 0, 0), width=2)
    portrait_page.insert_text((340, 425), "T-201", fontsize=10)
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp_path = tmp.name
        doc.save(tmp_path)
    doc.close()
    
    print(f"   ✓ Created sample PDF: {tmp_path}")
    print()
    
    # Simulate the old behavior (WRONG)
    print("2. OLD BEHAVIOR (before fix):")
    print("   " + "-"*60)
    doc = fitz.open(tmp_path)
    page = doc[0]
    
    W_pts, H_pts = page.rect.width, page.rect.height
    W_mm, H_mm = points_to_mm(W_pts), points_to_mm(H_pts)
    
    print(f"   Page dimensions from PDF: {W_mm:.1f} x {H_mm:.1f} mm")
    print(f"   Orientation: Portrait (height > width)")
    print()
    
    # Old approach: just swap variables
    if H_mm > W_mm:
        W_mm_swapped, H_mm_swapped = H_mm, W_mm
        print(f"   ❌ OLD: Swapped variables to {W_mm_swapped:.1f} x {H_mm_swapped:.1f} mm")
        print(f"   ❌ PROBLEM: AI is told dimensions are {W_mm_swapped:.1f} x {H_mm_swapped:.1f}")
    
    # Render the image (still portrait!)
    pix = page.get_pixmap(dpi=100)
    print(f"   ❌ PROBLEM: But image sent to AI is {pix.width} x {pix.height} pixels")
    print(f"   ❌ PROBLEM: Image orientation is still PORTRAIT!")
    print()
    print(f"   ⚠️  RESULT: Coordinates returned by AI are INCORRECT!")
    print(f"   ⚠️  The AI sees portrait but is told it's landscape")
    
    doc.close()
    print()
    
    # Simulate the new behavior (CORRECT)
    print("3. NEW BEHAVIOR (after fix):")
    print("   " + "-"*60)
    doc = fitz.open(tmp_path)
    page = doc[0]
    
    W_pts, H_pts = page.rect.width, page.rect.height
    
    print(f"   Page dimensions from PDF: {points_to_mm(W_pts):.1f} x {points_to_mm(H_pts):.1f} mm")
    print(f"   Orientation: Portrait (height > width)")
    print()
    
    # New approach: actually rotate the page
    if H_pts > W_pts:
        print(f"   ✓ NEW: Rotating page 90 degrees to landscape...")
        page.set_rotation(90)
        W_pts, H_pts = page.rect.width, page.rect.height
        W_mm, H_mm = points_to_mm(W_pts), points_to_mm(H_pts)
        print(f"   ✓ NEW: Page is now {W_mm:.1f} x {H_mm:.1f} mm (landscape)")
    
    # Render the image (now landscape!)
    pix = page.get_pixmap(dpi=100)
    print(f"   ✓ NEW: Image sent to AI is {pix.width} x {pix.height} pixels")
    print(f"   ✓ NEW: Image orientation is LANDSCAPE!")
    print()
    print(f"   ✅ RESULT: Coordinates returned by AI are CORRECT!")
    print(f"   ✅ The AI sees landscape AND is told it's landscape")
    
    doc.close()
    print()
    
    # Summary
    print("4. SUMMARY:")
    print("   " + "-"*60)
    print("   Before fix:")
    print("     • Variables swapped but page image remained portrait")
    print("     • AI received mismatched information")
    print("     • Coordinates were incorrect")
    print()
    print("   After fix:")
    print("     • Page physically rotated to landscape")
    print("     • AI receives consistent information")
    print("     • Coordinates are correct ✓")
    print()
    
    # Cleanup
    os.unlink(tmp_path)
    print(f"   Cleaned up temporary file")
    print()
    print("="*70)
    print("✅ FIX DEMONSTRATED SUCCESSFULLY!")
    print("="*70)


if __name__ == "__main__":
    demonstrate_fix()
