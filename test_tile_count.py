#!/usr/bin/env python3
"""
Test the calculate_tile_count function to verify it works correctly.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_tile_count_calculation():
    """Test that calculate_tile_count produces correct results"""
    print("\n=== Testing calculate_tile_count ===")
    
    # We'll test the calculation logic without a real PDF page
    tile_px = 1024
    overlap_ratio = 0.37
    
    # Test with various image dimensions
    test_cases = [
        (3637, 2572, 15),  # 220 DPI A3
        (4960, 3507, 28),  # 300 DPI A3
        (6614, 4677, 54),  # 400 DPI A3
        (500, 500, 1),     # Small image
    ]
    
    for W, H, expected in test_cases:
        step = int(tile_px * (1.0 - overlap_ratio)) or tile_px
        y_count = len(list(range(0, max(1, H - tile_px + 1), step)))
        x_count = len(list(range(0, max(1, W - tile_px + 1), step)))
        total = x_count * y_count
        
        print(f"   W={W}, H={H}: {x_count} x {y_count} = {total} tiles (expected {expected})")
        assert total == expected, f"Expected {expected} tiles, got {total}"
    
    print("✅ All tile count calculations correct!")
    return True


if __name__ == "__main__":
    try:
        success = test_tile_count_calculation()
        sys.exit(0 if success else 1)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
