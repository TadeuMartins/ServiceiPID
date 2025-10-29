# 🔎 P&ID Digitalizer DS Brazil - Siemens

Este projeto é um **aplicativo web** para análise de diagramas P&ID usando **Azure OpenAI GPT-4 multimodal**.

## Funcionalidades

### Versão 3
- Visualização gráfica com sobreposição dos pontos na **imagem real do P&ID**.
- Título e identidade visual Siemens.
- Exportação em Excel e JSON.

### Versão 4
- **Geração de P&ID a partir de linguagem natural**: Crie diagramas P&ID completos apenas descrevendo o processo
- Interface com abas: "Analisar PDF" e "Gerar a partir de Prompt"
- Geração automática de equipamentos e instrumentos com coordenadas em folha A0 (1189mm x 841mm)
- Aplicação automática do matcher para identificação de SystemFullName
- Visualização 2D do layout gerado
- Exportação dos dados gerados (Excel/JSON)

### Versão 5 (Nova! 🎉)
- **🤖 Descrição Automática do Processo**: Após análise ou geração, a IA cria automaticamente uma descrição técnica completa incluindo:
  - Objetivo do Processo
  - Etapas do Processo em sequência
  - Função dos Equipamentos Principais
  - Instrumentação e Controle
  - Elementos de Segurança
  - Fluxo de Materiais
- **💬 Chatbot Inteligente Minimizável**: Assistente conversacional que responde perguntas específicas sobre o P&ID
  - Histórico de conversação
  - Perguntas sugeridas para facilitar o uso
  - Respostas contextuais baseadas no P&ID específico
  - Interface minimizável para não ocupar espaço
- **💾 Base de Conhecimento**: Armazenamento automático de todos os P&IDs processados para consultas futuras
- **🔍 Análise Contextual**: Capacidade de fazer perguntas sobre equipamentos, instrumentos, fluxo do processo, etc.

## Como usar

### Modo 1: Analisar PDF existente
1. Acesse a aba "📂 Analisar PDF"
2. Faça upload de um arquivo PDF de P&ID
3. Aguarde o processamento
4. Visualize e exporte os resultados

### Modo 2: Gerar P&ID a partir de prompt
1. Acesse a aba "🎨 Gerar a partir de Prompt"
2. Descreva o processo em linguagem natural
   - Exemplo: "Gere um P&ID completo de um processo de clinquerização"
   - Exemplo: "Crie um diagrama P&ID para um sistema de destilação de petróleo"
3. Clique em "🎨 Gerar P&ID"
4. Visualize a tabela gerada com equipamentos e instrumentos
5. Exporte os resultados (Excel/JSON)

### Modo 3: Interagir com o Chatbot (Novo! 🤖)
Após análise ou geração de um P&ID:
1. **Visualize a descrição automática** do processo (expandida automaticamente)
2. **Role até o final da página** para encontrar o chatbot minimizável
3. **Faça perguntas** sobre o P&ID específico:
   - "Quais são os principais equipamentos?"
   - "Como funciona o controle de temperatura?"
   - "Explique o fluxo do processo"
4. **Use os botões de exemplo** para perguntas comuns
5. **Visualize o histórico** de todas as suas perguntas e respostas
6. **Minimize o chatbot** quando não estiver usando

![Chatbot Feature](https://github.com/user-attachments/assets/d9222492-37ca-4681-9e12-59d2d4f489d5)

## Como rodar

### Pré-requisitos
1. **⚠️ IMPORTANTE: Crie o arquivo `.env` com sua chave da OpenAI**
   
   O arquivo `.env` **não existe no repositório** por segurança. Você precisa criá-lo a partir do template:
   
   **Linux/Mac:**
   ```bash
   cp .env.example .env
   ```
   
   **Windows (CMD):**
   ```cmd
   copy .env.example .env
   ```
   
   **Windows (PowerShell):**
   ```powershell
   Copy-Item .env.example .env
   ```
   
   Depois **edite o arquivo `.env`** que foi criado e adicione sua chave OpenAI:
   ```
   OPENAI_API_KEY=sua-chave-openai-aqui
   ```
   
   **Nota:** O arquivo `.env` será automaticamente carregado pela aplicação e não deve ser commitado no repositório (já está no `.gitignore`).

### Iniciando o backend
2. Instale dependências e rode o backend:
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn backend:app --reload --port 8000
   ```
   
   **⚠️ Problemas com a porta 8000 no Windows?**
   
   Se você receber o erro `WinError 10013` (porta bloqueada), o backend tentará automaticamente usar portas alternativas (8001, 8002, 8003, 8080, 5000). Alternativamente, você pode especificar uma porta manualmente:
   
   ```bash
   # Windows
   set PORT=9000
   uvicorn backend:app --reload --port 9000
   
   # Linux/Mac
   export PORT=9000
   uvicorn backend:app --reload --port 9000
   ```
   
   Ou simplesmente execute:
   ```bash
   python backend.py
   ```
   O script automaticamente encontrará uma porta disponível.
   
### Iniciando o frontend
3. Rode o frontend:
   ```bash
   cd frontend
   pip install -r requirements.txt
   streamlit run app.py
   ```
4. Acesse no navegador: [http://localhost:8501](http://localhost:8501)

## API Endpoints

### POST `/analyze`
Analisa um arquivo PDF de P&ID e extrai equipamentos/instrumentos.

**Parâmetros:**
- `file`: Upload do arquivo PDF
- `dpi`: Resolução (100-600, padrão: 400)
- `grid`: Grade de quadrantes (1-6, padrão: 3)
- `tol_mm`: Tolerância de deduplicação em mm (1.0-50.0, padrão: 10.0)

### POST `/generate`
Gera P&ID a partir de descrição em linguagem natural.

**Parâmetros:**
- `prompt`: Descrição do processo (texto)

**Exemplo:**
```bash
curl -X POST "http://localhost:8000/generate?prompt=gere%20um%20P%26ID%20de%20clinquerização"
```

### GET `/describe` (Novo! 🆕)
Gera descrição técnica completa de um P&ID armazenado.

**Parâmetros:**
- `pid_id`: ID do P&ID (gerado automaticamente após análise/geração)

**Retorna:**
```json
{
  "pid_id": "analyzed_20241011_172600",
  "description": "**Objetivo do Processo:**\nEste é um sistema de...",
  "equipment_count": 45,
  "timestamp": "2024-10-11T17:26:00"
}
```

### POST `/chat` (Novo! 🆕)
Chatbot que responde perguntas sobre um P&ID específico.

**Parâmetros:**
- `pid_id`: ID do P&ID
- `question`: Pergunta do usuário

**Exemplo:**
```bash
curl -X POST "http://localhost:8000/chat?pid_id=analyzed_20241011_172600&question=Quais%20são%20os%20principais%20equipamentos?"
```

**Retorna:**
```json
{
  "pid_id": "analyzed_20241011_172600",
  "question": "Quais são os principais equipamentos?",
  "answer": "Os principais equipamentos identificados são: P-101 (Bomba Centrífuga)..."
}
```

### POST `/store` (Novo! 🆕)
Armazena dados de P&ID na base de conhecimento.

**Parâmetros:**
- `pid_id`: ID único para o P&ID
- `data`: Lista de equipamentos/instrumentos (JSON)

### GET `/knowledge-base` (Novo! 🆕)
Lista todos os P&IDs armazenados na base de conhecimento.

**Retorna:**
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

## Solução de Problemas

### Erro WinError 10013 no Windows (porta bloqueada)

**Problema:** Ao tentar iniciar o backend, você recebe o erro:
```
ERROR: [WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions
```

**Causa:** No Windows, certas portas (incluindo 8000) podem estar reservadas ou bloqueadas pelo sistema, Hyper-V, ou outros serviços.

**Solução 1 - Automática:** Execute o backend usando Python diretamente:
```bash
cd backend
python backend.py
```
O script automaticamente tentará portas alternativas (8001, 8002, 8003, 8080, 5000) e usará a primeira disponível.

**Solução 2 - Manual:** Especifique uma porta diferente:
```bash
# Windows
set PORT=9000
uvicorn backend:app --reload --port 9000

# Linux/Mac
export PORT=9000
uvicorn backend:app --reload --port 9000
```

**Solução 3 - Liberar a porta 8000:** 
1. Verifique quais portas estão reservadas:
   ```cmd
   netsh interface ipv4 show excludedportrange protocol=tcp
   ```
2. Se 8000 estiver na lista, escolha uma porta fora desses ranges

### Erro de API Key da OpenAI

Se você receber erros relacionados à API key da OpenAI:

1. **Verifique se o arquivo `.env` existe** na raiz do projeto
   - ❌ **Se não existir**: Você precisa criá-lo! Execute:
     ```bash
     # Linux/Mac
     cp .env.example .env
     
     # Windows CMD
     copy .env.example .env
     
     # Windows PowerShell
     Copy-Item .env.example .env
     ```
   - ✅ **Se já existir**: Prossiga para o próximo passo

2. **Certifique-se de que a chave está correta** no arquivo `.env`:
   ```
   OPENAI_API_KEY=sua-chave-openai-aqui
   ```
   - Abra o arquivo `.env` com um editor de texto (Notepad, VSCode, etc.)
   - Substitua `sua-chave-openai-aqui` pela sua chave real da OpenAI
   - Salve o arquivo

3. **Reinicie o servidor** após criar/modificar o arquivo `.env`

**Lembre-se:** O arquivo `.env` NÃO existe no repositório por segurança. Você SEMPRE precisa criá-lo manualmente usando o template `.env.example`.

#### Verificando a Configuração do .env

Para verificar se o arquivo `.env` foi criado corretamente:

**Linux/Mac:**
```bash
# Verificar se o arquivo existe
ls -la .env

# Ver o conteúdo (CUIDADO: não compartilhe a saída!)
cat .env
```

**Windows (CMD):**
```cmd
# Verificar se o arquivo existe
dir .env

# Ver o conteúdo (CUIDADO: não compartilhe a saída!)
type .env
```

**Dicas importantes:**
- Certifique-se de que o arquivo está na **raiz do projeto** (mesma pasta que README.md)
- O nome deve ser exatamente `.env` (com o ponto no início)
- **NUNCA** compartilhe seu arquivo `.env` ou sua chave de API
- **NUNCA** faça commit do arquivo `.env` no git (já protegido pelo `.gitignore`)

O arquivo `.env` é carregado automaticamente pelo backend usando `python-dotenv`.

### Erro de Certificado SSL (Certificate Verify Failed)

**Problema:** Ao chamar a API da OpenAI, você recebe o erro:
```
SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate
```

**Causa:** Problemas com certificados SSL no Windows, geralmente devido a:
- Certificados corporativos/proxy
- Certificados SSL desatualizados
- Configuração de rede empresarial

**Solução Automática:** O backend agora detecta automaticamente erros SSL e tenta novamente sem verificação SSL. Você verá mensagens como:
```
⚠️ Erro SSL detectado: [SSL: CERTIFICATE_VERIFY_FAILED]...
🔄 Tentando novamente sem verificação SSL...
```

**Solução Manual (se necessário):** 
1. Atualize o pacote `certifi`:
   ```bash
   pip install --upgrade certifi
   ```

2. Em ambientes corporativos, você pode precisar adicionar certificados personalizados ao Python. Consulte seu administrador de rede.
