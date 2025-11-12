# Siemens Electrical Diagram and P&ID Digitalizer

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

### Versão 5 (Nova! 🎉) - Versão 6 (Melhorada! 🔥)
- **🤖 Descrição Ultra-Completa do Processo**: Após análise ou geração, a IA cria automaticamente uma descrição técnica ULTRA-DETALHADA incluindo:
  - Objetivo do Processo
  - Inventário completo de TODOS os equipamentos com função e conexões
  - **NOVO:** Instrumentação detalhada por equipamento (qual instrumento mede pressão/temperatura/vazão de cada equipamento)
  - **NOVO:** Identificação de equipamentos reserva/backup (pares A/B, standby)
  - **NOVO:** Fluxo detalhado passo-a-passo usando TAGs (ex: T-101 → P-101A → FT-101 → E-201)
  - **NOVO:** Malhas de controle completas (sensor → controlador → atuador)
  - Elementos de Segurança com localização
  - Layout e distribuição espacial usando coordenadas
- **💬 Chatbot Inteligente com Múltiplos Modos**: Assistente conversacional otimizado
  - **NOVO:** Modo híbrido (detecta automaticamente tipo de pergunta)
  - **NOVO:** Modo texto (usa descrição ultra-completa - mais rápido e barato)
  - **NOVO:** Modo vision (analisa imagem do P&ID - mais preciso para perguntas visuais)
  - **NOVO:** Descrição gerada uma única vez (economia de tokens)
  - Histórico de conversação com indicação do modo usado
  - Perguntas sugeridas para facilitar o uso
  - Respostas contextuais baseadas no P&ID específico
  - Interface minimizável para não ocupar espaço
  - Configuração avançada para escolher modo manualmente
- **💾 Base de Conhecimento Otimizada**: Armazenamento automático com PDF original
  - Armazena descrição ultra-completa pré-processada
  - Armazena PDF original para modo vision
  - Acesso rápido sem reprocessamento
- **🔍 Análise Contextual Avançada**: Responde perguntas específicas como:
  - "Qual instrumento mede a pressão da bomba P-101?"
  - "Qual equipamento é reserva do P-101A?"
  - "Qual é o fluxo do material desde T-101 até E-201?"
  - "Onde está localizado o instrumento FT-101?"

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

### Modo 3: Interagir com o Chatbot (Melhorado! 🔥)
Após análise ou geração de um P&ID:
1. **Visualize a descrição ultra-completa** do processo (expandida automaticamente)
2. **Role até o final da página** para encontrar o chatbot minimizável
3. **Configure o modo do chatbot** (opcional - padrão é híbrido):
   - **Híbrido**: Detecta automaticamente (recomendado)
   - **Texto**: Sempre usa descrição ultra-completa
   - **Vision**: Sempre analisa imagem do P&ID
4. **Faça perguntas** sobre o P&ID específico:
   - "Quais são os principais equipamentos?"
   - "Qual instrumento mede a pressão da bomba P-101?"
   - "Qual equipamento é reserva do P-101A?"
   - "Onde está localizado o tanque T-101?" (modo vision)
   - "Qual é o fluxo do material desde T-101 até E-201?"
5. **Use os botões de exemplo** para perguntas comuns
6. **Visualize o histórico** de todas as suas perguntas e respostas (com indicação do modo usado)
7. **Minimize o chatbot** quando não estiver usando

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

### POST `/chat` (Melhorado! 🔥)
Chatbot inteligente que responde perguntas sobre um P&ID específico com suporte a múltiplos modos.

**Parâmetros:**
- `pid_id`: ID do P&ID
- `question`: Pergunta do usuário
- `mode` (opcional): Modo de resposta - `text`, `vision` ou `null` para automático (hybrid)

**Modos disponíveis:**
- **`text`**: Usa descrição ultra-completa pré-gerada (mais rápido, mais barato)
  - Ideal para perguntas sobre função, fluxo, equipamentos, instrumentação
  - Descrição gerada uma única vez e reutilizada
- **`vision`**: Envia imagem do P&ID para análise visual (mais preciso, mais caro)
  - Ideal para perguntas sobre layout, posição, símbolos, distribuição espacial
  - Requer que o P&ID tenha sido analisado a partir de PDF
- **`hybrid`** (padrão): Detecta automaticamente o melhor modo
  - Perguntas com "onde", "posição", "localização" → usa vision
  - Outras perguntas → usa text

**Exemplo:**
```bash
# Modo automático (hybrid)
curl -X POST "http://localhost:8000/chat?pid_id=analyzed_20241011_172600&question=Quais%20são%20os%20principais%20equipamentos?"

# Modo texto explícito
curl -X POST "http://localhost:8000/chat?pid_id=analyzed_20241011_172600&question=Qual%20instrumento%20mede%20a%20pressão%20da%20bomba%20P-101?&mode=text"

# Modo vision explícito
curl -X POST "http://localhost:8000/chat?pid_id=analyzed_20241011_172600&question=Onde%20está%20localizado%20o%20tanque%20T-101?&mode=vision"
```

**Retorna:**
```json
{
  "pid_id": "analyzed_20241011_172600",
  "question": "Quais são os principais equipamentos?",
  "answer": "Os principais equipamentos identificados são: P-101 (Bomba Centrífuga)...",
  "mode_used": "text"
}
```

**Descrição Ultra-Completa:**

O chatbot em modo `text` usa uma descrição ultra-completa que é gerada automaticamente uma única vez quando o P&ID é analisado. Esta descrição inclui:

- **Todos os equipamentos** com função, conexões (from/to) e coordenadas
- **Todos os instrumentos** agrupados por tipo (PT, TT, FT, LT, etc.)
- **Instrumentação por equipamento**: qual instrumento mede pressão/temperatura/vazão de cada equipamento
- **Equipamentos reserva/backup**: identificação de pares A/B, equipamentos standby
- **Fluxo detalhado do processo**: caminho completo usando TAGs (ex: T-101 → P-101A → FT-101 → FCV-101 → E-201)
- **Malhas de controle**: identificação completa de loops (sensor → controlador → atuador)
- **Elementos de segurança**: PSVs, alarmes, switches com localização
- **Layout espacial**: distribuição de equipamentos por região usando coordenadas

Exemplos de perguntas que podem ser respondidas:
- "Qual instrumento mede a pressão da bomba P-101?"
- "Qual equipamento é reserva do P-101A?"
- "Qual é o fluxo do material desde T-101 até E-201?"
- "Quais instrumentos estão associados ao trocador de calor E-201?"
- "Onde estão localizadas as válvulas de segurança?"


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

### Erro MuPDF ExtGState (PDF Corrompido)

**NOVO!** 🎉 O sistema agora tem **fallback automático** para PDFs corrompidos.

**Problema:** Você recebe o erro:
```
MuPDF error: syntax error: cannot find ExtGState resource 'R7'
```

**O que acontece agora:**
1. ✅ Sistema detecta automaticamente o erro
2. 🔄 Tenta abrir PDF com biblioteca alternativa (pdf2image/Poppler)
3. ✅ **Análise funciona normalmente** mesmo com PDF corrompido!

**Sistema de Fallback em 3 Níveis:**
- **PyMuPDF** (padrão - mais rápido)
- **pdf2image** (fallback - MUITO mais tolerante a erros) ⭐
- **pypdf** (último recurso - apenas metadados)

**Se o sistema ainda falhar após todas as tentativas:**

O PDF está muito corrompido. Soluções:
1. Abra o PDF em Adobe Reader e salve nova cópia: `Arquivo → Salvar Como`
2. Use ferramenta online: https://www.ilovepdf.com/pt/reparar-pdf
3. Recrie o PDF a partir do documento original

**Documentação completa:** Veja [PDF_FALLBACK_SYSTEM.md](PDF_FALLBACK_SYSTEM.md) para detalhes técnicos.

**Nota:** pdf2image requer Poppler instalado no sistema:
- **Linux:** `sudo apt-get install poppler-utils`
- **macOS:** `brew install poppler`
- **Windows:** Baixe de https://github.com/oschwartz10612/poppler-windows/releases

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
