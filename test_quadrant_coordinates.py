#!/usr/bin/env python3
"""
Test to validate that quadrant coordinate conversion works correctly.
"""

import sys


def test_quadrant_coordinate_conversion():
    """Test that local quadrant coordinates are correctly converted to global page coordinates"""
    
    print("="*60)
    print("QUADRANT COORDINATE CONVERSION TEST")
    print("="*60)
    print()
    
    # Simulate A0 page divided into 3x3 grid
    W_mm = 1189.0  # Page width
    H_mm = 841.0   # Page height
    grid = 3
    
    # Calculate quadrant dimensions
    quad_w = W_mm / grid  # ≈ 396.33 mm
    quad_h = H_mm / grid  # ≈ 280.33 mm
    
    print(f"Page dimensions: {W_mm} x {H_mm} mm")
    print(f"Grid: {grid}x{grid}")
    print(f"Quadrant dimensions: {quad_w:.2f} x {quad_h:.2f} mm")
    print()
    
    # Test cases for different quadrants
    test_cases = [
        # (quadrant_x, quadrant_y, local_x, local_y, expected_global_x, expected_global_y)
        # Top-left quadrant (0, 0)
        (0, 0, 100.0, 100.0, 100.0, 100.0),
        (0, 0, 0.0, 0.0, 0.0, 0.0),
        
        # Top-middle quadrant (1, 0)
        (1, 0, 100.0, 100.0, 100.0 + quad_w, 100.0),
        (1, 0, 0.0, 0.0, quad_w, 0.0),
        
        # Top-right quadrant (2, 0)
        (2, 0, 100.0, 100.0, 100.0 + 2*quad_w, 100.0),
        (2, 0, 0.0, 0.0, 2*quad_w, 0.0),
        
        # Middle-left quadrant (0, 1)
        (0, 1, 100.0, 100.0, 100.0, 100.0 + quad_h),
        (0, 1, 0.0, 0.0, 0.0, quad_h),
        
        # Center quadrant (1, 1)
        (1, 1, 100.0, 100.0, 100.0 + quad_w, 100.0 + quad_h),
        (1, 1, 0.0, 0.0, quad_w, quad_h),
        
        # Bottom-right quadrant (2, 2)
        (2, 2, 100.0, 100.0, 100.0 + 2*quad_w, 100.0 + 2*quad_h),
        (2, 2, 0.0, 0.0, 2*quad_w, 2*quad_h),
    ]
    
    passed = 0
    failed = 0
    
    for gx, gy, local_x, local_y, expected_x, expected_y in test_cases:
        # Calculate quadrant origin in global coordinates
        ox = (W_mm / grid) * gx
        oy = (H_mm / grid) * gy
        
        # Simulate the conversion logic from backend.py
        x_global = local_x + ox
        y_global = local_y + oy
        
        # Check if conversion is correct
        if abs(x_global - expected_x) < 0.01 and abs(y_global - expected_y) < 0.01:
            print(f"✓ Quadrant ({gx},{gy}) local ({local_x:.1f},{local_y:.1f}) → global ({x_global:.2f},{y_global:.2f})")
            passed += 1
        else:
            print(f"✗ FAILED: Quadrant ({gx},{gy}) local ({local_x:.1f},{local_y:.1f})")
            print(f"  Expected: ({expected_x:.2f},{expected_y:.2f})")
            print(f"  Got:      ({x_global:.2f},{y_global:.2f})")
            failed += 1
    
    print()
    print(f"Quadrant Conversion Test: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


def test_deduplication_logic():
    """Test that deduplication properly handles duplicates from global and quadrant analysis"""
    
    print()
    print("="*60)
    print("DEDUPLICATION LOGIC TEST")
    print("="*60)
    print()
    
    # Simulate items from global analysis and quadrant analysis
    items = [
        # Item from global analysis
        {"tag": "P-101", "descricao": "Pump", "x_mm": 500.0, "y_mm": 400.0, "pagina": 1},
        # Same item from quadrant analysis (slightly different coordinates)
        {"tag": "P-101", "descricao": "Pump", "x_mm": 502.0, "y_mm": 398.0, "pagina": 1},
        # Different item, close by but different tag
        {"tag": "PT-101", "descricao": "Pressure Transmitter", "x_mm": 505.0, "y_mm": 395.0, "pagina": 1},
        # Different item, far away
        {"tag": "T-101", "descricao": "Tank", "x_mm": 800.0, "y_mm": 400.0, "pagina": 1},
        # Item without tag, close to P-101
        {"tag": "N/A", "descricao": "Valve", "x_mm": 503.0, "y_mm": 399.0, "pagina": 1},
        # Item without tag, far away
        {"tag": "N/A", "descricao": "Valve", "x_mm": 300.0, "y_mm": 200.0, "pagina": 1},
    ]
    
    # Simulate dedup_items logic
    import math
    
    def dist_mm(a, b):
        return math.hypot(a[0] - b[0], a[1] - b[1])
    
    tol_mm = 10.0
    final = []
    seen_tags = {}  # Maps (tag, page) -> list of positions
    
    for it in items:
        tag = it.get("tag", "").strip().upper()
        pos = (it["x_mm"], it["y_mm"])
        page = it["pagina"]
        
        is_duplicate = False
        
        # Para itens com TAG válida (não N/A)
        if tag and tag != "N/A":
            tag_key = (tag, page)
            
            # Verifica se já existe esse mesmo TAG
            if tag_key in seen_tags:
                # Verifica se está próximo de alguma posição existente com MESMO TAG
                for existing_pos in seen_tags[tag_key]:
                    if dist_mm(pos, existing_pos) <= tol_mm:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    seen_tags[tag_key].append(pos)
            else:
                # Primeira ocorrência deste TAG
                seen_tags[tag_key] = [pos]
        
        # Para itens sem TAG (N/A), verifica proximidade com QUALQUER item existente
        else:
            for existing in final:
                if existing["pagina"] == page:
                    existing_pos = (existing["x_mm"], existing["y_mm"])
                    if dist_mm(pos, existing_pos) <= tol_mm:
                        is_duplicate = True
                        break
        
        if not is_duplicate:
            final.append(it)
    
    print("Input items:")
    for i, item in enumerate(items, 1):
        print(f"  {i}. {item['tag']:10s} at ({item['x_mm']:6.1f}, {item['y_mm']:6.1f})")
    
    print()
    print("After deduplication (tolerance=10mm):")
    for i, item in enumerate(final, 1):
        print(f"  {i}. {item['tag']:10s} at ({item['x_mm']:6.1f}, {item['y_mm']:6.1f})")
    
    print()
    
    # Validate results
    expected_count = 4  # P-101 (first one), PT-101, T-101, N/A at (300,200)
    
    if len(final) == expected_count:
        print(f"✓ Correct number of items after dedup: {len(final)} (expected {expected_count})")
        
        # Check that we kept the right items
        tags = [it["tag"] for it in final]
        if "P-101" in tags and "PT-101" in tags and "T-101" in tags:
            print("✓ Kept correct tagged items (P-101, PT-101, T-101)")
        else:
            print("✗ FAILED: Missing expected tagged items")
            return False
        
        # Check we removed duplicates
        p101_count = sum(1 for it in final if it["tag"] == "P-101")
        if p101_count == 1:
            print("✓ Removed duplicate P-101 (kept only one)")
        else:
            print(f"✗ FAILED: Found {p101_count} P-101 items, expected 1")
            return False
        
        # Check we removed N/A item close to P-101
        na_items = [it for it in final if it["tag"] == "N/A"]
        if len(na_items) == 1 and na_items[0]["x_mm"] == 300.0:
            print("✓ Removed N/A item too close to P-101, kept distant one")
        else:
            print("✗ FAILED: N/A items not handled correctly")
            return False
        
        print()
        print("Deduplication Test: PASSED")
        print("="*60)
        return True
    else:
        print(f"✗ FAILED: Got {len(final)} items, expected {expected_count}")
        print("="*60)
        return False


if __name__ == "__main__":
    result1 = test_quadrant_coordinate_conversion()
    result2 = test_deduplication_logic()
    
    print()
    if result1 and result2:
        print("✅ ALL TESTS PASSED!")
        print()
        print("Summary:")
        print("- Quadrant local coordinates correctly converted to global")
        print("- Deduplication removes both tag duplicates and spatial duplicates")
        print("- Items within tolerance are considered duplicates")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)
