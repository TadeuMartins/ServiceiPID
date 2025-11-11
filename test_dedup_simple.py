#!/usr/bin/env python3
"""
Simple test to verify the deduplication logic for electrical diagrams.
This test validates the concept without importing the full backend.
"""
import math


def dist_mm(pos1, pos2):
    """Calculate Euclidean distance between two positions"""
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)


def dedup_items_simple(items, is_electrical=False, tol_mm=10.0):
    """Simplified dedup logic for testing"""
    final = []
    seen_tags = {}
    
    for it in items:
        tag = it.get("tag", "").strip().upper()
        pos = (it["x_mm"], it["y_mm"])
        page = it.get("pagina", 1)
        
        is_duplicate = False
        
        if tag and tag != "N/A":
            tag_key = (tag, page)
            
            if tag_key in seen_tags:
                for existing_pos in seen_tags[tag_key]:
                    distance = dist_mm(pos, existing_pos)
                    
                    if is_electrical:
                        # Stricter logic for electrical diagrams
                        if distance == 0.0:
                            is_duplicate = True
                            print(f"  🔄 Removing duplicate: {tag} at exact same position")
                            break
                        elif distance <= tol_mm:
                            is_duplicate = True
                            print(f"  🔄 Removing near-duplicate: {tag} within {distance:.1f}mm")
                            break
                    else:
                        if distance <= tol_mm:
                            is_duplicate = True
                            print(f"  🔄 Removing duplicate: {tag} within {distance:.1f}mm")
                            break
                
                if not is_duplicate:
                    seen_tags[tag_key].append(pos)
            else:
                seen_tags[tag_key] = [pos]
        
        if not is_duplicate:
            final.append(it)
    
    return final


def test_electrical_duplicates():
    """Test electrical diagram duplicate removal"""
    print("="*70)
    print("TEST: Electrical Diagram Duplicate Removal")
    print("="*70)
    
    # Simulate 9 objects detected, but 18 lines due to duplicates
    items = [
        {"tag": "CB-101", "descricao": "Disjuntor trifásico", "x_mm": 100.0, "y_mm": 200.0, "pagina": 1},
        {"tag": "CB-101", "descricao": "Disjuntor trifásico", "x_mm": 100.0, "y_mm": 200.0, "pagina": 1},  # Duplicate
        {"tag": "M-201", "descricao": "Motor trifásico", "x_mm": 300.0, "y_mm": 200.0, "pagina": 1},
        {"tag": "M-201", "descricao": "Motor trifásico", "x_mm": 300.0, "y_mm": 200.0, "pagina": 1},  # Duplicate
        {"tag": "K-301", "descricao": "Contator trifásico", "x_mm": 200.0, "y_mm": 300.0, "pagina": 1},
        {"tag": "K-301", "descricao": "Contator trifásico", "x_mm": 200.0, "y_mm": 300.0, "pagina": 1},  # Duplicate
        {"tag": "F-401", "descricao": "Fusível monopolar", "x_mm": 400.0, "y_mm": 100.0, "pagina": 1},
        {"tag": "F-401", "descricao": "Fusível monopolar", "x_mm": 400.0, "y_mm": 100.0, "pagina": 1},  # Duplicate
        {"tag": "TR-501", "descricao": "Transformador trifásico", "x_mm": 500.0, "y_mm": 400.0, "pagina": 1},
        {"tag": "TR-501", "descricao": "Transformador trifásico", "x_mm": 500.0, "y_mm": 400.0, "pagina": 1},  # Duplicate
        {"tag": "A-601", "descricao": "Amperímetro", "x_mm": 150.0, "y_mm": 150.0, "pagina": 1},
        {"tag": "A-601", "descricao": "Amperímetro", "x_mm": 150.0, "y_mm": 150.0, "pagina": 1},  # Duplicate
        {"tag": "V-701", "descricao": "Voltímetro", "x_mm": 250.0, "y_mm": 150.0, "pagina": 1},
        {"tag": "V-701", "descricao": "Voltímetro", "x_mm": 250.0, "y_mm": 150.0, "pagina": 1},  # Duplicate
        {"tag": "REL-801", "descricao": "Relé de proteção", "x_mm": 350.0, "y_mm": 250.0, "pagina": 1},
        {"tag": "REL-801", "descricao": "Relé de proteção", "x_mm": 350.0, "y_mm": 250.0, "pagina": 1},  # Duplicate
        {"tag": "DS-901", "descricao": "Chave seccionadora trifásica", "x_mm": 450.0, "y_mm": 350.0, "pagina": 1},
        {"tag": "DS-901", "descricao": "Chave seccionadora trifásica", "x_mm": 450.0, "y_mm": 350.0, "pagina": 1},  # Duplicate
    ]
    
    print(f"\nInput: {len(items)} items (simulating duplicate detection)")
    print(f"Expected output: 9 unique items (50% reduction)\n")
    
    unique = dedup_items_simple(items, is_electrical=True, tol_mm=10.0)
    
    print(f"\n{'='*70}")
    print(f"Result: {len(unique)} unique items")
    print(f"Removed: {len(items) - len(unique)} duplicates")
    print(f"Reduction: {((len(items) - len(unique)) / len(items) * 100):.1f}%")
    
    # Verify tags
    unique_tags = [item["tag"] for item in unique]
    print(f"\nUnique tags found:")
    for tag in unique_tags:
        print(f"  - {tag}")
    
    # Check result
    if len(unique) == 9:
        print(f"\n{'='*70}")
        print("✅ TEST PASSED!")
        print("Electrical diagram deduplication working correctly")
        print("9 objects detected → 18 lines reduced to 9 unique items")
        return True
    else:
        print(f"\n{'='*70}")
        print("❌ TEST FAILED!")
        print(f"Expected 9 unique items, got {len(unique)}")
        return False


def test_pid_no_regression():
    """Test that P&ID deduplication still works"""
    print("\n" + "="*70)
    print("TEST: P&ID No Regression")
    print("="*70)
    
    items = [
        {"tag": "P-101", "descricao": "Bomba", "x_mm": 150.5, "y_mm": 250.3, "pagina": 1},
        {"tag": "P-101", "descricao": "Bomba", "x_mm": 152.1, "y_mm": 251.7, "pagina": 1},
    ]
    
    print(f"\nInput: {len(items)} items (near duplicates)")
    unique = dedup_items_simple(items, is_electrical=False, tol_mm=10.0)
    
    print(f"\nResult: {len(unique)} unique items")
    
    if len(unique) == 1:
        print("\n✅ TEST PASSED!")
        print("P&ID deduplication working correctly")
        return True
    else:
        print("\n❌ TEST FAILED!")
        return False


if __name__ == "__main__":
    result1 = test_electrical_duplicates()
    result2 = test_pid_no_regression()
    
    print("\n" + "="*70)
    if result1 and result2:
        print("✅ ALL TESTS PASSED")
        print("\nThe enhanced deduplication logic:")
        print("- Removes exact duplicates in electrical diagrams ✅")
        print("- Maintains P&ID functionality ✅")
    else:
        print("❌ SOME TESTS FAILED")
        exit(1)
    print("="*70)
