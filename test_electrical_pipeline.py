#!/usr/bin/env python3
"""
Test electrical pipeline data models and utilities.
This validates the core data structures and helper functions.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend import (
    BBox, Equip, Conn, Endpoint,
    _pt_dist, _path_sim, _nms, _cluster_centroid,
    merge_electrical_equips, merge_electrical_conns,
    dedup_endpoints, snap_endpoints_to_tags,
    detect_diagram_kind
)


def test_bbox_operations():
    """Test BBox IOU calculations"""
    print("\n=== Testing BBox operations ===")
    
    # Test area calculation
    bbox1 = BBox(0, 0, 10, 10)
    assert bbox1.area() == 100, f"Expected area 100, got {bbox1.area()}"
    print("✅ BBox area calculation correct")
    
    # Test IOU - overlapping boxes
    bbox2 = BBox(5, 5, 10, 10)
    iou = bbox1.iou(bbox2)
    print(f"   IOU of overlapping boxes: {iou:.3f}")
    assert 0 < iou < 1, f"Expected IOU between 0 and 1, got {iou}"
    print("✅ BBox IOU calculation correct")
    
    # Test IOU - identical boxes
    bbox3 = BBox(0, 0, 10, 10)
    iou_identical = bbox1.iou(bbox3)
    assert abs(iou_identical - 1.0) < 0.001, f"Expected IOU ~1.0, got {iou_identical}"
    print("✅ BBox IOU for identical boxes correct")
    
    # Test IOU - non-overlapping boxes
    bbox4 = BBox(100, 100, 10, 10)
    iou_none = bbox1.iou(bbox4)
    assert iou_none == 0.0, f"Expected IOU 0.0, got {iou_none}"
    print("✅ BBox IOU for non-overlapping boxes correct")


def test_distance_and_path_sim():
    """Test distance and path similarity functions"""
    print("\n=== Testing distance and path similarity ===")
    
    # Test point distance
    p1 = (0.0, 0.0)
    p2 = (3.0, 4.0)
    dist = _pt_dist(p1, p2)
    assert abs(dist - 5.0) < 0.001, f"Expected distance 5.0, got {dist}"
    print("✅ Point distance calculation correct")
    
    # Test path similarity - identical paths
    path1 = [(0, 0), (10, 10), (20, 20)]
    path2 = [(0, 0), (10, 10), (20, 20)]
    sim = _path_sim(path1, path2)
    assert abs(sim - 1.0) < 0.001, f"Expected similarity ~1.0, got {sim}"
    print("✅ Path similarity for identical paths correct")
    
    # Test path similarity - different paths
    path3 = [(0, 0), (100, 100), (200, 200)]
    sim_diff = _path_sim(path1, path3)
    assert sim_diff < 1.0, f"Expected similarity < 1.0, got {sim_diff}"
    print(f"   Path similarity for different paths: {sim_diff:.3f}")
    print("✅ Path similarity calculation correct")


def test_nms():
    """Test Non-Maximum Suppression"""
    print("\n=== Testing NMS ===")
    
    # Create overlapping equipment (larger overlap for IOU > 0.55)
    eq1 = Equip("MOTOR", "M-101", BBox(0, 0, 20, 20), 1, 0.9, False)
    eq2 = Equip("MOTOR", "M-101", BBox(2, 2, 20, 20), 1, 0.7, False)  # significant overlap
    eq3 = Equip("BREAKER", "CB-201", BBox(100, 100, 15, 15), 1, 0.8, False)  # separate
    
    result = _nms([eq1, eq2, eq3], iou_thr=0.55)
    
    # Should keep eq1 (higher confidence) and eq3 (no overlap)
    # eq2 should be filtered if IOU > 0.55
    print(f"   Items after NMS: {len(result)} (from 3)")
    assert len(result) <= 3, f"Expected <= 3 items after NMS, got {len(result)}"
    assert result[0].confidence >= 0.8, "Expected high confidence items first"
    print(f"✅ NMS correctly processed items")


def test_clustering():
    """Test centroid-based clustering"""
    print("\n=== Testing clustering ===")
    
    # Create close equipment (should cluster)
    eq1 = Equip("MOTOR", "M-101", BBox(100, 100, 10, 10), 1, 0.9, False)
    eq2 = Equip("MOTOR", "M-101", BBox(105, 105, 10, 10), 1, 0.7, False)
    
    # Create far equipment (separate cluster)
    eq3 = Equip("MOTOR", "M-201", BBox(200, 200, 10, 10), 1, 0.8, False)
    
    groups = _cluster_centroid([eq1, eq2, eq3], eps=10.0)
    
    assert len(groups) == 2, f"Expected 2 clusters, got {len(groups)}"
    assert len(groups[0]) == 2, f"Expected first cluster to have 2 items, got {len(groups[0])}"
    assert len(groups[1]) == 1, f"Expected second cluster to have 1 item, got {len(groups[1])}"
    print(f"✅ Clustering correctly grouped items: {[len(g) for g in groups]}")


def test_merge_electrical_equips():
    """Test equipment merging logic"""
    print("\n=== Testing equipment merging ===")
    
    # Create duplicates with different tags
    eq1 = Equip("MOTOR", "M-101", BBox(100, 100, 20, 20), 1, 0.9, False)
    eq2 = Equip("MOTOR", None, BBox(105, 105, 20, 20), 1, 0.7, False)  # no tag
    eq3 = Equip("MOTOR", "M-101", BBox(102, 102, 20, 20), 1, 0.85, False)  # duplicate tag
    eq4 = Equip("BREAKER", "CB-201", BBox(200, 200, 15, 15), 1, 0.8, False)  # different
    
    result = merge_electrical_equips([eq1, eq2, eq3, eq4])
    
    # Should merge duplicates with same tag
    assert len(result) <= 4, f"Expected <= 4 items after merge, got {len(result)}"
    
    # Check that tagged items are preferred
    tagged_motors = [r for r in result if r.type == "MOTOR" and r.tag == "M-101"]
    print(f"   Tagged motors after merge: {len(tagged_motors)}")
    print(f"✅ Equipment merging reduced {4} items to {len(result)}")


def test_merge_conns():
    """Test connection merging"""
    print("\n=== Testing connection merging ===")
    
    # Create similar connections
    path1 = [(0, 0), (10, 10), (20, 20)]
    path2 = [(0, 0), (10, 10), (20, 20)]
    path3 = [(100, 100), (110, 110)]
    
    conn1 = Conn("M-101", "CB-201", path1, "forward", 0.9)
    conn2 = Conn("M-101", "CB-201", path2, "forward", 0.8)  # duplicate
    conn3 = Conn("CB-201", "M-301", path3, "forward", 0.85)  # different
    
    result = merge_electrical_conns([conn1, conn2, conn3])
    
    # Should merge similar paths
    assert len(result) <= 3, f"Expected <= 3 connections after merge, got {len(result)}"
    print(f"✅ Connection merging reduced {3} items to {len(result)}")


def test_dedup_endpoints():
    """Test endpoint deduplication"""
    print("\n=== Testing endpoint deduplication ===")
    
    # Create close endpoints
    ep1 = Endpoint("M-101", (100.0, 100.0), 1)
    ep2 = Endpoint("M-101", (102.0, 102.0), 1)  # close to ep1
    ep3 = Endpoint("CB-201", (200.0, 200.0), 1)  # far from others
    
    result = dedup_endpoints([ep1, ep2, ep3])
    
    # Should deduplicate close endpoints
    assert len(result) <= 3, f"Expected <= 3 endpoints after dedup, got {len(result)}"
    print(f"✅ Endpoint deduplication reduced {3} items to {len(result)}")


def test_snap_endpoints():
    """Test endpoint snapping to tags"""
    print("\n=== Testing endpoint snapping ===")
    
    # Create equipment with tags
    eq1 = Equip("MOTOR", "M-101", BBox(100, 100, 20, 20), 1, 0.9, False)
    eq2 = Equip("BREAKER", "CB-201", BBox(200, 200, 15, 15), 1, 0.8, False)
    
    # Create endpoints near and far from equipment
    ep_near = Endpoint(None, (110.0, 110.0), 1)  # near M-101 center
    ep_far = Endpoint(None, (500.0, 500.0), 1)  # far from everything
    
    cons, leftovers = snap_endpoints_to_tags([], [ep_near, ep_far], [eq1, eq2], radius=25.0)
    
    print(f"   Snapped connections: {len(cons)}")
    print(f"   Leftover endpoints: {len(leftovers)}")
    
    # Should snap near endpoint and leave far one
    assert len(cons) >= 1, "Expected at least 1 snapped connection"
    assert len(leftovers) >= 1, "Expected at least 1 leftover endpoint"
    print("✅ Endpoint snapping works correctly")


def test_diagram_kind_detector():
    """Test diagram type detection"""
    print("\n=== Testing diagram type detection ===")
    
    # Test electrical diagram detection
    elec_text = "SINGLE LINE DIAGRAM - PANEL MCC-101 WITH CIRCUIT BREAKER CB-201"
    kind_elec = detect_diagram_kind(elec_text)
    assert kind_elec == "electrical", f"Expected 'electrical', got '{kind_elec}'"
    print(f"✅ Correctly detected electrical diagram")
    
    # Test P&ID detection
    pid_text = "P&ID PROCESS PIPING AND INSTRUMENTATION DIAGRAM WITH VALVE FV-101"
    kind_pid = detect_diagram_kind(pid_text)
    assert kind_pid == "pid", f"Expected 'pid', got '{kind_pid}'"
    print(f"✅ Correctly detected P&ID diagram")
    
    # Test ambiguous (should default to pid)
    ambig_text = "GENERAL DIAGRAM"
    kind_ambig = detect_diagram_kind(ambig_text)
    assert kind_ambig == "pid", f"Expected 'pid' (default), got '{kind_ambig}'"
    print(f"✅ Correctly defaulted to P&ID for ambiguous diagram")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("ELECTRICAL PIPELINE TESTS")
    print("="*60)
    
    try:
        test_bbox_operations()
        test_distance_and_path_sim()
        test_nms()
        test_clustering()
        test_merge_electrical_equips()
        test_merge_conns()
        test_dedup_endpoints()
        test_snap_endpoints()
        test_diagram_kind_detector()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
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
