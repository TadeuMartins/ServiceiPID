#!/usr/bin/env python3
"""
Test script to verify NO-TAG assignment functionality
"""

import sys
from typing import List, Dict, Any


def assign_no_tag_identifiers(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Assign sequential NO-TAG identifiers to equipment without valid tags.
    Equipment with tag "N/A" will be renamed based on instrument type:
    - PT-notag1, PT-notag2 for Transmissor de Pressão
    - PI-notag1, PI-notag2 for Indicador de Pressão
    - etc.
    """
    # Mapping from description keywords to instrument prefixes
    instrument_type_mapping = {
        # Pressure instruments
        "transmissor de pressão": "PT",
        "pressure transmitter": "PT",
        "indicador de pressão": "PI",
        "pressure indicator": "PI",
        "chave de pressão alta": "PSH",
        "pressure switch high": "PSH",
        "chave de pressão baixa": "PSL",
        "pressure switch low": "PSL",
        
        # Temperature instruments
        "controlador indicativo de temperatura": "TIC",
        "temperature indicating controller": "TIC",
        "indicador de temperatura": "TI",
        "temperature indicator": "TI",
        "transmissor de temperatura": "TT",
        "temperature transmitter": "TT",
        
        # Level instruments
        "transmissor de nível": "LT",
        "level transmitter": "LT",
        "controlador indicação de nível": "LIC",
        "controlador de nível": "LIC",
        "level indicating controller": "LIC",
        "level controller": "LIC",
        
        # Flow instruments
        "indicador de vazão": "FI",
        "flow indicator": "FI",
        "transmissor de vazão": "FT",
        "flow transmitter": "FT",
        "controlador de vazão": "FIC",
        "flow indicating controller": "FIC",
        "flow controller": "FIC",
        "válvula de controle de vazão": "FV",
        "flow control valve": "FV",
    }
    
    # Track counters for each instrument prefix
    prefix_counters = {}
    
    for item in items:
        if item.get("tag") == "N/A":
            descricao = item.get("descricao", "").lower()
            
            # Detect instrument type from description
            prefix = None
            for keyword, instrument_prefix in instrument_type_mapping.items():
                if keyword in descricao:
                    prefix = instrument_prefix
                    break
            
            # If no specific instrument type is detected, use generic NO-TAG
            if prefix is None:
                prefix = "NO-TAG"
            
            # Get or initialize counter for this prefix
            if prefix not in prefix_counters:
                prefix_counters[prefix] = 1
            
            # Assign tag based on prefix
            if prefix == "NO-TAG":
                item["tag"] = f"NO-TAG{prefix_counters[prefix]}"
            else:
                item["tag"] = f"{prefix}-notag{prefix_counters[prefix]}"
            
            prefix_counters[prefix] += 1
    
    return items


def test_assign_no_tag_identifiers():
    """Test that N/A tags are replaced with sequential NO-TAG identifiers"""
    print("Testing assign_no_tag_identifiers...\n")
    
    test_cases = [
        {
            "name": "Single equipment without tag (generic)",
            "input": [
                {"tag": "N/A", "descricao": "Bomba"},
            ],
            "expected_tags": ["NO-TAG1"]
        },
        {
            "name": "Single instrument without tag (Pressure Transmitter)",
            "input": [
                {"tag": "N/A", "descricao": "Transmissor de Pressão"},
            ],
            "expected_tags": ["PT-notag1"]
        },
        {
            "name": "Single instrument without tag (Temperature Indicator)",
            "input": [
                {"tag": "N/A", "descricao": "Indicador de Temperatura"},
            ],
            "expected_tags": ["TI-notag1"]
        },
        {
            "name": "Multiple instruments without tags of same type",
            "input": [
                {"tag": "N/A", "descricao": "Transmissor de Pressão"},
                {"tag": "N/A", "descricao": "Transmissor de Pressão"},
                {"tag": "N/A", "descricao": "Transmissor de Pressão"},
            ],
            "expected_tags": ["PT-notag1", "PT-notag2", "PT-notag3"]
        },
        {
            "name": "Multiple instruments without tags of different types",
            "input": [
                {"tag": "N/A", "descricao": "Transmissor de Pressão"},
                {"tag": "N/A", "descricao": "Indicador de Temperatura"},
                {"tag": "N/A", "descricao": "Transmissor de Vazão"},
            ],
            "expected_tags": ["PT-notag1", "TI-notag1", "FT-notag1"]
        },
        {
            "name": "Mix of tagged and untagged equipment",
            "input": [
                {"tag": "P-101", "descricao": "Bomba Principal"},
                {"tag": "N/A", "descricao": "Indicador de Pressão"},
                {"tag": "V-201", "descricao": "Válvula"},
                {"tag": "N/A", "descricao": "Transmissor de Nível"},
                {"tag": "T-301", "descricao": "Torre"},
            ],
            "expected_tags": ["P-101", "PI-notag1", "V-201", "LT-notag1", "T-301"]
        },
        {
            "name": "No equipment without tags",
            "input": [
                {"tag": "P-101", "descricao": "Bomba"},
                {"tag": "V-201", "descricao": "Válvula"},
            ],
            "expected_tags": ["P-101", "V-201"]
        },
        {
            "name": "All instrument types",
            "input": [
                {"tag": "N/A", "descricao": "Transmissor de Pressão"},
                {"tag": "N/A", "descricao": "Indicador de Pressão"},
                {"tag": "N/A", "descricao": "Chave de pressão alta"},
                {"tag": "N/A", "descricao": "Chave de pressão baixa"},
                {"tag": "N/A", "descricao": "Controlador indicativo de temperatura"},
                {"tag": "N/A", "descricao": "Indicador de Temperatura"},
                {"tag": "N/A", "descricao": "Transmissor de Nível"},
                {"tag": "N/A", "descricao": "Controlador Indicação de Nível"},
                {"tag": "N/A", "descricao": "Indicador de Vazão"},
                {"tag": "N/A", "descricao": "Transmissor de Vazão"},
                {"tag": "N/A", "descricao": "Controlador de Vazão"},
                {"tag": "N/A", "descricao": "Válvula de Controle de Vazão"},
            ],
            "expected_tags": [
                "PT-notag1", "PI-notag1", "PSH-notag1", "PSL-notag1",
                "TIC-notag1", "TI-notag1", "LT-notag1", "LIC-notag1",
                "FI-notag1", "FT-notag1", "FIC-notag1", "FV-notag1"
            ]
        },
        {
            "name": "Multiple same type instruments",
            "input": [
                {"tag": "N/A", "descricao": "Indicador de Pressão"},
                {"tag": "N/A", "descricao": "Indicador de Pressão"},
                {"tag": "N/A", "descricao": "Indicador de Temperatura"},
                {"tag": "N/A", "descricao": "Indicador de Temperatura"},
                {"tag": "N/A", "descricao": "Indicador de Temperatura"},
            ],
            "expected_tags": ["PI-notag1", "PI-notag2", "TI-notag1", "TI-notag2", "TI-notag3"]
        },
    ]
    
    all_passed = True
    for test_case in test_cases:
        result = assign_no_tag_identifiers(test_case["input"])
        actual_tags = [item["tag"] for item in result]
        expected_tags = test_case["expected_tags"]
        
        if actual_tags == expected_tags:
            print(f"✓ {test_case['name']}: PASSED")
        else:
            print(f"✗ {test_case['name']}: FAILED")
            print(f"  Expected: {expected_tags}")
            print(f"  Got:      {actual_tags}")
            all_passed = False
    
    return all_passed


if __name__ == "__main__":
    print("=" * 60)
    print("NO-TAG Assignment Tests")
    print("=" * 60 + "\n")
    
    passed = test_assign_no_tag_identifiers()
    
    print("\n" + "=" * 60)
    if passed:
        print("✓ All tests PASSED!")
        sys.exit(0)
    else:
        print("✗ Some tests FAILED!")
        sys.exit(1)
