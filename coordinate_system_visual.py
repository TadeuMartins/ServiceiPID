"""
Visual demonstration of the coordinate system change
"""

print("""
═══════════════════════════════════════════════════════════════
SISTEMA DE COORDENADAS - FOLHA A0 (1189mm x 841mm)
═══════════════════════════════════════════════════════════════

ANTES (Sistema Antigo - INCORRETO):
┌─────────────────────────────────┐
│                                 │ Y = 841mm (topo)
│                                 │
│                                 │
│         FLUXO →                 │
│                                 │
│                                 │
└─────────────────────────────────┘ Y = 0mm (base)
(0,0)                       (1189,0)


AGORA (Sistema Correto - Top-Left Origin):
(0,0) ────────────────────── (1189,0)
│                                 │ Y = 0mm (topo) ⬆️
│                                 │
│                                 │
│         FLUXO →                 │
│                                 │
│                                 │
└─────────────────────────────────┘ Y = 841mm (base) ⬇️
(0,841)                     (1189,841)


CARACTERÍSTICAS DO NOVO SISTEMA:
═════════════════════════════════

✓ Origem: Topo Superior Esquerdo (0, 0)
✓ Eixo X: 0 (esquerda) → 1189mm (direita)
✓ Eixo Y: 0 (topo) → 841mm (base)
✓ Y cresce de CIMA para BAIXO (downward)


EXEMPLOS DE COORDENADAS:
════════════════════════

Equipamento no topo esquerdo:
  • x_mm: 100.0
  • y_mm: 50.0
  • Posição: próximo ao canto superior esquerdo

Equipamento no centro da página:
  • x_mm: 594.5  (metade de 1189)
  • y_mm: 420.5  (metade de 841)
  • Posição: exatamente no centro

Equipamento no canto inferior direito:
  • x_mm: 1100.0
  • y_mm: 800.0
  • Posição: próximo ao canto inferior direito


COMPATIBILIDADE COMOS:
══════════════════════

O sistema COMOS (Siemens) utiliza origem inferior esquerda.
Para manter compatibilidade, calculamos y_mm_cad:

  y_mm_cad = 841 - y_mm

Exemplos:
  • y_mm = 0 (topo)      → y_mm_cad = 841 (topo no COMOS)
  • y_mm = 420.5 (meio)  → y_mm_cad = 420.5 (meio no COMOS)
  • y_mm = 841 (base)    → y_mm_cad = 0 (base no COMOS)


ALINHAMENTO COM PyMuPDF (fitz):
════════════════════════════════

PyMuPDF/fitz também usa origem superior esquerda (0,0)
com Y crescente para baixo, portanto:

✓ Coordenadas do PDF → Coordenadas do sistema (DIRETO)
✓ Quadrantes calculados corretamente
✓ Visualização alinhada com a imagem


VISUALIZAÇÃO MATPLOTLIB:
═══════════════════════

Por padrão, matplotlib usa origem inferior esquerda.
Solução: ax.invert_yaxis() inverte o eixo Y para
mostrar (0,0) no topo esquerdo.

════════════════════════════════════════════════════════════════
""")
