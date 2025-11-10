#!/usr/bin/env python3
"""
Test script to verify grid parameter validation for electrical diagrams.

For electrical diagrams, grid must be 1, 2, or 4 (multiple or divisible by 4).
For P&ID diagrams, grid can be any value from 1 to 6.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend import validate_grid_for_diagram_type
from fastapi import HTTPException


def test_electrical_grid_valid():
    """Test that valid grid values for electrical diagrams don't raise exceptions"""
    print("Testing Valid Grid Values for Electrical Diagrams...\n")
    
    valid_grids = [1, 2, 4]
    passed = 0
    failed = 0
    
    for grid in valid_grids:
        try:
            validate_grid_for_diagram_type(grid, "electrical")
            print(f"  ✓ Grid {grid} accepted for electrical diagram")
            passed += 1
        except HTTPException as e:
            print(f"  ✗ FAILED: Grid {grid} rejected for electrical diagram: {e.detail}")
            failed += 1
    
    print(f"\nValid Electrical Grid: {passed} passed, {failed} failed")
    return failed == 0


def test_electrical_grid_invalid():
    """Test that invalid grid values for electrical diagrams raise exceptions"""
    print("\n" + "="*70)
    print("Testing Invalid Grid Values for Electrical Diagrams...\n")
    
    invalid_grids = [3, 5, 6]
    passed = 0
    failed = 0
    
    for grid in invalid_grids:
        try:
            validate_grid_for_diagram_type(grid, "electrical")
            print(f"  ✗ FAILED: Grid {grid} should have been rejected for electrical diagram")
            failed += 1
        except HTTPException as e:
            print(f"  ✓ Grid {grid} correctly rejected for electrical diagram")
            print(f"     Error message: {e.detail}")
            passed += 1
    
    print(f"\nInvalid Electrical Grid: {passed} passed, {failed} failed")
    return failed == 0


def test_pid_grid_all_valid():
    """Test that P&ID diagrams accept all grid values from 1 to 6"""
    print("\n" + "="*70)
    print("Testing P&ID Grid Values (Should Accept 1-6)...\n")
    
    all_grids = [1, 2, 3, 4, 5, 6]
    passed = 0
    failed = 0
    
    for grid in all_grids:
        try:
            validate_grid_for_diagram_type(grid, "pid")
            print(f"  ✓ Grid {grid} accepted for P&ID diagram")
            passed += 1
        except HTTPException as e:
            print(f"  ✗ FAILED: Grid {grid} rejected for P&ID diagram: {e.detail}")
            failed += 1
    
    print(f"\nP&ID Grid Values: {passed} passed, {failed} failed")
    return failed == 0


def test_case_insensitive():
    """Test that diagram type is case-insensitive"""
    print("\n" + "="*70)
    print("Testing Case Insensitivity...\n")
    
    test_cases = [
        ("ELECTRICAL", 4, True),
        ("Electrical", 4, True),
        ("electrical", 4, True),
        ("ELECTRICAL", 3, False),
        ("PID", 5, True),
        ("Pid", 5, True),
        ("pid", 5, True),
    ]
    
    passed = 0
    failed = 0
    
    for diagram_type, grid, should_pass in test_cases:
        try:
            validate_grid_for_diagram_type(grid, diagram_type)
            if should_pass:
                print(f"  ✓ {diagram_type} with grid {grid} correctly accepted")
                passed += 1
            else:
                print(f"  ✗ FAILED: {diagram_type} with grid {grid} should have been rejected")
                failed += 1
        except HTTPException as e:
            if not should_pass:
                print(f"  ✓ {diagram_type} with grid {grid} correctly rejected")
                passed += 1
            else:
                print(f"  ✗ FAILED: {diagram_type} with grid {grid} should have been accepted: {e.detail}")
                failed += 1
    
    print(f"\nCase Insensitivity: {passed} passed, {failed} failed")
    return failed == 0


def test_error_message_quality():
    """Test that error messages are informative"""
    print("\n" + "="*70)
    print("Testing Error Message Quality...\n")
    
    passed = 0
    failed = 0
    
    try:
        validate_grid_for_diagram_type(3, "electrical")
        print(f"  ✗ FAILED: Should have raised exception for grid=3 on electrical")
        failed += 1
    except HTTPException as e:
        error_msg = e.detail
        
        # Check that error message is in Portuguese
        if "diagramas elétricos" in error_msg.lower():
            print(f"  ✓ Error message is in Portuguese")
            passed += 1
        else:
            print(f"  ✗ FAILED: Error message should be in Portuguese")
            failed += 1
        
        # Check that error message mentions valid values
        if "1, 2 ou 4" in error_msg or "1, 2, 4" in error_msg:
            print(f"  ✓ Error message mentions valid values (1, 2, 4)")
            passed += 1
        else:
            print(f"  ✗ FAILED: Error message should mention valid values")
            failed += 1
        
        # Check that error message mentions the invalid value provided
        if "3" in error_msg:
            print(f"  ✓ Error message includes the invalid value provided")
            passed += 1
        else:
            print(f"  ✗ FAILED: Error message should include the invalid value")
            failed += 1
        
        print(f"\n     Full error message: {error_msg}")
    
    print(f"\nError Message Quality: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    print("="*70)
    print("TESTING GRID VALIDATION FOR ELECTRICAL DIAGRAMS")
    print("="*70 + "\n")
    
    result1 = test_electrical_grid_valid()
    result2 = test_electrical_grid_invalid()
    result3 = test_pid_grid_all_valid()
    result4 = test_case_insensitive()
    result5 = test_error_message_quality()
    
    print("\n" + "="*70)
    if result1 and result2 and result3 and result4 and result5:
        print("✅ ALL TESTS PASSED!")
        print("\nSummary:")
        print("- Electrical diagrams only accept grid values: 1, 2, 4")
        print("- P&ID diagrams accept all grid values: 1, 2, 3, 4, 5, 6")
        print("- Diagram type checking is case-insensitive")
        print("- Error messages are clear and informative")
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)
    print("="*70)
