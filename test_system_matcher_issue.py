"""
Test to reproduce the system matcher issue where different equipment types
are incorrectly matched to the same SystemFullName.
"""
import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from system_matcher import match_system_fullname

# Test cases from the problem statement
test_cases = [
    {
        "tag": "H003A",
        "descricao": "Ponto de conexão/cabo trifásico (lado de entrada do acionamento)",
        "tipo": "",
        "expected_different_from": "Motor protection switch, 3-pole"
    },
    {
        "tag": "NO-TAG4",
        "descricao": "Acionamento eletrônico de motor trifásico (VFD/soft-starter) (3-pole) - Alimentador C",
        "tipo": "",
        "expected_different_from": "Motor protection switch, 3-pole"
    },
    {
        "tag": "H003B",
        "descricao": "Ponto de conexão/cabo trifásico (saída do acionamento para o motor)",
        "tipo": "",
        "expected_different_from": "Motor protection switch, 3-pole"
    },
    {
        "tag": "ZMS300",
        "descricao": "Motor trifásico AC (3-pole) 75,0 cv",
        "tipo": "",
        "expected_different_from": "Motor protection switch, 3-pole"
    }
]

def test_different_equipment_different_matches():
    """Test that different equipment types get different SystemFullName matches."""
    print("Testing system matcher with different equipment types...")
    print("=" * 80)
    
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest case {i}:")
        print(f"  Tag: {test_case['tag']}")
        print(f"  Descrição: {test_case['descricao']}")
        
        result = match_system_fullname(
            tag=test_case['tag'],
            descricao=test_case['descricao'],
            tipo=test_case['tipo'],
            diagram_type="electrical"
        )
        
        print(f"  Matched SystemFullName: {result.get('SystemFullName', 'N/A')}")
        print(f"  Matched Description: {result.get('Descricao_ref', 'N/A')}")
        print(f"  Confidence: {result.get('Confiança', 0.0)}")
        
        results.append(result)
    
    print("\n" + "=" * 80)
    print("\nSUMMARY:")
    print("-" * 80)
    
    # Check if all results have the same SystemFullName
    system_full_names = [r.get('Descricao_ref', 'N/A') for r in results]
    unique_names = set(system_full_names)
    
    print(f"\nUnique SystemFullName descriptions matched: {len(unique_names)}")
    for name in unique_names:
        count = system_full_names.count(name)
        print(f"  - {name}: {count} occurrences")
    
    # Check if the issue is present
    issue_present = False
    motor_protection_count = sum(1 for name in system_full_names if "Motor protection switch" in name)
    
    if motor_protection_count >= 3:
        print(f"\n❌ ISSUE DETECTED: {motor_protection_count} different equipment types matched to 'Motor protection switch'")
        issue_present = True
    else:
        print(f"\n✅ PASS: Different equipment types matched to different SystemFullNames")
    
    return not issue_present

if __name__ == "__main__":
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set. Please set it in .env file")
        print("Skipping test...")
        sys.exit(0)
    
    try:
        passed = test_different_equipment_different_matches()
        sys.exit(0 if passed else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
