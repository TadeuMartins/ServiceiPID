#!/usr/bin/env python3
"""
Script de teste para verificar a configuração da Groq API
"""

import os
import sys
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def test_groq_config():
    """Testa se a configuração da Groq está correta"""
    
    print("=" * 60)
    print("TESTE DE CONFIGURAÇÃO GROQ API")
    print("=" * 60)
    
    # Verificar variáveis de ambiente
    groq_key = os.getenv("GROQ_API_KEY")
    groq_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    primary_model = os.getenv("PRIMARY_MODEL", "gpt-oss-120b")
    fallback_model = os.getenv("FALLBACK_MODEL", "llama-3.3-70b-versatile")
    
    print("\n📋 Configuração Carregada:")
    print(f"  - GROQ_API_KEY: {'✅ Definida' if groq_key else '❌ Não definida'}")
    if groq_key:
        print(f"    Valor: {groq_key[:20]}... (primeiros 20 caracteres)")
    print(f"  - GROQ_BASE_URL: {groq_url}")
    print(f"  - PRIMARY_MODEL: {primary_model}")
    print(f"  - FALLBACK_MODEL: {fallback_model}")
    
    # Verificar se a chave tem o formato correto
    if groq_key:
        if groq_key.startswith("gsk_"):
            print("\n✅ Formato da chave: OK (inicia com 'gsk_')")
        else:
            print("\n⚠️  Aviso: A chave não inicia com 'gsk_' (formato Groq esperado)")
    else:
        print("\n❌ Erro: GROQ_API_KEY não definida no arquivo .env")
        print("\nPara corrigir:")
        print("1. Copie .env.example para .env")
        print("2. Edite .env e adicione sua chave Groq")
        return False
    
    # Testar importação do cliente
    try:
        from openai import OpenAI
        print("\n✅ Biblioteca OpenAI importada com sucesso")
        
        # Tentar criar cliente
        client = OpenAI(api_key=groq_key, base_url=groq_url)
        print("✅ Cliente Groq criado com sucesso")
        print(f"   Base URL: {client.base_url}")
        
        return True
    except ImportError as e:
        print(f"\n❌ Erro ao importar biblioteca: {e}")
        print("   Execute: pip install openai")
        return False
    except Exception as e:
        print(f"\n❌ Erro ao criar cliente: {e}")
        return False

if __name__ == "__main__":
    print("\n")
    success = test_groq_config()
    print("\n" + "=" * 60)
    if success:
        print("✅ TESTE CONCLUÍDO COM SUCESSO")
        print("\nO backend está configurado para usar Groq API")
        print(f"Para iniciar o servidor: cd backend && python backend.py")
    else:
        print("❌ TESTE FALHOU")
        print("\nVerifique as mensagens acima e corrija os problemas")
        sys.exit(1)
    print("=" * 60 + "\n")
