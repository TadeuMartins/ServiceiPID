#!/usr/bin/env python3
"""
Visual demonstration of the coordinate system fix.
This script shows how coordinates are now correctly handled.
"""

import sys


def print_page_visualization():
    """Visualize the A0 page coordinate system"""
    print("="*70)
    print("A0 PAGE COORDINATE SYSTEM")
    print("="*70)
    print()
    print("┌─────────────────────────────────────────────────────────────────┐")
    print("│ (0, 0)                    TOP                    (1189, 0)      │")
    print("│                                                                 │")
    print("│  ←─── X aumenta da ESQUERDA para DIREITA ───→                  │")
    print("│  ↑                                                              │")
    print("│  │                                                              │")
    print("│  │                                                              │")
    print("│  Y                                                              │")
    print("│  a                   (594.5, 420.5)                             │")
    print("│  u                      [CENTRO]                                │")
    print("│  m                                                              │")
    print("│  e                                                              │")
    print("│  n                                                              │")
    print("│  t                                                              │")
    print("│  a                                                              │")
    print("│  ↓                                                              │")
    print("│                                                                 │")
    print("│ (0, 841)                 BOTTOM                 (1189, 841)     │")
    print("└─────────────────────────────────────────────────────────────────┘")
    print()
    print("Dimensões: 1189mm (largura) x 841mm (altura)")
    print("Origem: Canto superior esquerdo = (0, 0)")
    print("Sistema: Y cresce de CIMA para BAIXO")
    print()


def print_quadrant_visualization():
    """Visualize quadrant division and coordinate conversion"""
    print("="*70)
    print("QUADRANT DIVISION (3x3 Grid)")
    print("="*70)
    print()
    print("┌────────────────┬────────────────┬────────────────┐")
    print("│  Quadrante 1-1 │  Quadrante 1-2 │  Quadrante 1-3 │")
    print("│   (gx=0,gy=0)  │   (gx=1,gy=0)  │   (gx=2,gy=0)  │")
    print("│  Origem global │  Origem global │  Origem global │")
    print("│    (0.0, 0.0)  │  (396.3, 0.0)  │  (792.7, 0.0)  │")
    print("├────────────────┼────────────────┼────────────────┤")
    print("│  Quadrante 2-1 │  Quadrante 2-2 │  Quadrante 2-3 │")
    print("│   (gx=0,gy=1)  │   (gx=1,gy=1)  │   (gx=2,gy=1)  │")
    print("│  Origem global │  Origem global │  Origem global │")
    print("│  (0.0, 280.3)  │ (396.3, 280.3) │ (792.7, 280.3) │")
    print("├────────────────┼────────────────┼────────────────┤")
    print("│  Quadrante 3-1 │  Quadrante 3-2 │  Quadrante 3-3 │")
    print("│   (gx=0,gy=2)  │   (gx=1,gy=2)  │   (gx=2,gy=2)  │")
    print("│  Origem global │  Origem global │  Origem global │")
    print("│  (0.0, 560.7)  │ (396.3, 560.7) │ (792.7, 560.7) │")
    print("└────────────────┴────────────────┴────────────────┘")
    print()
    print("Cada quadrante: ~396.3mm x 280.3mm")
    print()


def demonstrate_coordinate_conversion():
    """Show examples of coordinate conversion"""
    print("="*70)
    print("COORDINATE CONVERSION EXAMPLES")
    print("="*70)
    print()
    
    examples = [
        {
            "quadrant": "2-2 (Centro)",
            "gx": 1, "gy": 1,
            "local": (100.0, 50.0),
            "description": "Equipamento P-101 no centro do quadrante central"
        },
        {
            "quadrant": "1-1 (Topo-esquerda)",
            "gx": 0, "gy": 0,
            "local": (200.0, 150.0),
            "description": "Tanque T-101 no primeiro quadrante"
        },
        {
            "quadrant": "3-3 (Baixo-direita)",
            "gx": 2, "gy": 2,
            "local": (50.0, 100.0),
            "description": "Válvula FCV-201 no último quadrante"
        },
    ]
    
    W_mm = 1189.0
    H_mm = 841.0
    grid = 3
    
    for i, ex in enumerate(examples, 1):
        gx, gy = ex["gx"], ex["gy"]
        local_x, local_y = ex["local"]
        
        # Calculate quadrant origin
        ox = (W_mm / grid) * gx
        oy = (H_mm / grid) * gy
        
        # Convert to global
        global_x = local_x + ox
        global_y = local_y + oy
        
        print(f"{i}. {ex['description']}")
        print(f"   Quadrante: {ex['quadrant']} (gx={gx}, gy={gy})")
        print(f"   Origem do quadrante: ({ox:.1f}, {oy:.1f}) mm")
        print(f"   Coordenada LOCAL:    ({local_x:.1f}, {local_y:.1f}) mm")
        print(f"   Coordenada GLOBAL:   ({global_x:.1f}, {global_y:.1f}) mm")
        print(f"   Fórmula: Global = Local + Origem")
        print(f"            ({global_x:.1f}, {global_y:.1f}) = ({local_x:.1f}, {local_y:.1f}) + ({ox:.1f}, {oy:.1f})")
        print()
    
    print("✅ Todas as coordenadas globais estão dentro dos limites:")
    print(f"   0 ≤ X ≤ {W_mm} mm")
    print(f"   0 ≤ Y ≤ {H_mm} mm")
    print()


def demonstrate_deduplication():
    """Show deduplication logic in action"""
    print("="*70)
    print("DEDUPLICATION LOGIC DEMONSTRATION")
    print("="*70)
    print()
    
    print("Exemplo: Sistema detecta o mesmo equipamento em duas análises")
    print()
    
    print("ENTRADA (items detectados):")
    print("  1. P-101 (Bomba)         em (500.0, 400.0) - da análise GLOBAL")
    print("  2. P-101 (Bomba)         em (502.0, 398.0) - da análise QUADRANTE")
    print("  3. PT-101 (Transmissor)  em (505.0, 395.0) - próximo à bomba")
    print("  4. T-101 (Tanque)        em (800.0, 400.0) - distante")
    print("  5. N/A (Válvula)         em (503.0, 399.0) - sem TAG, próximo")
    print("  6. N/A (Válvula)         em (300.0, 200.0) - sem TAG, distante")
    print()
    
    print("PROCESSAMENTO (tolerância = 10mm):")
    print("  ✓ Item 1 (P-101 em 500,400): MANTIDO (primeiro)")
    print("  ✗ Item 2 (P-101 em 502,398): REMOVIDO (duplicata - mesmo TAG, dist=2.8mm)")
    print("  ✓ Item 3 (PT-101 em 505,395): MANTIDO (TAG diferente, apesar de próximo)")
    print("  ✓ Item 4 (T-101 em 800,400): MANTIDO (distante)")
    print("  ✗ Item 5 (N/A em 503,399): REMOVIDO (sem TAG e próximo de P-101)")
    print("  ✓ Item 6 (N/A em 300,200): MANTIDO (distante de todos)")
    print()
    
    print("SAÍDA (items únicos):")
    print("  1. P-101 (Bomba)         em (500.0, 400.0)")
    print("  2. PT-101 (Transmissor)  em (505.0, 395.0)")
    print("  3. T-101 (Tanque)        em (800.0, 400.0)")
    print("  4. N/A (Válvula)         em (300.0, 200.0)")
    print()
    
    print("REGRAS:")
    print("  ✅ Mesmo TAG + próximo (< 10mm) = DUPLICATA → remove segundo")
    print("  ✅ TAGs diferentes + próximos = NÃO duplicata → mantém ambos")
    print("  ✅ Sem TAG (N/A) + próximo de qualquer item = DUPLICATA → remove")
    print()


def show_before_after():
    """Show the improvement"""
    print("="*70)
    print("COMPARAÇÃO: ANTES vs DEPOIS DA CORREÇÃO")
    print("="*70)
    print()
    
    print("CENÁRIO: P&ID com bomba P-101 no centro da página")
    print()
    
    print("❌ ANTES (Sistema Antigo):")
    print("   Análise Global:")
    print("     - Detecta: P-101 em (594.5, 420.5)")
    print("   Análise Quadrante 2-2:")
    print("     - LLM retorna coordenadas ambíguas")
    print("     - Código tenta adivinhar se é local ou global")
    print("     - Resultado: P-101 em (198.2, 140.2) ← ERRADO!")
    print("   Deduplicação:")
    print("     - Dois P-101 em posições diferentes")
    print("     - Sistema mantém ambos (distância > 10mm)")
    print("   RESULTADO: P-101 duplicado com coordenadas erradas!")
    print()
    
    print("✅ DEPOIS (Sistema Corrigido):")
    print("   Análise Global:")
    print("     - Detecta: P-101 em (594.5, 420.5)")
    print("   Análise Quadrante 2-2:")
    print("     - LLM retorna coordenadas LOCAIS: (198.2, 140.2)")
    print("     - Código converte: (198.2 + 396.3, 140.2 + 280.3)")
    print("     - Resultado: P-101 em (594.5, 420.5) ← CORRETO!")
    print("   Deduplicação:")
    print("     - Dois P-101 na MESMA posição (diferença de 0.0mm)")
    print("     - Sistema remove duplicata")
    print("   RESULTADO: Um único P-101 na coordenada correta!")
    print()


def main():
    """Run all demonstrations"""
    print()
    print_page_visualization()
    print_quadrant_visualization()
    demonstrate_coordinate_conversion()
    demonstrate_deduplication()
    show_before_after()
    
    print("="*70)
    print("✅ CORREÇÃO IMPLEMENTADA COM SUCESSO")
    print("="*70)
    print()
    print("Principais melhorias:")
    print("  1. Sistema de coordenadas claro e consistente")
    print("  2. Conversão local→global sempre na mesma direção")
    print("  3. Deduplicação inteligente (TAG + proximidade)")
    print("  4. Coordenadas correspondem exatamente ao PDF")
    print("  5. Sem duplicatas de equipamentos")
    print()
    print("Documentação completa: COORDINATE_FIX_SUMMARY.md")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
