#!/usr/bin/env python3
"""
Test to verify that duplicate objects are removed from electrical diagrams.
This test validates the enhanced deduplication logic for electrical diagrams.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend import dedup_items


def test_electrical_duplicate_removal():
    """Test that electrical diagrams remove exact duplicates (same tag, same coordinates)"""
    print("Testing electrical diagram duplicate removal...\n")
    
    # Simulate items from global + quadrant analysis with duplicates
    # These are typical results where the same object is detected twice
    items = [
        {
            "tag": "CB-101",
            "descricao": "Disjuntor trifásico",
            "x_mm": 100.0,
            "y_mm": 200.0,
            "pagina": 1,
            "from": "N/A",
            "to": "M-201"
        },
        {
            "tag": "CB-101",  # Same tag
            "descricao": "Disjuntor trifásico",
            "x_mm": 100.0,  # Same coordinates (after rounding to 4mm)
            "y_mm": 200.0,
            "pagina": 1,
            "from": "N/A",
            "to": "M-201"
        },
        {
            "tag": "M-201",
            "descricao": "Motor trifásico",
            "x_mm": 300.0,
            "y_mm": 200.0,
            "pagina": 1,
            "from": "CB-101",
            "to": "N/A"
        },
        {
            "tag": "M-201",  # Duplicate motor
            "descricao": "Motor trifásico",
            "x_mm": 300.0,
            "y_mm": 200.0,
            "pagina": 1,
            "from": "CB-101",
            "to": "N/A"
        },
    ]
    
    print(f"Input: {len(items)} items (with duplicates)")
    for item in items:
        print(f"  - {item['tag']} at ({item['x_mm']}, {item['y_mm']})")
    
    # Run deduplication with electrical diagram mode
    unique = dedup_items(items, page_num=1, tol_mm=10.0, 
                        use_dynamic_tolerance=False, 
                        log_metadata=False,
                        is_electrical=True)
    
    print(f"\nOutput: {len(unique)} unique items")
    for item in unique:
        print(f"  - {item['tag']} at ({item['x_mm']}, {item['y_mm']})")
    
    # Verify duplicates were removed
    expected_count = 2  # CB-101 and M-201 (one each)
    actual_count = len(unique)
    
    if actual_count == expected_count:
        print(f"\n✅ PASS: Correctly removed duplicates")
        print(f"   Expected {expected_count} unique items, got {actual_count}")
        return True
    else:
        print(f"\n❌ FAIL: Duplicate removal failed")
        print(f"   Expected {expected_count} unique items, got {actual_count}")
        return False


def test_pid_duplicate_removal():
    """Test that P&ID diagrams still work correctly (no regression)"""
    print("\n" + "="*70)
    print("Testing P&ID duplicate removal (should work as before)...\n")
    
    items = [
        {
            "tag": "P-101",
            "descricao": "Bomba centrífuga",
            "x_mm": 150.5,
            "y_mm": 250.3,
            "pagina": 1,
            "from": "T-101",
            "to": "E-201"
        },
        {
            "tag": "P-101",  # Same tag, slightly different coords
            "descricao": "Bomba centrífuga",
            "x_mm": 152.1,  # Within 10mm tolerance
            "y_mm": 251.7,
            "pagina": 1,
            "from": "T-101",
            "to": "E-201"
        },
    ]
    
    print(f"Input: {len(items)} items")
    for item in items:
        print(f"  - {item['tag']} at ({item['x_mm']}, {item['y_mm']})")
    
    # Run deduplication WITHOUT electrical diagram mode
    unique = dedup_items(items, page_num=1, tol_mm=10.0, 
                        use_dynamic_tolerance=False,
                        log_metadata=False,
                        is_electrical=False)
    
    print(f"\nOutput: {len(unique)} unique items")
    for item in unique:
        print(f"  - {item['tag']} at ({item['x_mm']}, {item['y_mm']})")
    
    # Verify P&ID dedup still works
    if len(unique) == 1:
        print(f"\n✅ PASS: P&ID deduplication works correctly")
        return True
    else:
        print(f"\n❌ FAIL: P&ID deduplication broken")
        return False


def test_electrical_near_duplicates():
    """Test that electrical diagrams handle near-duplicates (within tolerance)"""
    print("\n" + "="*70)
    print("Testing electrical diagram near-duplicate removal...\n")
    
    items = [
        {
            "tag": "K-101",
            "descricao": "Contator trifásico",
            "x_mm": 100.0,
            "y_mm": 200.0,
            "pagina": 1,
            "from": "N/A",
            "to": "M-201"
        },
        {
            "tag": "K-101",  # Same tag, slightly different (within tolerance)
            "descricao": "Contator trifásico",
            "x_mm": 104.0,  # 4mm away (within 10mm tolerance)
            "y_mm": 200.0,
            "pagina": 1,
            "from": "N/A",
            "to": "M-201"
        },
    ]
    
    print(f"Input: {len(items)} items (near duplicates)")
    for item in items:
        print(f"  - {item['tag']} at ({item['x_mm']}, {item['y_mm']})")
    
    unique = dedup_items(items, page_num=1, tol_mm=10.0, 
                        use_dynamic_tolerance=False,
                        log_metadata=False,
                        is_electrical=True)
    
    print(f"\nOutput: {len(unique)} unique items")
    for item in unique:
        print(f"  - {item['tag']} at ({item['x_mm']}, {item['y_mm']})")
    
    # Should remove near-duplicate
    if len(unique) == 1:
        print(f"\n✅ PASS: Near-duplicates removed correctly")
        return True
    else:
        print(f"\n❌ FAIL: Near-duplicates not removed")
        return False


def test_electrical_different_tags():
    """Test that items with different tags are NOT removed as duplicates"""
    print("\n" + "="*70)
    print("Testing that different tags are kept (not duplicates)...\n")
    
    items = [
        {
            "tag": "CB-101",
            "descricao": "Disjuntor trifásico",
            "x_mm": 100.0,
            "y_mm": 200.0,
            "pagina": 1,
            "from": "N/A",
            "to": "M-201"
        },
        {
            "tag": "CB-102",  # Different tag
            "descricao": "Disjuntor trifásico",
            "x_mm": 100.0,  # Same coordinates
            "y_mm": 200.0,
            "pagina": 1,
            "from": "N/A",
            "to": "M-202"
        },
    ]
    
    print(f"Input: {len(items)} items (different tags, same position)")
    for item in items:
        print(f"  - {item['tag']} at ({item['x_mm']}, {item['y_mm']})")
    
    unique = dedup_items(items, page_num=1, tol_mm=10.0, 
                        use_dynamic_tolerance=False,
                        log_metadata=False,
                        is_electrical=True)
    
    print(f"\nOutput: {len(unique)} unique items")
    for item in unique:
        print(f"  - {item['tag']} at ({item['x_mm']}, {item['y_mm']})")
    
    # Should keep both (different tags)
    if len(unique) == 2:
        print(f"\n✅ PASS: Different tags kept correctly")
        return True
    else:
        print(f"\n❌ FAIL: Different tags incorrectly removed")
        return False


if __name__ == "__main__":
    print("="*70)
    print("TESTING ELECTRICAL DIAGRAM DUPLICATE REMOVAL")
    print("="*70 + "\n")
    
    try:
        result1 = test_electrical_duplicate_removal()
        result2 = test_pid_duplicate_removal()
        result3 = test_electrical_near_duplicates()
        result4 = test_electrical_different_tags()
        
        print("\n" + "="*70)
        if result1 and result2 and result3 and result4:
            print("✅ ALL TESTS PASSED!")
            print("\nSummary:")
            print("- Electrical diagrams: exact duplicates removed ✅")
            print("- Electrical diagrams: near-duplicates removed ✅")
            print("- Electrical diagrams: different tags preserved ✅")
            print("- P&ID diagrams: no regression ✅")
        else:
            print("❌ SOME TESTS FAILED")
            sys.exit(1)
        print("="*70)
    except Exception as e:
        print(f"❌ ERROR during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
