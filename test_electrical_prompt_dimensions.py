#!/usr/bin/env python3
"""
Test that electrical diagram prompts now use actual sheet dimensions
instead of hardcoded A3 dimensions.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend import build_prompt_electrical_global, build_prompt_electrical_tile


def test_global_prompt_includes_dimensions():
    """Test that global prompt includes actual sheet dimensions"""
    print("\n=== Testing global prompt dimensions ===")
    
    # Test with A4 sheet (210mm x 297mm)
    prompt_a4 = build_prompt_electrical_global(
        page_idx=0,
        wpx=595,
        hpx=842,
        w_mm=210.0,
        h_mm=297.0
    )
    
    # Should include actual dimensions
    assert "210.0mm" in prompt_a4, "Prompt should include actual width (210mm)"
    assert "297.0mm" in prompt_a4, "Prompt should include actual height (297mm)"
    print("✅ Global prompt includes A4 dimensions (210mm x 297mm)")
    
    # Test with A0 sheet (841mm x 1189mm)
    prompt_a0 = build_prompt_electrical_global(
        page_idx=0,
        wpx=2384,
        hpx=3370,
        w_mm=841.0,
        h_mm=1189.0
    )
    
    # Should include actual dimensions
    assert "841.0mm" in prompt_a0, "Prompt should include actual width (841mm)"
    assert "1189.0mm" in prompt_a0, "Prompt should include actual height (1189mm)"
    print("✅ Global prompt includes A0 dimensions (841mm x 1189mm)")
    
    # Should NOT reference hardcoded A3 dimensions
    assert "420" not in prompt_a4, "Prompt should NOT include hardcoded A3 width (420mm)"
    print("✅ Global prompt does NOT include hardcoded A3 dimensions")


def test_tile_prompt_includes_dimensions():
    """Test that tile prompt includes actual sheet dimensions"""
    print("\n=== Testing tile prompt dimensions ===")
    
    # Test with A3 sheet (420mm x 297mm)
    prompt_a3 = build_prompt_electrical_tile(
        page_idx=0,
        ox=0,
        oy=0,
        tile_w_px=1536,
        tile_h_px=1536,
        page_w_mm=420.0,
        page_h_mm=297.0,
        page_w_px=3000,
        page_h_px=2100
    )
    
    # Should include actual page dimensions
    assert "420.0mm" in prompt_a3, "Prompt should include actual page width (420mm)"
    assert "297.0mm" in prompt_a3, "Prompt should include actual page height (297mm)"
    print("✅ Tile prompt includes A3 sheet dimensions (420mm x 297mm)")
    
    # Should include pixel to mm conversion info
    assert "mm" in prompt_a3.lower(), "Prompt should mention mm units"
    print("✅ Tile prompt includes pixel to mm conversion info")
    
    # Test with A1 sheet (594mm x 841mm)
    prompt_a1 = build_prompt_electrical_tile(
        page_idx=0,
        ox=1000,
        oy=500,
        tile_w_px=1536,
        tile_h_px=1536,
        page_w_mm=594.0,
        page_h_mm=841.0,
        page_w_px=4200,
        page_h_px=5950
    )
    
    # Should include actual dimensions
    assert "594.0mm" in prompt_a1, "Prompt should include actual page width (594mm)"
    assert "841.0mm" in prompt_a1, "Prompt should include actual page height (841mm)"
    print("✅ Tile prompt includes A1 sheet dimensions (594mm x 841mm)")


def test_prompt_calculates_mm_per_pixel():
    """Test that prompts calculate and include mm per pixel ratios"""
    print("\n=== Testing mm per pixel calculation ===")
    
    # Test with known dimensions
    prompt = build_prompt_electrical_tile(
        page_idx=0,
        ox=0,
        oy=0,
        tile_w_px=1536,
        tile_h_px=1536,
        page_w_mm=420.0,
        page_h_mm=297.0,
        page_w_px=3000,
        page_h_px=2100
    )
    
    # Expected ratios:
    # X: 420.0 / 3000 = 0.14 mm/px
    # Y: 297.0 / 2100 = 0.141 mm/px
    
    # Should mention the conversion ratio
    assert "0.14" in prompt or "0.141" in prompt, "Prompt should include mm per pixel ratio"
    print("✅ Tile prompt includes mm per pixel conversion ratios")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("ELECTRICAL PROMPT DIMENSIONS TESTS")
    print("="*60)
    
    try:
        test_global_prompt_includes_dimensions()
        test_tile_prompt_includes_dimensions()
        test_prompt_calculates_mm_per_pixel()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nSummary:")
        print("- Global prompts now use actual sheet dimensions")
        print("- Tile prompts now use actual sheet dimensions")
        print("- Prompts include mm per pixel conversion ratios")
        print("- No more hardcoded A3 dimensions for electrical diagrams")
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
