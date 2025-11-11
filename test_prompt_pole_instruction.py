#!/usr/bin/env python3
"""
Test to verify that the electrical diagram prompt includes instructions
to always specify pole count in equipment descriptions.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend import build_prompt


def test_prompt_contains_pole_instruction():
    """Test that electrical diagram prompt explicitly requires pole information"""
    print("Testing electrical diagram prompt for pole count instructions...\n")
    
    # Generate prompt for electrical diagram
    prompt = build_prompt(
        width_mm=420.0,
        height_mm=297.0,
        scope="global",
        diagram_type="electrical"
    )
    
    # Check for key instructions
    required_instructions = [
        "SEMPRE INCLUA O NÚMERO DE POLOS",  # Main instruction
        "1-pole, 2-pole ou 3-pole",  # Pole count variants
        "monopolar, bipolar, tripolar",  # Portuguese variants
        "monofásico, bifásico, trifásico",  # Phase variants
        "Exemplos CORRETOS",  # Examples section
        "Disjuntor trifásico",  # Correct example
        "Motor trifásico",  # Correct example
        "Exemplos INCORRETOS",  # Anti-patterns section
        "falta informação de polos",  # Explanation
    ]
    
    all_present = True
    missing = []
    
    for instruction in required_instructions:
        if instruction in prompt:
            print(f"  ✓ Found: '{instruction}'")
        else:
            print(f"  ✗ Missing: '{instruction}'")
            all_present = False
            missing.append(instruction)
    
    # Check that examples in JSON output include pole info
    json_examples = [
        '"descricao": "Disjuntor trifásico',
        '"descricao": "Motor trifásico',
        '"descricao": "Transformador de corrente trifásico',
    ]
    
    print("\nChecking JSON output examples...")
    for example in json_examples:
        if example in prompt:
            print(f"  ✓ Found example: {example}")
        else:
            print(f"  ✗ Missing example: {example}")
            all_present = False
            missing.append(example)
    
    print("\n" + "="*70)
    if all_present:
        print("✅ PASS: Prompt includes all required pole count instructions!")
        print("\nThe AI will be instructed to:")
        print("- Always include pole count (1-pole, 2-pole, 3-pole)")
        print("- Use Portuguese variants (monopolar, bipolar, tripolar)")
        print("- Include phase information (monofásico, bifásico, trifásico)")
        print("- Follow correct examples in descriptions")
        print("- Avoid incorrect patterns without pole information")
        return True
    else:
        print("❌ FAIL: Prompt is missing required instructions")
        print(f"\nMissing instructions:")
        for item in missing:
            print(f"  - {item}")
        return False


def test_pid_prompt_unchanged():
    """Test that P&ID prompts are not affected by changes"""
    print("\n" + "="*70)
    print("Testing P&ID prompt (should not mention poles)...\n")
    
    # Generate prompt for P&ID diagram
    prompt = build_prompt(
        width_mm=1189.0,
        height_mm=841.0,
        scope="global",
        diagram_type="pid"
    )
    
    # P&ID prompts should NOT mention poles
    pole_keywords = [
        "NÚMERO DE POLOS",
        "monopolar",
        "bipolar", 
        "tripolar",
        "1-pole",
        "2-pole",
        "3-pole"
    ]
    
    has_pole_keywords = False
    for keyword in pole_keywords:
        if keyword in prompt:
            print(f"  ✗ Unexpected keyword in P&ID prompt: '{keyword}'")
            has_pole_keywords = True
    
    if not has_pole_keywords:
        print("  ✓ P&ID prompt does not contain pole-related instructions")
        print("\n✅ PASS: P&ID prompts remain unchanged")
        return True
    else:
        print("\n❌ FAIL: P&ID prompt incorrectly contains pole instructions")
        return False


if __name__ == "__main__":
    print("="*70)
    print("TESTING PROMPT MODIFICATIONS FOR POLE COUNT")
    print("="*70 + "\n")
    
    try:
        result1 = test_prompt_contains_pole_instruction()
        result2 = test_pid_prompt_unchanged()
        
        print("\n" + "="*70)
        if result1 and result2:
            print("✅ ALL TESTS PASSED!")
            print("\nSummary:")
            print("- Electrical prompts now require pole count in descriptions")
            print("- P&ID prompts remain unchanged")
            print("- AI will generate better descriptions for system matching")
        else:
            print("❌ SOME TESTS FAILED")
            sys.exit(1)
        print("="*70)
    except Exception as e:
        print(f"❌ ERROR during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
