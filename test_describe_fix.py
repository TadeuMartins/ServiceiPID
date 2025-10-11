#!/usr/bin/env python3
"""
Test to verify the /describe endpoint accepts GET requests
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_describe_endpoint_method():
    """Verify /describe endpoint is GET"""
    import backend
    
    app = backend.app
    routes = [route for route in app.routes]
    
    # Find the describe route
    describe_route = None
    for route in routes:
        if hasattr(route, 'path') and route.path == '/describe':
            describe_route = route
            break
    
    assert describe_route is not None, "/describe endpoint not found"
    assert 'GET' in describe_route.methods, f"/describe should accept GET, but accepts: {describe_route.methods}"
    assert 'POST' not in describe_route.methods, f"/describe should NOT accept POST, but accepts: {describe_route.methods}"
    
    print("✅ /describe endpoint correctly configured as GET")
    return True


if __name__ == "__main__":
    print("🧪 Testing /describe endpoint method fix...\n")
    
    try:
        test_describe_endpoint_method()
        print("\n✅ All tests passed! The 405 error should be fixed.")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
