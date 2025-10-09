# Implementação Completa: Geração de P&ID a partir de Linguagem Natural

## 🎯 Objetivo Alcançado

Foi implementada com sucesso a funcionalidade solicitada de **criar tabelas de equipamentos e instrumentos baseadas em prompts de linguagem natural**, sem necessidade de escanear PDFs existentes.

## ✨ O que foi implementado

### 1. Backend (`backend/backend.py`)

#### Novo Endpoint: `POST /generate`
```python
@app.post("/generate")
async def generate_pid(
    prompt: str = Query(..., description="Descrição do processo em linguagem natural")
):
    """
    Gera P&ID a partir de descrição em linguagem natural.
    """
```

**Funcionalidades:**
- Recebe descrição do processo em linguagem natural
- Usa GPT-4o para gerar equipamentos e instrumentos
- Distribui coordenadas em folha A0 (1189mm x 841mm)
- Aplica matcher automático para SystemFullName
- Retorna dados no mesmo formato do `/analyze`

#### Função de Geração de Prompt
```python
def build_generation_prompt(process_description: str, width_mm: float = 1189.0, height_mm: float = 841.0) -> str:
    """
    Constrói prompt para gerar P&ID completo a partir de descrição do processo.
    A0 sheet dimensions: 1189mm x 841mm (landscape)
    """
```

**Características do prompt:**
- Instruções detalhadas sobre P&ID e símbolos ISA
- Especificação de dimensões A0 (1189mm x 841mm)
- Regras para TAGs (equipamentos e instrumentos)
- Formato JSON de saída
- Distribuição lógica de equipamentos

### 2. Frontend (`frontend/app.py`)

#### Nova Interface com Abas
```python
tab1, tab2 = st.tabs(["📂 Analisar PDF", "🎨 Gerar a partir de Prompt"])
```

**Aba 1: Analisar PDF** (funcionalidade existente)
- Upload de PDF
- Análise com IA
- Visualização de resultados

**Aba 2: Gerar a partir de Prompt** (NOVO!)
- Campo de texto para descrição do processo
- Exemplos de prompts
- Botão "Gerar P&ID"
- Tabela de resultados
- Visualização 2D do layout
- Exportação Excel/JSON

#### Exemplos de Prompts Sugeridos
```
• "Gere um P&ID completo de um processo de clinquerização"
• "Crie um diagrama P&ID para um sistema de destilação de petróleo"
• "Gere P&ID de uma planta de tratamento de água"
```

### 3. Processamento e Integração

**Fluxo Completo:**
1. Usuário digita prompt → Frontend envia para backend
2. Backend constrói prompt técnico → Chama GPT-4o
3. GPT-4o gera JSON com equipamentos → Backend parseia
4. Para cada item:
   - Valida coordenadas (clamp em A0)
   - Calcula y_mm_cad (flip Y para COMOS)
   - **Aplica matcher** para obter SystemFullName
   - Adiciona metadados (página, modelo, etc.)
5. Remove duplicatas → Retorna JSON
6. Frontend exibe tabela e visualização

### 4. Matcher Automático

**Integração com `system_matcher.py`:**
```python
try:
    tipo = it.get("tipo", "")
    match = match_system_fullname(item["tag"], item["descricao"], tipo)
    item.update(match)
except Exception as e:
    item.update({
        "SystemFullName": None,
        "Confiança": 0,
        "matcher_error": str(e)
    })
```

**Campos adicionados pelo matcher:**
- `SystemFullName`: Nome completo do sistema
- `Confiança`: Score de similaridade (0-1)
- `Tipo_ref`: Tipo de referência
- `Descricao_ref`: Descrição de referência

### 5. Coordenadas em Folha A0

**Dimensões Padrão:**
- Largura (X): 1189 mm
- Altura (Y): 841 mm
- Orientação: Paisagem (landscape)

**Distribuição:**
- Equipamentos principais: distribuídos logicamente
- Instrumentos: posicionados próximos aos equipamentos
- Fluxo: entrada à esquerda, saída à direita
- Validação: coordenadas dentro dos limites (0-1189, 0-841)

### 6. Visualização 2D

**Gráfico de Layout:**
```python
# Desenha borda da folha A0
ax.add_patch(plt.Rectangle((0, 0), 1189, 841, fill=False, edgecolor='black', linewidth=2))

# Plota equipamentos
for _, item in df.iterrows():
    x, y = item.get("x_mm", 0), item.get("y_mm", 0)
    # Cor por tipo: azul para instrumentos, vermelho para equipamentos
    color = "blue" if "instrumento" in tipo.lower() else "red"
```

## 📊 Formato de Dados Gerados

Exemplo de resposta:
```json
[
  {
    "pagina": 1,
    "modelo": "gpt-4o",
    "resultado": [
      {
        "tag": "P-101",
        "descricao": "Bomba Centrífuga",
        "tipo": "Bomba",
        "x_mm": 200.0,
        "y_mm": 400.0,
        "y_mm_cad": 441.0,
        "from": "T-101",
        "to": "E-201",
        "page_width_mm": 1189.0,
        "page_height_mm": 841.0,
        "SystemFullName": "Plant/Area/P-101",
        "Confiança": 0.85,
        "Tipo_ref": "Bomba",
        "Descricao_ref": "Bomba Centrífuga"
      }
    ]
  }
]
```

## 🔧 Como Usar

### Via Interface Web

1. Acesse http://localhost:8501
2. Clique na aba "🎨 Gerar a partir de Prompt"
3. Digite a descrição do processo:
   ```
   gere um P&ID completo de um processo de clinquerização
   ```
4. Clique em "🎨 Gerar P&ID"
5. Visualize a tabela gerada
6. Exporte para Excel ou JSON

### Via API

```bash
curl -X POST "http://localhost:8000/generate?prompt=gere%20um%20P%26ID%20de%20clinquerização"
```

## ✅ Validação Realizada

### Testes Executados:
- ✓ Verificação de sintaxe Python (backend e frontend)
- ✓ Teste de formato de resposta
- ✓ Validação de dimensões A0 (1189mm x 841mm)
- ✓ Verificação da estrutura do endpoint
- ✓ Teste de build do prompt de geração

### Arquivos de Teste:
- `test_generate_feature.py`: Testes unitários de validação
- `create_ui_mockup.py`: Script para gerar mockup da interface

## 📦 Arquivos Alterados

1. **backend/backend.py** (+172 linhas)
   - Função `build_generation_prompt()`
   - Endpoint `POST /generate`
   - Integração com matcher

2. **frontend/app.py** (+138 linhas)
   - Nova aba "Gerar a partir de Prompt"
   - Campo de texto para prompt
   - Botão de geração
   - Visualização 2D
   - Exportação de resultados

3. **README.md** (atualizado)
   - Documentação da nova funcionalidade
   - Exemplos de uso
   - Documentação da API

4. **.gitignore** (criado)
   - Exclusão de __pycache__
   - Exclusão de arquivos .pkl
   - Exclusão de arquivos temporários

## 🎨 Resultado Visual

A interface agora possui:
- ✅ Duas abas distintas
- ✅ Campo de texto para prompt
- ✅ Botão "Gerar P&ID" destacado
- ✅ Tabela de resultados com todos os campos
- ✅ Visualização 2D do layout
- ✅ Botões de exportação (Excel/JSON)
- ✅ SystemFullName exibido na tabela

## 🚀 Próximos Passos (Opcional)

Para testes em ambiente real:
1. Configure a chave OpenAI em variável de ambiente
2. Certifique-se que o arquivo `referencia_systems.xlsx` está presente
3. Inicie o backend: `uvicorn backend:app --reload --port 8000`
4. Inicie o frontend: `streamlit run app.py`
5. Acesse http://localhost:8501

## 📝 Conclusão

A implementação foi concluída com sucesso, atendendo completamente ao requisito:

> "criar uma tabela baseada em um prompt de linguagem natural, exemplo: gere um P&ID completo de um processo de clinquerização, nesse momento você deve gerar a tabela distribuindo os equipamentos e instrumentos em coordenadas x e Y considerando uma folha A0, e também usando o matcher para trazer o system full name na tabela final"

✅ Tabela criada a partir de prompt
✅ Coordenadas X e Y em folha A0 (1189mm x 841mm)
✅ Matcher aplicado para SystemFullName
✅ Interface com botão e campo de prompt
✅ Exportação em Excel/JSON
✅ Visualização 2D do layout
