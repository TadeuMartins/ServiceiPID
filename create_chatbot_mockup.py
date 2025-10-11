#!/usr/bin/env python3
"""
Create a visual mockup showing the chatbot interface
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Rectangle
import matplotlib.lines as mlines

# Create figure
fig, ax = plt.subplots(figsize=(14, 10))
ax.set_xlim(0, 10)
ax.set_ylim(0, 12)
ax.axis('off')

# Title
ax.text(5, 11.5, 'P&ID Digitalizer - Novo Recurso: Chatbot Inteligente', 
        ha='center', va='top', fontsize=16, fontweight='bold', color='#009999')

# Main content area (simulating the existing content)
main_content = FancyBboxPatch((0.2, 6), 9.6, 5, 
                              boxstyle="round,pad=0.1", 
                              edgecolor='#cccccc', 
                              facecolor='#f8f9fa',
                              linewidth=2)
ax.add_patch(main_content)

ax.text(5, 10.5, '📊 Resumo da Análise / Geração', 
        ha='center', va='top', fontsize=12, fontweight='bold')

ax.text(5, 10, '📋 Tabela de Equipamentos e Instrumentos', 
        ha='center', va='center', fontsize=10, style='italic', color='#666')

ax.text(5, 9.2, '📝 NOVO: Descrição Completa do Processo', 
        ha='center', va='center', fontsize=10, fontweight='bold', 
        color='#007700', bbox=dict(boxstyle='round', facecolor='#ccffcc', alpha=0.8))

ax.text(5, 8.5, 'A IA gera automaticamente uma descrição técnica detalhada incluindo:', 
        ha='center', va='center', fontsize=9)

description_items = [
    '• Objetivo do Processo',
    '• Etapas do Processo em sequência',
    '• Função dos Equipamentos Principais',
    '• Instrumentação e Controle',
    '• Elementos de Segurança',
    '• Fluxo de Materiais'
]

y_pos = 7.8
for item in description_items:
    ax.text(3, y_pos, item, ha='left', va='center', fontsize=8, color='#333')
    y_pos -= 0.3

# Divider line
ax.plot([0.2, 9.8], [5.8, 5.8], 'k--', linewidth=1, alpha=0.3)

# Chatbot Section (minimizable)
chatbot_box = FancyBboxPatch((0.2, 0.5), 9.6, 5, 
                             boxstyle="round,pad=0.1", 
                             edgecolor='#009999', 
                             facecolor='#e6f7f7',
                             linewidth=3)
ax.add_patch(chatbot_box)

# Chatbot header
header_box = Rectangle((0.3, 5.1), 9.4, 0.35, 
                       facecolor='#009999', 
                       edgecolor='none')
ax.add_patch(header_box)

ax.text(0.5, 5.27, '💬 Assistente P&ID - Faça perguntas sobre este diagrama', 
        ha='left', va='center', fontsize=11, fontweight='bold', color='white')

ax.text(9.5, 5.27, '🔽 Minimizar', 
        ha='right', va='center', fontsize=9, color='white',
        bbox=dict(boxstyle='round', facecolor='#007777', alpha=0.8))

# P&ID ID
ax.text(0.5, 4.8, 'P&ID ID: analyzed_20241011_172600', 
        ha='left', va='center', fontsize=8, style='italic', color='#666',
        family='monospace')

# Chat history example
ax.text(0.5, 4.4, '📜 Histórico de Conversação', 
        ha='left', va='center', fontsize=10, fontweight='bold')

# User message 1
user_box1 = FancyBboxPatch((0.5, 3.8), 4.5, 0.4, 
                           boxstyle="round,pad=0.05", 
                           edgecolor='#0066cc', 
                           facecolor='#e6f2ff',
                           linewidth=1.5)
ax.add_patch(user_box1)
ax.text(0.6, 4.0, '👤 Usuário: Quais são os principais equipamentos?', 
        ha='left', va='center', fontsize=8, color='#0066cc', fontweight='bold')

# Assistant response 1
assistant_box1 = FancyBboxPatch((5.0, 3.2), 4.5, 0.5, 
                                boxstyle="round,pad=0.05", 
                                edgecolor='#009999', 
                                facecolor='#f0ffff',
                                linewidth=1.5)
ax.add_patch(assistant_box1)
ax.text(5.1, 3.6, '🤖 Assistente: Os principais equipamentos identificados são:', 
        ha='left', va='top', fontsize=8, color='#009999', fontweight='bold')
ax.text(5.2, 3.4, '• P-101: Bomba Centrífuga\n• T-101: Tanque de Armazenamento\n• E-201: Trocador de Calor', 
        ha='left', va='top', fontsize=7, color='#333')

# New question input area
question_box = FancyBboxPatch((0.5, 1.8), 7.5, 0.5, 
                              boxstyle="round,pad=0.05", 
                              edgecolor='#999', 
                              facecolor='white',
                              linewidth=1.5)
ax.add_patch(question_box)

ax.text(0.6, 2.05, '❓ Faça uma pergunta', 
        ha='left', va='center', fontsize=9, fontweight='bold')

ax.text(0.7, 1.9, 'Ex: Como funciona o controle de temperatura?', 
        ha='left', va='center', fontsize=8, style='italic', color='#999')

# Send button
send_button = FancyBboxPatch((8.2, 1.85), 1.3, 0.4, 
                             boxstyle="round,pad=0.05", 
                             edgecolor='#009999', 
                             facecolor='#009999',
                             linewidth=1.5)
ax.add_patch(send_button)
ax.text(8.85, 2.05, '📤 Enviar', 
        ha='center', va='center', fontsize=9, color='white', fontweight='bold')

# Example questions
ax.text(0.5, 1.5, '💡 Exemplos de perguntas:', 
        ha='left', va='center', fontsize=9, fontweight='bold')

example_buttons = [
    ('📋 Listar equipamentos principais', 0.5, 1.2),
    ('🎛️ Instrumentação do processo', 3.5, 1.2),
    ('🔄 Descrever fluxo', 6.5, 1.2)
]

for text, x, y in example_buttons:
    button = FancyBboxPatch((x, y-0.15), 2.8, 0.3, 
                           boxstyle="round,pad=0.05", 
                           edgecolor='#0066cc', 
                           facecolor='#e6f2ff',
                           linewidth=1)
    ax.add_patch(button)
    ax.text(x + 1.4, y, text, 
            ha='center', va='center', fontsize=7, color='#0066cc')

# Clear history button
clear_button = FancyBboxPatch((0.5, 0.6), 2.5, 0.3, 
                             boxstyle="round,pad=0.05", 
                             edgecolor='#cc0000', 
                             facecolor='#ffe6e6',
                             linewidth=1)
ax.add_patch(clear_button)
ax.text(1.75, 0.75, '🗑️ Limpar histórico de conversação', 
        ha='center', va='center', fontsize=7, color='#cc0000')

# Feature highlights
highlights = [
    '✨ Base de Conhecimento automática',
    '✨ Descrição completa do processo',
    '✨ Chatbot minimizável',
    '✨ Integrado com Análise e Geração'
]

y_highlight = 0.3
ax.text(5, y_highlight, ' | '.join(highlights), 
        ha='center', va='center', fontsize=8, 
        color='#007700', fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='#ccffcc', alpha=0.5))

plt.tight_layout()
plt.savefig('/home/runner/work/ServiceiPID/ServiceiPID/chatbot_mockup.png', 
            dpi=150, bbox_inches='tight', facecolor='white')
print("✅ Chatbot mockup created: chatbot_mockup.png")
plt.close()

# Create a before/after comparison
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

# BEFORE
ax1.set_xlim(0, 10)
ax1.set_ylim(0, 12)
ax1.axis('off')
ax1.text(5, 11, 'ANTES', ha='center', va='top', fontsize=18, fontweight='bold', color='#666')

before_box = FancyBboxPatch((0.5, 1), 9, 9, 
                           boxstyle="round,pad=0.1", 
                           edgecolor='#999', 
                           facecolor='#f5f5f5',
                           linewidth=2)
ax1.add_patch(before_box)

ax1.text(5, 9, '📂 Analisar PDF', ha='center', va='center', fontsize=14, fontweight='bold')
ax1.text(5, 8, '📋 Tabela de Equipamentos', ha='center', va='center', fontsize=12)
ax1.text(5, 7, '📥 Exportar Excel/JSON', ha='center', va='center', fontsize=12)
ax1.text(5, 5.5, '🎨 Gerar P&ID', ha='center', va='center', fontsize=14, fontweight='bold')
ax1.text(5, 4.5, '📋 Tabela de Equipamentos', ha='center', va='center', fontsize=12)
ax1.text(5, 3.5, '📐 Visualização 2D', ha='center', va='center', fontsize=12)

ax1.text(5, 1.8, '❌ Sem descrição do processo', ha='center', va='center', fontsize=10, color='red')
ax1.text(5, 1.3, '❌ Sem capacidade de Q&A', ha='center', va='center', fontsize=10, color='red')

# AFTER
ax2.set_xlim(0, 10)
ax2.set_ylim(0, 12)
ax2.axis('off')
ax2.text(5, 11, 'DEPOIS', ha='center', va='top', fontsize=18, fontweight='bold', color='#009999')

after_box = FancyBboxPatch((0.5, 1), 9, 9, 
                          boxstyle="round,pad=0.1", 
                          edgecolor='#009999', 
                          facecolor='#e6f7f7',
                          linewidth=3)
ax2.add_patch(after_box)

ax2.text(5, 9, '📂 Analisar PDF', ha='center', va='center', fontsize=14, fontweight='bold')
ax2.text(5, 8.3, '✨ Descrição Automática do Processo', ha='center', va='center', fontsize=11, 
         color='#007700', bbox=dict(boxstyle='round', facecolor='#ccffcc'))
ax2.text(5, 7.6, '📋 Tabela de Equipamentos', ha='center', va='center', fontsize=12)
ax2.text(5, 6.9, '📥 Exportar Excel/JSON', ha='center', va='center', fontsize=12)

ax2.text(5, 6, '🎨 Gerar P&ID', ha='center', va='center', fontsize=14, fontweight='bold')
ax2.text(5, 5.3, '✨ Descrição Automática do Processo', ha='center', va='center', fontsize=11, 
         color='#007700', bbox=dict(boxstyle='round', facecolor='#ccffcc'))
ax2.text(5, 4.6, '📋 Tabela de Equipamentos', ha='center', va='center', fontsize=12)
ax2.text(5, 3.9, '📐 Visualização 2D', ha='center', va='center', fontsize=12)

chatbot_highlight = FancyBboxPatch((1, 2.5), 8, 1, 
                                  boxstyle="round,pad=0.1", 
                                  edgecolor='#009999', 
                                  facecolor='#ffffff',
                                  linewidth=3)
ax2.add_patch(chatbot_highlight)

ax2.text(5, 3, '💬 Chatbot Inteligente Minimizável', ha='center', va='center', 
         fontsize=12, fontweight='bold', color='#009999')
ax2.text(5, 2.7, 'Responde perguntas sobre o P&ID específico', ha='center', va='center', 
         fontsize=10, style='italic', color='#666')

ax2.text(5, 1.8, '✅ Base de conhecimento automática', ha='center', va='center', fontsize=10, color='green')
ax2.text(5, 1.3, '✅ Análise contextual do processo', ha='center', va='center', fontsize=10, color='green')

plt.tight_layout()
plt.savefig('/home/runner/work/ServiceiPID/ServiceiPID/before_after_comparison.png', 
            dpi=150, bbox_inches='tight', facecolor='white')
print("✅ Before/after comparison created: before_after_comparison.png")
plt.close()
