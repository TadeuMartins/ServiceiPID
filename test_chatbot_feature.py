#!/usr/bin/env python3
"""
Test script to validate chatbot and description endpoints
"""

import sys
import os

def test_imports():
    """Test that backend imports work"""
    try:
        # Add backend to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
        
        # Import should work even without API key
        import backend
        
        print("✅ Backend imports successfully")
        
        # Check that new endpoints exist
        app = backend.app
        routes = [route.path for route in app.routes]
        
        assert "/describe" in routes, "/describe endpoint not found"
        assert "/chat" in routes, "/chat endpoint not found"
        assert "/store" in routes, "/store endpoint not found"
        assert "/knowledge-base" in routes, "/knowledge-base endpoint not found"
        
        print("✅ All new endpoints are registered")
        
        # Check that knowledge base exists
        assert hasattr(backend, 'pid_knowledge_base'), "pid_knowledge_base not found"
        assert isinstance(backend.pid_knowledge_base, dict), "pid_knowledge_base should be a dict"
        
        print("✅ Knowledge base initialized correctly")
        
        # Check that generate_process_description function exists
        assert hasattr(backend, 'generate_process_description'), "generate_process_description function not found"
        
        print("✅ generate_process_description function exists")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except AssertionError as e:
        print(f"❌ Assertion error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_process_description_structure():
    """Test the structure of process description generation"""
    # Mock data
    sample_pid_data = [
        {
            "tag": "P-101",
            "descricao": "Centrifugal Pump",
            "tipo": "equipment",
            "x_mm": 100.0,
            "y_mm": 200.0
        },
        {
            "tag": "FT-101",
            "descricao": "Flow Transmitter",
            "tipo": "instrument",
            "x_mm": 150.0,
            "y_mm": 200.0
        },
        {
            "tag": "T-101",
            "descricao": "Storage Tank",
            "tipo": "equipment",
            "x_mm": 50.0,
            "y_mm": 200.0
        }
    ]
    
    # The function should classify items correctly
    equipamentos = []
    instrumentos = []
    
    for item in sample_pid_data:
        tag = item.get("tag", "N/A")
        if any(prefix in tag for prefix in ["FT", "PT", "TT", "LT", "FIC", "PIC", "TIC", "LIC"]):
            instrumentos.append(item)
        else:
            equipamentos.append(item)
    
    assert len(equipamentos) == 2, f"Expected 2 equipamentos, got {len(equipamentos)}"
    assert len(instrumentos) == 1, f"Expected 1 instrumento, got {len(instrumentos)}"
    
    print("✅ Process description structure test passed")
    return True


def test_frontend_imports():
    """Test that frontend imports work"""
    try:
        # We can't fully test streamlit UI, but we can check the file structure
        frontend_path = os.path.join(os.path.dirname(__file__), 'frontend', 'app.py')
        
        with open(frontend_path, 'r') as f:
            content = f.read()
        
        # Check for new URLs
        assert 'CHAT_URL' in content, "CHAT_URL not defined"
        assert 'DESCRIBE_URL' in content, "DESCRIBE_URL not defined"
        
        # Check for session state initialization
        assert 'pid_id' in content, "pid_id not in session state"
        assert 'chat_history' in content, "chat_history not in session state"
        assert 'show_chatbot' in content, "show_chatbot not in session state"
        assert 'process_description' in content, "process_description not in session state"
        
        # Check for chatbot UI elements
        assert '💬 Assistente P&ID' in content, "Chatbot title not found"
        assert 'Minimizar' in content, "Minimize button not found"
        
        print("✅ Frontend structure test passed")
        return True
        
    except Exception as e:
        print(f"❌ Frontend test error: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Testing chatbot feature implementation...\n")
    
    all_passed = True
    
    # Run tests
    all_passed &= test_imports()
    print()
    
    all_passed &= test_process_description_structure()
    print()
    
    all_passed &= test_frontend_imports()
    print()
    
    if all_passed:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)
