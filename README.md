# 🔎 P&ID Digitalizer DS Brazil - Siemens

Este projeto é um **aplicativo web** para análise de diagramas P&ID usando **Azure OpenAI GPT-4 multimodal**.

## Funcionalidades

### Versão 3
- Visualização gráfica com sobreposição dos pontos na **imagem real do P&ID**.
- Título e identidade visual Siemens.
- Exportação em Excel e JSON.

### Versão 4 (Nova!)
- **Geração de P&ID a partir de linguagem natural**: Crie diagramas P&ID completos apenas descrevendo o processo
- Interface com abas: "Analisar PDF" e "Gerar a partir de Prompt"
- Geração automática de equipamentos e instrumentos com coordenadas em folha A0 (1189mm x 841mm)
- Aplicação automática do matcher para identificação de SystemFullName
- Visualização 2D do layout gerado
- Exportação dos dados gerados (Excel/JSON)

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

## Como rodar
1. Configure as variáveis do Azure no `backend/backend.py`.
2. Instale dependências e rode o backend:
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn backend:app --reload --port 8000
   ```
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
