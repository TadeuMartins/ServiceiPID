#!/usr/bin/env python3
"""
Demonstration test showing how the improved prompt would prevent the error.
This simulates the before/after behavior of the LLM response.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend import ensure_json_list

# BEFORE: LLM returns descriptive text (the error case from the issue)
BEFORE_RESPONSE = """Creating an electrical diagram for a star-delta starter is a classic example for educational purposes. Below, I will describe how the diagram will be structured, along with the key components and their connections. Please note that this is a textual representation, and a physical drawing would typically be created using CAD software.

### Electrical Diagram for Star-Delta Starter

#### General Layout
- **Sheet Size**: A0 landscape (1189.0 mm x 841.0 mm)
- **Coordinate System**: X increases left to right..."""

# AFTER: LLM returns JSON as requested (expected behavior with improved prompt)
AFTER_RESPONSE = """[
  {
    "tag": "CB-101",
    "descricao": "Main Circuit Breaker",
    "x_mm": 150.5,
    "y_mm": 400.0,
    "from": "N/A",
    "to": "C-101"
  },
  {
    "tag": "C-101",
    "descricao": "Main Contactor",
    "x_mm": 250.5,
    "y_mm": 400.0,
    "from": "CB-101",
    "to": "C-102"
  },
  {
    "tag": "C-102",
    "descricao": "Star Contactor",
    "x_mm": 350.5,
    "y_mm": 350.0,
    "from": "C-101",
    "to": "M-101"
  },
  {
    "tag": "C-103",
    "descricao": "Delta Contactor",
    "x_mm": 350.5,
    "y_mm": 450.0,
    "from": "C-101",
    "to": "M-101"
  },
  {
    "tag": "M-101",
    "descricao": "Three-Phase Motor",
    "x_mm": 500.5,
    "y_mm": 400.0,
    "from": "C-102",
    "to": "N/A"
  },
  {
    "tag": "REL-101",
    "descricao": "Overload Relay",
    "x_mm": 420.5,
    "y_mm": 400.0,
    "from": "C-101",
    "to": "M-101"
  },
  {
    "tag": "A-101",
    "descricao": "Ammeter",
    "x_mm": 300.5,
    "y_mm": 300.0,
    "from": "C-101",
    "to": "N/A"
  }
]"""

print("=" * 70)
print("DEMONSTRATION: Before and After Prompt Improvement")
print("=" * 70)
print()

print("BEFORE (Original Error Case):")
print("-" * 70)
print("LLM Response (first 200 chars):")
print(BEFORE_RESPONSE[:200] + "...")
print()

items_before = ensure_json_list(BEFORE_RESPONSE)
if not items_before:
    print("❌ ERROR: LLM não retornou equipamentos válidos")
    print("   Reason: ensure_json_list returned empty list")
    print("   This would cause ValueError: 'LLM não retornou equipamentos válidos'")
else:
    print(f"✓ Found {len(items_before)} items")

print()
print("=" * 70)
print()

print("AFTER (With Improved Prompt):")
print("-" * 70)
print("LLM Response (first 200 chars):")
print(AFTER_RESPONSE[:200] + "...")
print()

items_after = ensure_json_list(AFTER_RESPONSE)
if not items_after:
    print("❌ ERROR: LLM não retornou equipamentos válidos")
else:
    print(f"✅ SUCCESS: Gerados {len(items_after)} equipamentos/instrumentos")
    print()
    print("Equipment list:")
    for item in items_after:
        print(f"  - {item['tag']}: {item['descricao']} at ({item['x_mm']}, {item['y_mm']})")

print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print()
print("The improved prompt with:")
print("  • CRITICAL OUTPUT REQUIREMENT at the top")
print("  • OUTPUT FORMAT - CRITICAL section")
print("  • Star-delta starter example for electrical diagrams")
print("  • CRITICAL REMINDERS section")
print("  • Multiple 'JSON-only' emphasis statements")
print()
print("...should prevent the LLM from returning descriptive text")
print("and instead ensure it returns a valid JSON array.")
print()
print("Before: 0 items extracted (ERROR)")
print(f"After:  {len(items_after)} items extracted (SUCCESS)")
print()
