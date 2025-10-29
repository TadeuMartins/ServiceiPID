#!/usr/bin/env python3
"""
Test to validate chatbot optimization:
- Ultra-complete description is generated ONCE
- Chatbot reads pre-generated description (doesn't regenerate)
"""

def test_description_generation_once():
    """Verify description is generated only once during analysis"""
    print("🧪 Teste: Descrição ultra-completa gerada apenas UMA VEZ")
    print("="*70)
    
    with open('backend/backend.py', 'r') as f:
        content = f.read()
    
    checks = {
        "Descrição gerada em /analyze": (
            'description = generate_process_description(all_items, ultra_complete=True)',
            'pid_knowledge_base[pid_id]["description"] = description'
        ),
        "Descrição gerada em /generate": (
            'description = generate_process_description(unique, ultra_complete=True)',
            'pid_knowledge_base[pid_id]["description"] = description'
        ),
        "PDF armazenado para modo vision": (
            '"pdf_data": data',
            '# Armazena PDF original para modo vision'
        ),
        "Modo híbrido configurável": (
            'CHATBOT_MODE = os.getenv("CHATBOT_MODE", "hybrid")',
            '# "hybrid" = decide automaticamente'
        ),
    }
    
    all_found = True
    for check, patterns in checks.items():
        found = all(pattern in content for pattern in patterns)
        status = "✅" if found else "❌"
        print(f"  {status} {check}")
        if not found:
            all_found = False
    
    return all_found


def test_describe_endpoint_optimization():
    """Verify /describe endpoint doesn't regenerate by default"""
    print("\n🧪 Teste: Endpoint /describe otimizado")
    print("="*70)
    
    with open('backend/backend.py', 'r') as f:
        content = f.read()
    
    checks = {
        "Parâmetro regenerate (padrão False)": 'regenerate: bool = Query(False',
        "Retorna descrição existente": 'description = pid_info.get("description", "")',
        "Só regenera se forçado": 'if regenerate or not description:',
        "Log ao retornar existente": 'Retornando descrição ultra-completa existente',
        "Log ao regenerar": "Regenerando' if regenerate else 'Gerando",
    }
    
    all_found = True
    for check, pattern in checks.items():
        found = pattern in content
        status = "✅" if found else "❌"
        print(f"  {status} {check}")
        if not found:
            all_found = False
    
    return all_found


def test_chatbot_text_mode_optimization():
    """Verify chatbot text mode uses pre-generated description"""
    print("\n🧪 Teste: Chatbot modo texto otimizado")
    print("="*70)
    
    with open('backend/backend.py', 'r') as f:
        content = f.read()
    
    # Find chat_with_text function - busca mais robusta
    chat_text_lines = []
    in_function = False
    for line in content.split('\n'):
        if 'async def chat_with_text' in line:
            in_function = True
        elif in_function and line.startswith('async def '):
            break
        elif in_function:
            chat_text_lines.append(line)
    
    text_mode_code = '\n'.join(chat_text_lines)
    
    checks = {
        "Usa descrição pré-gerada": 'description = pid_info.get("description"' in text_mode_code,
        "Não envia lista completa de equipamentos": 'for item in pid_data' not in text_mode_code,
        "Log indica uso de descrição pré-gerada": 'pré-gerada' in text_mode_code,
        "Fallback gera se não existir": 'generate_process_description' in text_mode_code,
        "Docstring menciona ultra-completa": 'ultra-completa' in text_mode_code,
    }
    
    all_found = True
    for check, condition in checks.items():
        status = "✅" if condition else "❌"
        print(f"  {status} {check}")
        if not condition:
            all_found = False
    
    return all_found


def test_chatbot_vision_mode():
    """Verify vision mode uses PDF data"""
    print("\n🧪 Teste: Chatbot modo vision")
    print("="*70)
    
    with open('backend/backend.py', 'r') as f:
        content = f.read()
    
    # Find chat_with_vision function
    vision_start = content.find('async def chat_with_vision')
    vision_end = content.find('async def chat_with_text', vision_start)
    
    vision_code = content[vision_start:vision_end]
    
    checks = {
        "Acessa PDF armazenado": 'pdf_data = pid_info.get("pdf_data")',
        "Fallback para texto se sem PDF": 'return await chat_with_text',
        "Abre PDF com fitz": 'doc = fitz.open(stream=pdf_data',
        "Renderiza imagem": 'pix = page.get_pixmap',
        "Envia imagem para GPT-4": 'type": "image_url"',
        "Log modo vision": 'Usando MODO VISION',
    }
    
    all_found = True
    for check, pattern in checks.items():
        found = pattern in vision_code
        status = "✅" if found else "❌"
        print(f"  {status} {check}")
        if not found:
            all_found = False
    
    return all_found


def test_hybrid_mode_logic():
    """Verify hybrid mode automatically detects question type"""
    print("\n🧪 Teste: Lógica de modo híbrido")
    print("="*70)
    
    with open('backend/backend.py', 'r') as f:
        content = f.read()
    
    checks = {
        "Função should_use_vision_mode": 'def should_use_vision_mode(question: str)',
        "Detecta palavras-chave visuais": 'vision_keywords = [',
        "Keywords: onde, posição": '"onde", "posição"' in content or '"onde", "localiz"' in content,
        "Endpoint aceita parâmetro mode": 'mode: str = Query(None',
        "Decide automaticamente": 'use_vision = should_use_vision_mode(question)',
        "Log de detecção": 'detectou pergunta',
    }
    
    all_found = True
    for check, pattern in checks.items():
        if isinstance(pattern, bool):
            found = pattern
        else:
            found = pattern in content
        status = "✅" if found else "❌"
        print(f"  {status} {check}")
        if not found:
            all_found = False
    
    return all_found


def test_frontend_mode_selector():
    """Verify frontend has mode selector"""
    print("\n🧪 Teste: Frontend com seletor de modo")
    print("="*70)
    
    with open('frontend/app.py', 'r') as f:
        content = f.read()
    
    checks = {
        "Expander de configurações": '⚙️ Configurações Avançadas do Chatbot',
        "Radio button para modo": 'st.radio',
        "Opções: hybrid, text, vision": 'options=["hybrid", "text", "vision"]',
        "Envia modo no request": '"mode": selected_mode',
        "Timeout aumentado para vision": 'timeout=120',
        "Mostra modo usado": 'mode_used = entry.get("mode_used"',
        "Emoji para vision": '🖼️',
        "Exemplos de perguntas visuais": '📍 Localização de equipamento',
    }
    
    all_found = True
    for check, pattern in checks.items():
        found = pattern in content
        status = "✅" if found else "❌"
        print(f"  {status} {check}")
        if not found:
            all_found = False
    
    return all_found


def test_env_configuration():
    """Verify .env.example has CHATBOT_MODE"""
    print("\n🧪 Teste: Configuração em .env.example")
    print("="*70)
    
    with open('.env.example', 'r') as f:
        content = f.read()
    
    checks = {
        "Variável CHATBOT_MODE": 'CHATBOT_MODE=',
        "Modo hybrid explicado": '"hybrid": Decide automaticamente',
        "Modo text explicado": '"text": Usa descrição ultra-completa',
        "Modo vision explicado": '"vision": Envia imagem do P&ID',
        "Marcado como RECOMENDADO": 'RECOMENDADO',
    }
    
    all_found = True
    for check, pattern in checks.items():
        found = pattern in content
        status = "✅" if found else "❌"
        print(f"  {status} {check}")
        if not found:
            all_found = False
    
    return all_found


def generate_optimization_report():
    """Generate final optimization report"""
    print("\n" + "="*70)
    print("RELATÓRIO DE OTIMIZAÇÃO - CHATBOT P&ID")
    print("="*70)
    
    results = {
        "Descrição gerada uma única vez": test_description_generation_once(),
        "Endpoint /describe otimizado": test_describe_endpoint_optimization(),
        "Chatbot modo texto otimizado": test_chatbot_text_mode_optimization(),
        "Chatbot modo vision implementado": test_chatbot_vision_mode(),
        "Modo híbrido inteligente": test_hybrid_mode_logic(),
        "Frontend com seletor de modo": test_frontend_mode_selector(),
        "Configuração em .env": test_env_configuration(),
    }
    
    print("\n" + "="*70)
    print("RESUMO DOS RESULTADOS")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*70)
    if all_passed:
        print("✅ TODOS OS TESTES DE OTIMIZAÇÃO PASSARAM!")
        print("="*70)
        print("\n🎉 CHATBOT OTIMIZADO COM SUCESSO!")
        print("\n📊 Otimizações implementadas:")
        print("  1. ✅ Descrição ultra-completa gerada UMA ÚNICA VEZ durante análise/geração")
        print("  2. ✅ Chatbot modo texto LÊ descrição pré-gerada (não reprocessa)")
        print("  3. ✅ Chatbot modo vision envia imagem do P&ID para perguntas visuais")
        print("  4. ✅ Modo híbrido detecta automaticamente tipo de pergunta")
        print("  5. ✅ Endpoint /describe retorna descrição existente (não regenera)")
        print("  6. ✅ Frontend permite escolher modo manualmente")
        print("  7. ✅ Configuração via CHATBOT_MODE no .env")
        print("\n💡 Benefícios:")
        print("  • Economia de tokens (descrição gerada 1x ao invés de N vezes)")
        print("  • Respostas mais rápidas (usa descrição pré-processada)")
        print("  • Flexibilidade (pode escolher text, vision ou hybrid)")
        print("  • Melhor UX (modo híbrido escolhe o melhor para cada pergunta)")
        print("\n🔍 Comparação:")
        print("  ANTES: Descrição gerada a cada pergunta do chatbot")
        print("  DEPOIS: Descrição gerada 1x, chatbot sempre lê a mesma")
    else:
        print("❌ ALGUNS TESTES FALHARAM")
        print("="*70)
        failed = [name for name, passed in results.items() if not passed]
        print(f"\n❌ Testes que falharam ({len(failed)}):")
        for name in failed:
            print(f"  • {name}")
    
    return all_passed


def main():
    """Run optimization test suite"""
    print("🧪 SUITE DE TESTES - OTIMIZAÇÃO DO CHATBOT P&ID")
    print("="*70 + "\n")
    
    try:
        success = generate_optimization_report()
        return 0 if success else 1
    except Exception as e:
        print(f"\n❌ ERRO DURANTE TESTE: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
