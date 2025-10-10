#!/usr/bin/env python3
"""
Test script to verify the improved prompts
"""

import sys
import re

def extract_function(file_path, function_name):
    """Extract a function definition from a Python file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find the function definition
    pattern = rf'def {function_name}\([^)]*\).*?(?=\ndef |\nclass |\nif __name__|$)'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        return match.group(0)
    return None

# Extract the functions as strings to analyze
backend_path = '/home/runner/work/ServiceiPID/ServiceiPID/backend/backend.py'
build_prompt_code = extract_function(backend_path, 'build_prompt')
build_generation_prompt_code = extract_function(backend_path, 'build_generation_prompt')

def test_pdf_reading_prompt():
    """Test that the PDF reading prompt is more technical and complete"""
    print("Testing PDF Reading Prompt (build_prompt)...\n")
    
    if not build_prompt_code:
        print("✗ Could not extract build_prompt function")
        return False
    
    # Verify key technical elements are present
    checks = [
        ("ISA S5.1/S5.2/S5.3", "ISA standards mentioned"),
        ("COMOS", "COMOS compatibility mentioned"),
        ("coordenadas GLOBAIS", "Global coordinates emphasis"),
        ("ABSOLUTO e GLOBAL", "Absolute and global coordinate system"),
        ("Bombas", "Pumps mentioned in equipment list"),
        ("transmissor", "Transmitters mentioned"),
        ("Válvulas de controle", "Control valves mentioned"),
        ("nomenclatura ISA", "ISA nomenclature"),
        ("P-XXX", "Equipment tag examples"),
        ("PI (indicador), PT (transmissor)", "Pressure instrument examples"),
        ("FI, FT, FE", "Flow instrument examples"),
    ]
    
    passed = 0
    failed = 0
    
    for check_text, description in checks:
        if check_text in build_prompt_code:
            print(f"✓ {description}")
            passed += 1
        else:
            print(f"✗ FAILED: {description} - '{check_text}' not found")
            failed += 1
    
    # Test quadrant-specific instructions
    quadrant_checks = [
        ("X_global = X_local +", "Formula for converting local to global"),
        ("Origem do quadrante no sistema global", "Quadrant origin mentioned"),
    ]
    
    for check_text, description in quadrant_checks:
        if check_text in build_prompt_code:
            print(f"✓ {description}")
            passed += 1
        else:
            print(f"✗ FAILED: {description} - '{check_text}' not found")
            failed += 1
    
    print(f"\nPDF Reading Prompt: {passed} passed, {failed} failed")
    return failed == 0

def test_generation_prompt():
    """Test that the generation prompt is more technical and complete"""
    print("\n" + "="*60)
    print("Testing P&ID Generation Prompt (build_generation_prompt)...\n")
    
    if not build_generation_prompt_code:
        print("✗ Could not extract build_generation_prompt function")
        return False
    
    # Verify key technical elements are present
    checks = [
        ("engenheiro de processos sênior", "Senior process engineer role"),
        ("ISA S5.1, S5.2, S5.3", "ISA standards mentioned"),
        ("COMOS", "COMOS compatibility"),
        ("Bombas: P-101", "Pump tag examples"),
        ("Tanques de armazenamento", "Storage tanks"),
        ("Trocadores de calor", "Heat exchangers"),
        ("Reatores", "Reactors"),
        ("Torres", "Towers/Columns"),
        ("PT: Transmissores de pressão", "Pressure transmitters"),
        ("FT: Transmissores de vazão", "Flow transmitters"),
        ("LT: Transmissores de nível", "Level transmitters"),
        ("TT: Transmissores de temperatura", "Temperature transmitters"),
        ("FCV, PCV, LCV, TCV", "Control valves"),
        ("PSV, TSV, PRV", "Safety valves"),
        ("redundância", "Redundancy consideration"),
        ("COMPLETO e DETALHADO", "Emphasis on completeness"),
        ("MÍNIMO ESPERADO: 15-30", "Minimum equipment count guidance"),
        ("Zona de entrada", "Spatial distribution zones"),
    ]
    
    passed = 0
    failed = 0
    
    for check_text, description in checks:
        if check_text in build_generation_prompt_code:
            print(f"✓ {description}")
            passed += 1
        else:
            print(f"✗ FAILED: {description} - '{check_text}' not found")
            failed += 1
    
    print(f"\nGeneration Prompt: {passed} passed, {failed} failed")
    return failed == 0

def test_prompt_separation():
    """Verify that the two prompts are clearly different and serve different purposes"""
    print("\n" + "="*60)
    print("Testing Prompt Separation and Differences...\n")
    
    if not build_prompt_code or not build_generation_prompt_code:
        print("✗ Could not extract functions")
        return False
    
    # Unique elements in PDF reading prompt
    pdf_unique = [
        "Extrair TODOS os elementos",
        "ANÁLISE DE FLUXOGRAMA",
        "símbolos visíveis",
    ]
    
    # Unique elements in generation prompt
    gen_unique = [
        "Desenvolver um P&ID",
        "TAREFA: Desenvolver",
        "MÍNIMO ESPERADO",
    ]
    
    print("Checking PDF Reading Prompt has unique extraction language:")
    all_pdf_found = True
    for text in pdf_unique:
        if text in build_prompt_code:
            print(f"  ✓ '{text}' found in PDF prompt")
        else:
            print(f"  ✗ '{text}' NOT found in PDF prompt")
            all_pdf_found = False
    
    print("\nChecking Generation Prompt has unique creation language:")
    all_gen_found = True
    for text in gen_unique:
        if text in build_generation_prompt_code:
            print(f"  ✓ '{text}' found in Generation prompt")
        else:
            print(f"  ✗ '{text}' NOT found in Generation prompt")
            all_gen_found = False
    
    # Check they're not identical
    if build_prompt_code != build_generation_prompt_code:
        print("\n✓ Prompts are different (as expected)")
        return all_pdf_found and all_gen_found
    else:
        print("\n✗ FAILED: Prompts are identical!")
        return False

if __name__ == "__main__":
    print("="*60)
    print("TESTING IMPROVED LLM PROMPTS")
    print("="*60 + "\n")
    
    result1 = test_pdf_reading_prompt()
    result2 = test_generation_prompt()
    result3 = test_prompt_separation()
    
    print("\n" + "="*60)
    if result1 and result2 and result3:
        print("✅ ALL TESTS PASSED!")
        print("\nSummary:")
        print("- PDF reading prompt is more technical and comprehensive")
        print("- Generation prompt is more detailed with complete specifications")
        print("- Both prompts emphasize global coordinates for COMOS compatibility")
        print("- Prompts include extensive ISA standards and equipment types")
        print("- Clear separation between analysis (PDF) and generation tasks")
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)
    print("="*60)
