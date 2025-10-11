# 📝 Nova Funcionalidade: Descrição Automática e Chatbot P&ID

## 🎯 Resumo

Esta implementação adiciona duas funcionalidades principais ao P&ID Digitalizer:

1. **Geração Automática de Descrição Completa do Processo**: Após análise ou geração de um P&ID, a IA automaticamente cria uma descrição técnica detalhada do processo industrial.

2. **Chatbot Inteligente Minimizável**: Um assistente conversacional que responde perguntas específicas sobre o P&ID analisado/gerado.

## ✨ Funcionalidades Implementadas

### Backend (backend/backend.py)

#### 1. Base de Conhecimento (`pid_knowledge_base`)
- Dicionário em memória que armazena dados de P&IDs processados
- Cada entrada contém:
  - `data`: Lista de equipamentos e instrumentos
  - `timestamp`: Data/hora do processamento
  - `description`: Descrição completa gerada pela IA
  - `source`: Origem ("analyze" ou "generate")
  - Metadados adicionais (filename, original_prompt, etc.)

#### 2. Função `generate_process_description()`
- Analisa os equipamentos e instrumentos identificados
- Classifica automaticamente em equipamentos principais e instrumentação
- Gera prompt estruturado para a IA incluindo:
  - Objetivo do Processo
  - Etapas do Processo
  - Equipamentos Principais
  - Instrumentação e Controle
  - Elementos de Segurança
  - Fluxo de Materiais
- Usa GPT-4o para gerar descrição técnica detalhada

#### 3. Novos Endpoints API

##### POST `/describe`
**Parâmetros:**
- `pid_id`: ID do P&ID armazenado

**Retorna:**
```json
{
  "pid_id": "analyzed_20241011_172600",
  "description": "Descrição completa do processo...",
  "equipment_count": 45,
  "timestamp": "2024-10-11T17:26:00"
}
```

##### POST `/chat`
**Parâmetros:**
- `pid_id`: ID do P&ID
- `question`: Pergunta do usuário

**Retorna:**
```json
{
  "pid_id": "analyzed_20241011_172600",
  "question": "Quais são os principais equipamentos?",
  "answer": "Os principais equipamentos identificados são: P-101 (Bomba Centrífuga)..."
}
```

##### POST `/store`
**Parâmetros:**
- `pid_id`: ID único para o P&ID
- `data`: Lista de equipamentos/instrumentos

**Retorna:**
```json
{
  "status": "success",
  "pid_id": "custom_pid_001",
  "items_stored": 42,
  "message": "P&ID armazenado com sucesso..."
}
```

##### GET `/knowledge-base`
**Retorna lista de todos os P&IDs armazenados:**
```json
{
  "total_pids": 3,
  "pids": [
    {
      "pid_id": "analyzed_20241011_172600",
      "item_count": 45,
      "timestamp": "2024-10-11T17:26:00",
      "has_description": true
    }
  ]
}
```

#### 4. Integração Automática

**Endpoint `/analyze`:**
- Após processar o PDF, automaticamente:
  - Cria um `pid_id` único baseado em timestamp
  - Armazena todos os dados na base de conhecimento
  - Gera a descrição completa do processo
  - Retorna o `pid_id` junto com os resultados

**Endpoint `/generate`:**
- Após gerar o P&ID, automaticamente:
  - Cria um `pid_id` único baseado em timestamp
  - Armazena todos os dados gerados
  - Gera a descrição completa do processo
  - Retorna o `pid_id` junto com os resultados

### Frontend (frontend/app.py)

#### 1. Session State
Novas variáveis de estado:
- `pid_id`: ID do P&ID atual
- `chat_history`: Histórico de conversação
- `show_chatbot`: Controle de visibilidade do chatbot
- `process_description`: Descrição do processo

#### 2. URLs Adicionais
```python
CHAT_URL = "http://localhost:8000/chat"
DESCRIBE_URL = "http://localhost:8000/describe"
```

#### 3. Exibição da Descrição do Processo
- Após análise/geração, busca automaticamente a descrição
- Exibe em um expander "📝 Descrição Completa do Processo"
- Expandido por padrão para visualização imediata

#### 4. Chatbot Minimizável

**Localização:** Na parte inferior da página, após os resultados

**Componentes:**
- **Header:** 
  - Título: "💬 Assistente P&ID - Faça perguntas sobre este diagrama"
  - Botão "🔽 Minimizar" / "🔼 Expandir"
  - Exibe o `pid_id` atual

- **Histórico de Conversação:**
  - Mensagens do usuário (fundo azul)
  - Respostas do assistente (fundo ciano)
  - Scroll automático para novas mensagens

- **Input de Pergunta:**
  - Campo de texto para digitar pergunta
  - Botão "📤 Enviar"
  - Placeholder com exemplo de pergunta

- **Botões de Exemplo:**
  - "📋 Listar equipamentos principais"
  - "🎛️ Instrumentação do processo"
  - "🔄 Descrever fluxo"
  - Clique rápido para perguntas comuns

- **Limpar Histórico:**
  - Botão "🗑️ Limpar histórico de conversação"

## 🔄 Fluxo de Uso

### Cenário 1: Análise de PDF
1. Usuário faz upload de PDF P&ID
2. Backend processa e extrai equipamentos
3. Backend automaticamente:
   - Cria `pid_id` único
   - Armazena na base de conhecimento
   - Gera descrição do processo
4. Frontend exibe:
   - Descrição completa do processo (expandido)
   - Tabela de equipamentos
   - Chatbot minimizável na parte inferior
5. Usuário pode:
   - Ler a descrição técnica
   - Fazer perguntas no chatbot
   - Minimizar/expandir o chatbot

### Cenário 2: Geração a partir de Prompt
1. Usuário descreve o processo
2. Backend gera P&ID completo
3. Backend automaticamente:
   - Cria `pid_id` único
   - Armazena na base de conhecimento
   - Gera descrição do processo
4. Frontend exibe:
   - Descrição completa do processo (expandido)
   - Tabela e visualização 2D
   - Chatbot minimizável na parte inferior
5. Usuário pode:
   - Ler a descrição técnica
   - Fazer perguntas no chatbot
   - Exportar dados

### Cenário 3: Interação com Chatbot
1. Chatbot aparece automaticamente após análise/geração
2. Usuário pode:
   - Digitar pergunta customizada
   - Usar botões de exemplo
   - Ver histórico de conversação
3. Backend:
   - Consulta a base de conhecimento
   - Monta contexto com descrição + dados
   - Usa GPT-4o para responder
4. Resposta aparece no histórico
5. Usuário pode continuar perguntando

## 📊 Dados Técnicos

### Armazenamento
- **Tipo:** In-memory (dicionário Python)
- **Persistência:** Durante execução do servidor
- **Reinício:** Dados perdidos ao reiniciar backend

### Modelos de IA
- **Descrição:** GPT-4o (FALLBACK_MODEL)
- **Chatbot:** GPT-4o (FALLBACK_MODEL)
- **Temperatura Descrição:** 0.7 (criativo)
- **Temperatura Chatbot:** 0.5 (preciso)

### Limites
- **Equipamentos na descrição:** Até 20 equipamentos principais
- **Instrumentos na descrição:** Até 30 instrumentos
- **Equipamentos no chatbot:** Até 50 itens no contexto
- **Timeout:** 60 segundos (describe, chat)

## 🎨 Interface do Usuário

Ver arquivos de mockup:
- `chatbot_mockup.png`: Interface completa do chatbot
- `before_after_comparison.png`: Comparação antes/depois da implementação

## 🧪 Testes

Execute:
```bash
python test_chatbot_feature.py
```

Testes incluídos:
- ✅ Imports do backend
- ✅ Registro de endpoints
- ✅ Inicialização da base de conhecimento
- ✅ Função generate_process_description
- ✅ Estrutura do frontend
- ✅ URLs do chatbot

## 📝 Exemplo de Uso

### Exemplo de Descrição Gerada

```
**Objetivo do Processo:**
Este é um sistema de bombeamento e controle de fluidos com monitoramento 
de temperatura e pressão, típico de aplicações de transferência de líquidos 
em processos industriais.

**Etapas do Processo:**
1. Armazenamento em T-101 (Feed Tank)
2. Bombeamento através de P-101 (Centrifugal Pump)
3. Aquecimento em E-201 (Heat Exchanger)
4. Controle de temperatura e pressão contínuos
5. Descarga para processo downstream

**Equipamentos Principais:**
- T-101: Tanque de armazenamento de alimentação com indicador de nível
- P-101: Bomba centrífuga para transferência do fluido
- E-201: Trocador de calor para aquecimento do processo

**Instrumentação e Controle:**
- FT-101: Medição de vazão na descarga da bomba
- PT-102: Medição de pressão após bombeamento
- TT-201: Medição de temperatura após aquecimento
- LT-101: Medição de nível no tanque T-101

**Elementos de Segurança:**
- PSV-101: Válvula de segurança e alívio de pressão
- Alarmes de alta/baixa pressão
- Intertravamento de nível baixo

**Fluxo de Materiais:**
Fluido entra em T-101 → P-101 bombeia → E-201 aquece → Sai para processo
```

### Exemplo de Interação com Chatbot

**Usuário:** "Quais são os principais equipamentos?"

**Assistente:** "Os principais equipamentos identificados neste P&ID são:
- **P-101**: Bomba Centrífuga - responsável por transferir o fluido do tanque T-101 para o trocador de calor E-201
- **T-101**: Tanque de Armazenamento - armazena o fluido de alimentação antes do bombeamento
- **E-201**: Trocador de Calor - aquece o fluido antes de seguir para o processo downstream

Esses três equipamentos formam a espinha dorsal do sistema de transferência e aquecimento."

**Usuário:** "Como funciona o controle de temperatura?"

**Assistente:** "O controle de temperatura neste sistema é realizado através do instrumento **TT-201** (Temperature Transmitter), que está instalado após o trocador de calor E-201. 

Este transmissor monitora continuamente a temperatura do fluido aquecido. A temperatura medida é enviada para o sistema de controle, que pode ajustar automaticamente o aquecimento no E-201 para manter a temperatura desejada do processo.

É um controle em malha fechada que garante que o fluido saia do E-201 com a temperatura especificada para o processo."

## 🚀 Melhorias Futuras Possíveis

1. **Persistência:** Salvar base de conhecimento em banco de dados
2. **Busca Semântica:** Usar embeddings para melhorar respostas do chatbot
3. **Histórico Persistente:** Salvar conversações entre sessões
4. **Multi-P&ID:** Comparar múltiplos P&IDs na mesma conversação
5. **Export Chat:** Exportar conversação como PDF/TXT
6. **Sugestões Inteligentes:** IA sugere perguntas relevantes baseadas no P&ID
7. **Visualização no Chat:** Destacar equipamentos mencionados na visualização 2D
8. **Voz:** Integração com speech-to-text para perguntas por voz

## 📚 Documentação de Código

### Backend - Principais Funções

```python
def generate_process_description(pid_data: List[Dict[str, Any]]) -> str:
    """
    Gera descrição completa do P&ID baseada nos equipamentos identificados.
    
    Args:
        pid_data: Lista de dicionários com equipamentos/instrumentos
        
    Returns:
        String com descrição técnica formatada em markdown
    """
```

### Frontend - Session State

```python
st.session_state.pid_id          # ID único do P&ID atual
st.session_state.chat_history     # Lista de {question, answer}
st.session_state.show_chatbot     # Boolean para controle de visibilidade
st.session_state.process_description  # String com descrição completa
```

## ✅ Checklist de Implementação

- [x] Criar base de conhecimento (pid_knowledge_base)
- [x] Implementar generate_process_description()
- [x] Criar endpoint POST /describe
- [x] Criar endpoint POST /chat
- [x] Criar endpoint POST /store
- [x] Criar endpoint GET /knowledge-base
- [x] Integrar auto-store no /analyze
- [x] Integrar auto-store no /generate
- [x] Adicionar session state no frontend
- [x] Implementar exibição da descrição
- [x] Criar UI do chatbot minimizável
- [x] Implementar histórico de conversação
- [x] Adicionar botões de exemplo
- [x] Criar testes automatizados
- [x] Criar mockups visuais
- [x] Documentar funcionalidade

## 🎯 Conclusão

Esta implementação atende completamente aos requisitos da issue:
1. ✅ Função após leitura do P&ID que gera descrição completa
2. ✅ Base de dados para perguntas futuras sobre o P&ID
3. ✅ Chatbot minimizável que responde perguntas específicas

A solução é integrada, automática e não requer intervenção manual do usuário.
