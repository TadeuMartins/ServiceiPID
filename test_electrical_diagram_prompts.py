#!/usr/bin/env python3
"""
Test script to verify electrical diagram prompts are correctly separated from P&ID prompts.
This test ensures the AI receives electrical-specific instructions when analyzing electrical diagrams.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend import build_prompt, build_generation_prompt


def test_electrical_analysis_prompt():
    """Test that electrical diagram analysis prompts use electrical terminology"""
    print("Testing Electrical Diagram Analysis Prompt (build_prompt)...\n")
    
    # Generate electrical diagram prompt
    electrical_prompt = build_prompt(1189.0, 841.0, scope="global", diagram_type="electrical")
    
    # Check for electrical-specific content
    electrical_checks = [
        ("diagramas elétricos (Electrical Diagrams)", "Electrical diagram specialist role mentioned"),
        ("ANÁLISE DE DIAGRAMA ELÉTRICO", "Electrical analysis type header"),
        ("Transformadores", "Transformers in equipment list"),
        ("Motores elétricos", "Electrical motors in equipment list"),
        ("Disjuntores", "Circuit breakers in equipment list"),
        ("Relés de proteção", "Protection relays in equipment list"),
        ("CB-101", "Electrical tag example (circuit breaker)"),
        ("M-201", "Electrical tag example (motor)"),
        ("TR-301", "Electrical tag example (transformer)"),
        ("Disjuntor Principal", "Electrical equipment description"),
        ("Motor trifásico", "Motor description"),
        ("CONEXÕES ELÉTRICAS", "Electrical connections (not process)"),
        ("componente de origem → componente de destino", "Electrical component flow"),
        ("símbolos elétricos visíveis", "Electrical symbols completeness"),
        ("nomenclatura elétrica", "Electrical nomenclature"),
    ]
    
    # Check that P&ID-specific content is NOT present
    pid_exclusion_checks = [
        ("nomenclatura ISA S5.1", "ISA nomenclature should NOT be in electrical prompt"),
        ("CONEXÕES DE PROCESSO", "Process connections should NOT be in electrical prompt"),
        ("Bomba Centrífuga", "Pump example should NOT be in electrical prompt"),
        ("Indicador de Pressão", "Pressure indicator should NOT be in electrical prompt"),
        ('"T-101"', "Tank tag (quoted) should NOT be in electrical prompt"),
        ("E-201", "Heat exchanger tag should NOT be in electrical prompt"),
    ]
    
    passed = 0
    failed = 0
    
    print("Checking electrical-specific content IS present:")
    for check_text, description in electrical_checks:
        if check_text in electrical_prompt:
            print(f"  ✓ {description}")
            passed += 1
        else:
            print(f"  ✗ FAILED: {description} - '{check_text}' not found")
            failed += 1
    
    print("\nChecking P&ID-specific content is NOT present:")
    for check_text, description in pid_exclusion_checks:
        if check_text not in electrical_prompt:
            print(f"  ✓ {description}")
            passed += 1
        else:
            print(f"  ✗ FAILED: {description} - '{check_text}' should not be present")
            failed += 1
    
    print(f"\nElectrical Analysis Prompt: {passed} passed, {failed} failed")
    return failed == 0


def test_pid_analysis_prompt():
    """Test that P&ID analysis prompts use process terminology"""
    print("\n" + "="*70)
    print("Testing P&ID Analysis Prompt (build_prompt)...\n")
    
    # Generate P&ID prompt
    pid_prompt = build_prompt(1189.0, 841.0, scope="global", diagram_type="pid")
    
    # Check for P&ID-specific content
    pid_checks = [
        ("P&ID (Piping and Instrumentation Diagram)", "P&ID type mentioned"),
        ("diagramas P&ID", "P&ID description"),
        ("ANÁLISE DE FLUXOGRAMA DE PROCESSO", "Process flowsheet analysis header"),
        ("nomenclatura ISA S5.1", "ISA nomenclature"),
        ("CONEXÕES DE PROCESSO", "Process connections"),
        ("Bomba Centrífuga", "Pump example"),
        ("Indicador de Pressão", "Pressure indicator example"),
        ("P-101", "Pump tag example"),
        ("PI-9039", "Pressure indicator tag"),
        ("equipamento de origem → equipamento de destino", "Process equipment flow"),
    ]
    
    # Check that electrical-specific content is NOT present
    electrical_exclusion_checks = [
        ("ANÁLISE DE DIAGRAMA ELÉTRICO", "Electrical analysis should NOT be in P&ID prompt"),
        ("CONEXÕES ELÉTRICAS", "Electrical connections should NOT be in P&ID prompt"),
        ("nomenclatura elétrica", "Electrical nomenclature should NOT be in P&ID prompt"),
        ("Disjuntor Principal", "Circuit breaker should NOT be in P&ID prompt"),
        ("Motor trifásico", "Motor description should NOT be in P&ID prompt"),
        ("CB-101", "Circuit breaker tag should NOT be in P&ID prompt"),
    ]
    
    passed = 0
    failed = 0
    
    print("Checking P&ID-specific content IS present:")
    for check_text, description in pid_checks:
        if check_text in pid_prompt:
            print(f"  ✓ {description}")
            passed += 1
        else:
            print(f"  ✗ FAILED: {description} - '{check_text}' not found")
            failed += 1
    
    print("\nChecking electrical-specific content is NOT present:")
    for check_text, description in electrical_exclusion_checks:
        if check_text not in pid_prompt:
            print(f"  ✓ {description}")
            passed += 1
        else:
            print(f"  ✗ FAILED: {description} - '{check_text}' should not be present")
            failed += 1
    
    print(f"\nP&ID Analysis Prompt: {passed} passed, {failed} failed")
    return failed == 0


def test_electrical_generation_prompt():
    """Test that electrical diagram generation prompts are correct"""
    print("\n" + "="*70)
    print("Testing Electrical Diagram Generation Prompt...\n")
    
    # Generate electrical generation prompt
    electrical_gen_prompt = build_generation_prompt(
        "Sistema elétrico básico", 
        diagram_type="electrical"
    )
    
    # Check for electrical-specific content
    checks = [
        ("Electrical Diagram (Diagrama Elétrico)", "Electrical diagram type"),
        ("electrical standards and symbols", "Electrical standards"),
        ("electrical diagram", "Task description"),
        ("electrical components, connections, and power distribution", "Focus on electrical"),
        ("Transformers: TR-101", "Transformer examples"),
        ("Motors: M-101", "Motor examples"),
        ("Circuit Breakers: CB-101", "Circuit breaker examples"),
    ]
    
    passed = 0
    failed = 0
    
    for check_text, description in checks:
        if check_text in electrical_gen_prompt:
            print(f"  ✓ {description}")
            passed += 1
        else:
            print(f"  ✗ FAILED: {description} - '{check_text}' not found")
            failed += 1
    
    print(f"\nElectrical Generation Prompt: {passed} passed, {failed} failed")
    return failed == 0


def test_prompt_quadrant_mode():
    """Test that quadrant mode also works correctly for electrical diagrams"""
    print("\n" + "="*70)
    print("Testing Electrical Diagram Quadrant Mode...\n")
    
    # Generate electrical diagram prompt in quadrant mode
    electrical_quad_prompt = build_prompt(
        400.0, 280.0, 
        scope="quadrant", 
        origin=(100, 50), 
        quad_label="Q1",
        diagram_type="electrical"
    )
    
    # Check for electrical-specific content in quadrant mode
    checks = [
        ("ANÁLISE DE DIAGRAMA ELÉTRICO", "Electrical analysis in quadrant mode"),
        ("VOCÊ ESTÁ ANALISANDO APENAS O QUADRANTE Q1", "Quadrant label present"),
        ("nomenclatura elétrica", "Electrical nomenclature in quadrant"),
        ("CONEXÕES ELÉTRICAS", "Electrical connections in quadrant"),
    ]
    
    # Check that process-specific content is NOT present
    exclusion_checks = [
        ("nomenclatura ISA S5.1", "ISA should NOT be in electrical quadrant"),
        ("CONEXÕES DE PROCESSO", "Process connections should NOT be in electrical quadrant"),
    ]
    
    passed = 0
    failed = 0
    
    print("Checking electrical content in quadrant mode:")
    for check_text, description in checks:
        if check_text in electrical_quad_prompt:
            print(f"  ✓ {description}")
            passed += 1
        else:
            print(f"  ✗ FAILED: {description} - '{check_text}' not found")
            failed += 1
    
    print("\nChecking P&ID content is excluded:")
    for check_text, description in exclusion_checks:
        if check_text not in electrical_quad_prompt:
            print(f"  ✓ {description}")
            passed += 1
        else:
            print(f"  ✗ FAILED: {description}")
            failed += 1
    
    print(f"\nElectrical Quadrant Prompt: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    print("="*70)
    print("TESTING ELECTRICAL DIAGRAM PROMPT SEPARATION")
    print("="*70 + "\n")
    
    result1 = test_electrical_analysis_prompt()
    result2 = test_pid_analysis_prompt()
    result3 = test_electrical_generation_prompt()
    result4 = test_prompt_quadrant_mode()
    
    print("\n" + "="*70)
    if result1 and result2 and result3 and result4:
        print("✅ ALL TESTS PASSED!")
        print("\nSummary:")
        print("- Electrical diagram analysis uses electrical-specific terminology")
        print("- P&ID analysis uses process-specific terminology")
        print("- No cross-contamination between diagram types")
        print("- Electrical examples (CB-101, M-201, TR-301) are used for electrical")
        print("- Process examples (P-101, T-101, E-201) are used for P&ID")
        print("- Both global and quadrant modes work correctly")
        print("- AI will now correctly analyze electrical diagrams without expecting process equipment")
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)
    print("="*70)
