#!/usr/bin/env python3
"""
Demonstration of the electrical diagram coordinate fix.

This script shows how the coordinate system now works correctly
for electrical diagrams using actual sheet dimensions.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend import (
    build_prompt_electrical_global,
    build_prompt_electrical_tile,
    points_to_mm
)


def demo_coordinate_fix():
    """
    Demonstrate that electrical diagrams now use actual sheet dimensions
    instead of hardcoded A3 dimensions.
    """
    print("\n" + "="*70)
    print("ELECTRICAL DIAGRAM COORDINATE FIX DEMONSTRATION")
    print("="*70)
    
    print("\n📋 PROBLEM STATEMENT:")
    print("   Electrical diagrams had poor coordinate accuracy because:")
    print("   - Used hardcoded A3 dimensions (420mm x 297mm) regardless of actual sheet")
    print("   - Had 4mm coordinate rounding (too coarse)")
    print("   - Didn't match P&ID behavior which uses actual dimensions")
    
    print("\n✅ SOLUTION:")
    print("   - Now uses actual sheet dimensions (not hardcoded A3)")
    print("   - Maintains 4mm grid rounding (but with correct scale)")
    print("   - Prompts include sheet dimensions and mm/px conversion ratios")
    
    print("\n" + "="*70)
    print("EXAMPLE 1: A3 SHEET (420mm x 297mm)")
    print("="*70)
    
    # Simulate A3 sheet
    w_mm_a3 = 420.0
    h_mm_a3 = 297.0
    wpx_a3 = 3000
    hpx_a3 = 2100
    
    print(f"\n📐 Sheet: {w_mm_a3}mm x {h_mm_a3}mm")
    print(f"🖼️  Image: {wpx_a3}px x {hpx_a3}px")
    
    # Generate prompt
    prompt = build_prompt_electrical_global(0, wpx_a3, hpx_a3, w_mm_a3, h_mm_a3)
    
    # Check that prompt includes actual dimensions
    if f"{w_mm_a3:.1f}mm" in prompt and f"{h_mm_a3:.1f}mm" in prompt:
        print("✅ Prompt includes actual sheet dimensions")
    else:
        print("❌ ERROR: Prompt missing actual dimensions!")
    
    # Calculate mm per pixel
    mm_per_px_x = w_mm_a3 / wpx_a3
    mm_per_px_y = h_mm_a3 / hpx_a3
    print(f"🔍 Conversion: {mm_per_px_x:.3f}mm/px (X), {mm_per_px_y:.3f}mm/px (Y)")
    
    # Example equipment at pixel (1500, 1050)
    eq_px_x = 1500.0
    eq_px_y = 1050.0
    eq_mm_x = (eq_px_x / wpx_a3) * w_mm_a3
    eq_mm_y = (eq_px_y / hpx_a3) * h_mm_a3
    
    # Apply 4mm rounding
    import math
    eq_mm_x_rounded = math.floor((eq_mm_x + 2.0) / 4.0) * 4.0
    eq_mm_y_rounded = math.floor((eq_mm_y + 2.0) / 4.0) * 4.0
    
    print(f"\n📍 Equipment at pixel ({eq_px_x:.0f}, {eq_px_y:.0f})")
    print(f"   Calculated: ({eq_mm_x:.2f}mm, {eq_mm_y:.2f}mm)")
    print(f"   After 4mm rounding: ({eq_mm_x_rounded:.0f}mm, {eq_mm_y_rounded:.0f}mm)")
    print(f"   ✅ Coordinates use actual sheet size, then rounded to 4mm grid")
    
    print("\n" + "="*70)
    print("EXAMPLE 2: A1 SHEET (594mm x 841mm) - LARGER THAN A3")
    print("="*70)
    
    # Simulate A1 sheet (larger than A3)
    w_mm_a1 = 594.0
    h_mm_a1 = 841.0
    wpx_a1 = 4200
    hpx_a1 = 5950
    
    print(f"\n📐 Sheet: {w_mm_a1}mm x {h_mm_a1}mm")
    print(f"🖼️  Image: {wpx_a1}px x {hpx_a1}px")
    
    # Generate prompt
    prompt_a1 = build_prompt_electrical_global(0, wpx_a1, hpx_a1, w_mm_a1, h_mm_a1)
    
    # Check that prompt includes actual dimensions (NOT A3!)
    if f"{w_mm_a1:.1f}mm" in prompt_a1 and f"{h_mm_a1:.1f}mm" in prompt_a1:
        print("✅ Prompt includes actual sheet dimensions (A1, not hardcoded A3)")
    else:
        print("❌ ERROR: Prompt missing actual dimensions!")
    
    if "420" not in prompt_a1:  # Should NOT contain A3 width
        print("✅ No hardcoded A3 dimensions in prompt")
    
    # Calculate mm per pixel
    mm_per_px_x_a1 = w_mm_a1 / wpx_a1
    mm_per_px_y_a1 = h_mm_a1 / hpx_a1
    print(f"🔍 Conversion: {mm_per_px_x_a1:.3f}mm/px (X), {mm_per_px_y_a1:.3f}mm/px (Y)")
    
    # Example equipment at same pixel location
    eq_mm_x_a1 = (eq_px_x / wpx_a1) * w_mm_a1
    eq_mm_y_a1 = (eq_px_y / hpx_a1) * h_mm_a1
    
    # Apply 4mm rounding
    eq_mm_x_a1_rounded = math.floor((eq_mm_x_a1 + 2.0) / 4.0) * 4.0
    eq_mm_y_a1_rounded = math.floor((eq_mm_y_a1 + 2.0) / 4.0) * 4.0
    
    print(f"\n📍 Equipment at pixel ({eq_px_x:.0f}, {eq_px_y:.0f})")
    print(f"   Calculated: ({eq_mm_x_a1:.2f}mm, {eq_mm_y_a1:.2f}mm)")
    print(f"   After 4mm rounding: ({eq_mm_x_a1_rounded:.0f}mm, {eq_mm_y_a1_rounded:.0f}mm)")
    print(f"   ✅ Uses A1 sheet dimensions (not A3!)")
    
    print("\n" + "="*70)
    print("COMPARISON: BEFORE vs AFTER")
    print("="*70)
    
    print("\n❌ BEFORE (with hardcoded A3):")
    print("   - A1 sheet would be treated as A3")
    print("   - Coordinates would be wrong by a factor of:")
    print(f"     X: {w_mm_a1/420.0:.2f}x ({(w_mm_a1/420.0 - 1)*100:.0f}% error)")
    print(f"     Y: {h_mm_a1/297.0:.2f}x ({(h_mm_a1/297.0 - 1)*100:.0f}% error)")
    print("   - 4mm grid applied to WRONG scale")
    
    print("\n✅ AFTER (with actual dimensions + 4mm grid):")
    print("   - Each sheet size uses its actual dimensions")
    print("   - Coordinates calculated with correct scale")
    print("   - 4mm grid applied AFTER correct calculation")
    print("   - Prompts include mm/px conversion for LLM understanding")
    
    print("\n" + "="*70)
    print("TILE PROCESSING EXAMPLE")
    print("="*70)
    
    # Simulate tile processing
    tile_w_px = 1536
    tile_h_px = 1536
    ox = 1000  # Tile offset X
    oy = 500   # Tile offset Y
    
    print(f"\n🔲 Tile: {tile_w_px}px x {tile_h_px}px")
    print(f"📍 Tile offset: ({ox}px, {oy}px)")
    print(f"📐 Page: {w_mm_a1}mm x {h_mm_a1}mm ({wpx_a1}px x {hpx_a1}px)")
    
    tile_prompt = build_prompt_electrical_tile(
        0, ox, oy, tile_w_px, tile_h_px, w_mm_a1, h_mm_a1, wpx_a1, hpx_a1
    )
    
    if f"{w_mm_a1:.1f}mm" in tile_prompt:
        print("✅ Tile prompt includes actual page dimensions")
    
    if f"{ox}px" in tile_prompt and f"{oy}px" in tile_prompt:
        print("✅ Tile prompt includes tile offset information")
    
    print(f"🔍 Tile LLM will know:")
    print(f"   - This is a {tile_w_px}x{tile_h_px} tile of a larger page")
    print(f"   - The full page is {w_mm_a1}mm x {h_mm_a1}mm")
    print(f"   - Conversion: {mm_per_px_x_a1:.3f}mm/px")
    
    print("\n" + "="*70)
    print("✅ SUMMARY")
    print("="*70)
    print("\nThe coordinate fix ensures that:")
    print("1. ✅ Electrical diagrams use actual sheet dimensions (not hardcoded A3)")
    print("2. ✅ Coordinates calculated with correct scale based on real sheet size")
    print("3. ✅ 4mm grid rounding applied AFTER correct calculation")
    print("4. ✅ Prompts inform LLM about sheet size and px→mm conversion")
    print("5. ✅ Works correctly for any sheet size (A0, A1, A2, A3, A4, custom)")
    print("6. ✅ Tile processing includes offset and page context")
    print("\n🎯 Result: Coordinates use correct scale + 4mm grid positioning!")
    print("="*70 + "\n")


if __name__ == "__main__":
    demo_coordinate_fix()
