#!/usr/bin/env python3
"""
Test that electrical diagrams always use A3 dimensions (420mm x 297mm)
regardless of actual PDF page dimensions.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend import get_electrical_diagram_dimensions


def test_electrical_dimensions_are_always_a3():
    """Test that electrical diagram dimensions are always A3 (420x297)"""
    print("\n=== Testing electrical diagram dimensions ===")
    
    # Get dimensions
    w_mm, h_mm = get_electrical_diagram_dimensions()
    
    # Should always be A3 landscape
    assert w_mm == 420.0, f"Width should be 420mm, got {w_mm}mm"
    assert h_mm == 297.0, f"Height should be 297mm, got {h_mm}mm"
    
    print(f"✅ Electrical diagrams use fixed A3 dimensions: {w_mm}mm x {h_mm}mm")


def test_prompts_exclude_terminals():
    """Test that electrical prompts exclude terminals/bornes"""
    print("\n=== Testing terminal exclusion in prompts ===")
    
    from backend import build_prompt, build_prompt_electrical_global, build_prompt_electrical_tile
    
    # Test main electrical prompt
    electrical_prompt = build_prompt(420.0, 297.0, scope="global", diagram_type="electrical")
    
    # Should mention exclusion of bornes
    assert "borne" in electrical_prompt.lower(), "Prompt should mention bornes exclusion"
    assert "desconsiderados" in electrical_prompt.lower() or "ignorar" in electrical_prompt.lower(), \
        "Prompt should state that bornes should be ignored"
    
    print("✅ Main electrical prompt excludes bornes")
    
    # Test global electrical prompt
    global_prompt = build_prompt_electrical_global(0, 3000, 2100, 420.0, 297.0)
    assert "terminal" in global_prompt.lower() or "borne" in global_prompt.lower(), \
        "Global prompt should mention terminal/borne exclusion"
    print("✅ Global electrical prompt excludes terminals")
    
    # Test tile electrical prompt
    tile_prompt = build_prompt_electrical_tile(0, 0, 0, 1536, 1536, 420.0, 297.0, 3000, 2100)
    assert "terminal" in tile_prompt.lower() or "borne" in tile_prompt.lower(), \
        "Tile prompt should mention terminal/borne exclusion"
    print("✅ Tile electrical prompt excludes terminals")


def test_terminal_filtering():
    """Test that terminals are filtered out during parsing"""
    print("\n=== Testing terminal filtering ===")
    
    from backend import parse_electrical_equips
    
    # Mock response with terminals and regular equipment
    mock_response = {
        "equipments": [
            {
                "type": "motor",
                "tag": "M-101",
                "descricao": "Motor trifásico",
                "bbox": {"x": 100, "y": 100, "w": 50, "h": 50},
                "confidence": 0.95,
                "partial": False
            },
            {
                "type": "terminal",
                "tag": "TB-001",
                "descricao": "Terminal de conexão",
                "bbox": {"x": 200, "y": 100, "w": 20, "h": 20},
                "confidence": 0.90,
                "partial": False
            },
            {
                "type": "terminal_block",
                "tag": "N/A",
                "descricao": "Borne de ligação",
                "bbox": {"x": 250, "y": 100, "w": 20, "h": 20},
                "confidence": 0.85,
                "partial": False
            },
            {
                "type": "breaker",
                "tag": "CB-101",
                "descricao": "Disjuntor trifásico",
                "bbox": {"x": 300, "y": 100, "w": 40, "h": 40},
                "confidence": 0.98,
                "partial": False
            }
        ]
    }
    
    # Parse equipment
    equipment = parse_electrical_equips(mock_response, page=0)
    
    # Should only have 2 items (motor and breaker, no terminals)
    assert len(equipment) == 2, f"Expected 2 equipment items, got {len(equipment)}"
    
    # Check that terminals were filtered out
    tags = [e.tag for e in equipment]
    assert "M-101" in tags, "Motor should be present"
    assert "CB-101" in tags, "Breaker should be present"
    assert "TB-001" not in tags, "Terminal should be filtered out"
    
    print(f"✅ Terminals filtered correctly: {len(equipment)}/4 items kept")
    print(f"   Kept: {', '.join(tags)}")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("ELECTRICAL A3 DIMENSIONS AND TERMINAL EXCLUSION TESTS")
    print("="*60)
    
    try:
        test_electrical_dimensions_are_always_a3()
        test_prompts_exclude_terminals()
        test_terminal_filtering()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nSummary:")
        print("- Electrical diagrams always use A3 dimensions (420mm x 297mm)")
        print("- Prompts exclude terminals/bornes from extraction")
        print("- Terminal filtering works correctly")
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
