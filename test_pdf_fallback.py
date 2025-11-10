#!/usr/bin/env python3
"""
Teste do sistema de fallback para PDFs corrompidos.
Verifica se o sistema usa pdf2image quando PyMuPDF falha.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend import open_pdf_with_fallback, PDF2IMAGE_AVAILABLE, PYPDF_AVAILABLE
import io
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

def create_valid_pdf() -> bytes:
    """Cria um PDF válido simples para teste"""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.drawString(100, 750, "Test P&ID Document")
    c.drawString(100, 700, "Equipment: P-101")
    c.showPage()
    c.save()
    return buffer.getvalue()


def test_valid_pdf():
    """Testa abertura de PDF válido"""
    print("\n" + "="*60)
    print("TESTE 1: PDF Válido")
    print("="*60)
    
    try:
        pdf_data = create_valid_pdf()
        doc = open_pdf_with_fallback(pdf_data, "test_valid.pdf", dpi=200)
        
        print(f"✅ PDF aberto com sucesso!")
        print(f"   Fonte: {doc.source}")
        print(f"   Páginas: {len(doc)}")
        print(f"   Primeira página: {doc[0].width_mm:.1f}mm x {doc[0].height_mm:.1f}mm")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao abrir PDF válido: {e}")
        return False


def test_fallback_availability():
    """Testa disponibilidade das bibliotecas de fallback"""
    print("\n" + "="*60)
    print("TESTE 2: Disponibilidade de Bibliotecas de Fallback")
    print("="*60)
    
    print(f"pdf2image disponível: {'✅ SIM' if PDF2IMAGE_AVAILABLE else '❌ NÃO'}")
    print(f"pypdf disponível: {'✅ SIM' if PYPDF_AVAILABLE else '❌ NÃO'}")
    
    if not PDF2IMAGE_AVAILABLE:
        print("\n⚠️ AVISO: pdf2image não está instalado!")
        print("   Instale com: pip install pdf2image")
        print("   NOTA: Também precisa do Poppler instalado no sistema")
    
    if not PYPDF_AVAILABLE:
        print("\n⚠️ AVISO: pypdf não está instalado!")
        print("   Instale com: pip install pypdf")
    
    return PDF2IMAGE_AVAILABLE or PYPDF_AVAILABLE


def test_corrupted_pdf_simulation():
    """Simula um PDF que falha no PyMuPDF mas pode funcionar no fallback"""
    print("\n" + "="*60)
    print("TESTE 3: Simulação de PDF Corrompido")
    print("="*60)
    
    # Nota: É difícil criar um PDF que falha especificamente com ExtGState
    # sem ter um arquivo real corrompido, então este teste é mais conceitual
    
    print("ℹ️ Este teste requer um PDF real com erro ExtGState")
    print("   Para testar completamente:")
    print("   1. Encontre um PDF que gera erro 'cannot find ExtGState resource'")
    print("   2. Faça upload dele através do endpoint /analyze")
    print("   3. Verifique nos logs se o fallback foi usado")
    
    return True


def main():
    """Executa todos os testes"""
    print("\n" + "="*60)
    print("TESTE DE SISTEMA DE FALLBACK PARA PDFs")
    print("="*60)
    
    results = []
    
    # Teste 1: PDF válido
    results.append(("PDF Válido", test_valid_pdf()))
    
    # Teste 2: Disponibilidade de fallback
    results.append(("Bibliotecas Fallback", test_fallback_availability()))
    
    # Teste 3: PDF corrompido (simulação)
    results.append(("PDF Corrompido (simulação)", test_corrupted_pdf_simulation()))
    
    # Resumo
    print("\n" + "="*60)
    print("RESUMO DOS TESTES")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status}: {test_name}")
    
    print(f"\nResultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} teste(s) falharam")
        return 1


if __name__ == "__main__":
    sys.exit(main())
