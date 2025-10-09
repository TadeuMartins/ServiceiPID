#!/usr/bin/env python3
"""
Script to generate a visual mockup of the new UI feature
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import numpy as np

def create_ui_mockup():
    """Create a visual mockup of the new UI feature"""
    
    fig = plt.figure(figsize=(16, 10))
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    # Header
    header_box = FancyBboxPatch((2, 92), 96, 6, 
                                boxstyle="round,pad=0.1", 
                                edgecolor='#009999', 
                                facecolor='#e6f7f7',
                                linewidth=2)
    ax.add_patch(header_box)
    ax.text(50, 95, '🔎 P&ID Digitalizer DS Brazil - Siemens', 
            fontsize=20, fontweight='bold', ha='center', va='center',
            color='#009999')
    
    # Tab bar
    tab1_box = FancyBboxPatch((2, 86), 25, 4,
                              boxstyle="round,pad=0.1",
                              edgecolor='#009999',
                              facecolor='white',
                              linewidth=2)
    ax.add_patch(tab1_box)
    ax.text(14.5, 88, '📂 Analisar PDF', 
            fontsize=12, ha='center', va='center')
    
    tab2_box = FancyBboxPatch((28, 86), 35, 4,
                              boxstyle="round,pad=0.1",
                              edgecolor='#009999',
                              facecolor='#009999',
                              linewidth=2)
    ax.add_patch(tab2_box)
    ax.text(45.5, 88, '🎨 Gerar a partir de Prompt (NOVO!)', 
            fontsize=12, ha='center', va='center',
            color='white', fontweight='bold')
    
    # Main content area
    content_box = FancyBboxPatch((2, 10), 96, 74,
                                 boxstyle="round,pad=0.1",
                                 edgecolor='gray',
                                 facecolor='white',
                                 linewidth=1)
    ax.add_patch(content_box)
    
    # Title
    ax.text(50, 80, 'Gere um P&ID a partir de descrição em linguagem natural',
            fontsize=14, ha='center', va='center', fontweight='bold')
    
    # Examples box
    examples_box = FancyBboxPatch((5, 65), 90, 12,
                                  boxstyle="round,pad=0.3",
                                  edgecolor='#cccccc',
                                  facecolor='#f9f9f9',
                                  linewidth=1)
    ax.add_patch(examples_box)
    ax.text(50, 75, 'Exemplo de prompts:', fontsize=11, ha='center', va='center',
            fontweight='bold')
    ax.text(50, 72, '• "Gere um P&ID completo de um processo de clinquerização"',
            fontsize=10, ha='center', va='center', style='italic')
    ax.text(50, 69, '• "Crie um diagrama P&ID para um sistema de destilação de petróleo"',
            fontsize=10, ha='center', va='center', style='italic')
    ax.text(50, 66, '• "Gere P&ID de uma planta de tratamento de água"',
            fontsize=10, ha='center', va='center', style='italic')
    
    # Input field
    input_box = FancyBboxPatch((5, 52), 90, 10,
                               boxstyle="round,pad=0.3",
                               edgecolor='#999999',
                               facecolor='white',
                               linewidth=1.5)
    ax.add_patch(input_box)
    ax.text(7, 60, 'Descreva o processo:', fontsize=10, ha='left', va='center')
    ax.text(50, 56, 'Ex: gere um P&ID completo de um processo de clinquerização',
            fontsize=9, ha='center', va='center', color='#999999', style='italic')
    
    # Generate button
    button_box = FancyBboxPatch((35, 45), 30, 5,
                                boxstyle="round,pad=0.3",
                                edgecolor='#009999',
                                facecolor='#009999',
                                linewidth=2)
    ax.add_patch(button_box)
    ax.text(50, 47.5, '🎨 Gerar P&ID', 
            fontsize=14, ha='center', va='center', 
            color='white', fontweight='bold')
    
    # Results preview
    results_box = FancyBboxPatch((5, 12), 90, 30,
                                 boxstyle="round,pad=0.3",
                                 edgecolor='#cccccc',
                                 facecolor='#f5f5f5',
                                 linewidth=1)
    ax.add_patch(results_box)
    ax.text(50, 40, 'Resultados Gerados:', fontsize=12, ha='center', va='center',
            fontweight='bold')
    
    # Sample table
    table_data = [
        ['Tag', 'Descrição', 'Tipo', 'X (mm)', 'Y (mm)', 'SystemFullName'],
        ['P-101', 'Bomba Centrífuga', 'Bomba', '200.0', '400.0', 'Plant/Area/P-101'],
        ['T-101', 'Tanque de Armazenamento', 'Tanque', '100.0', '400.0', 'Plant/Area/T-101'],
        ['PI-101', 'Indicador de Pressão', 'Instrumento', '250.0', '380.0', 'Plant/Area/PI-101'],
        ['...', '...', '...', '...', '...', '...']
    ]
    
    y_pos = 36
    for i, row in enumerate(table_data):
        if i == 0:  # Header
            for j, cell in enumerate(row):
                ax.text(8 + j * 15, y_pos, cell, fontsize=8, ha='left', va='center',
                       fontweight='bold')
        else:
            for j, cell in enumerate(row):
                ax.text(8 + j * 15, y_pos - i * 3, cell, fontsize=7, ha='left', va='center')
    
    # Export buttons
    export_y = 15
    excel_box = FancyBboxPatch((10, export_y), 35, 3.5,
                               boxstyle="round,pad=0.2",
                               edgecolor='#009999',
                               facecolor='white',
                               linewidth=1.5)
    ax.add_patch(excel_box)
    ax.text(27.5, export_y + 1.75, '💾 Baixar Excel', 
            fontsize=10, ha='center', va='center')
    
    json_box = FancyBboxPatch((55, export_y), 35, 3.5,
                              boxstyle="round,pad=0.2",
                              edgecolor='#009999',
                              facecolor='white',
                              linewidth=1.5)
    ax.add_patch(json_box)
    ax.text(72.5, export_y + 1.75, '💾 Baixar JSON', 
            fontsize=10, ha='center', va='center')
    
    # A0 visualization note
    ax.text(50, 11, 'Equipamentos distribuídos em folha A0 (1189mm x 841mm)', 
            fontsize=9, ha='center', va='center', 
            color='#666666', style='italic')
    
    plt.title('Nova Funcionalidade: Geração de P&ID a partir de Prompt', 
              fontsize=16, fontweight='bold', pad=20)
    
    plt.tight_layout()
    return fig

if __name__ == "__main__":
    print("Creating UI mockup...")
    fig = create_ui_mockup()
    
    # Save the figure
    output_file = '/tmp/pid_generate_ui_mockup.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"✅ UI mockup saved to: {output_file}")
    
    print("\n📊 Feature Highlights:")
    print("  • New tab 'Gerar a partir de Prompt' in the UI")
    print("  • Text area for natural language process description")
    print("  • Generate button to create P&ID from description")
    print("  • Results displayed in table with coordinates")
    print("  • SystemFullName automatically matched for each item")
    print("  • Export to Excel and JSON supported")
    print("  • Equipment positioned on A0 sheet (1189mm x 841mm)")
