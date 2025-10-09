# 🔎 P&ID Digitalizer DS Brazil - Siemens

Este projeto é um **aplicativo web** para análise de diagramas P&ID usando **Azure OpenAI GPT-4 multimodal**.

## Versão 3
- Visualização gráfica com sobreposição dos pontos na **imagem real do P&ID**.
- Título e identidade visual Siemens.
- Exportação em Excel e JSON.

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
