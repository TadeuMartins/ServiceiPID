# Correção do Sistema de Coordenadas

## Problema Identificado

O problema reportado foi: **"As coordenadas devem ser calculadas considerando que o topo superior esquerdo é o ponto 0 em x e 0 em Y."**

Antes da correção, havia uma inconsistência:
- O prompt de análise de PDF (`build_prompt`) especificava: `Y crescente de baixo para cima` (origem inferior esquerda)
- O prompt de geração (`build_generation_prompt`) especificava: `Y crescente de cima para baixo` (origem superior esquerda)

## Solução Implementada

### Mudanças Realizadas

1. **Atualização do Prompt de Análise de PDF** (`build_prompt`):
   - ✅ Alterado de: `Y crescente de baixo para cima`
   - ✅ Para: `Y crescente de cima para baixo`
   - ✅ Adicionado: `Origem: Topo superior esquerdo é o ponto (0, 0)`
   - ✅ Atualizado: `Y: 0.0 (topo da página) até {height_mm} (base da página)`

2. **Atualização do Prompt de Geração** (`build_generation_prompt`):
   - ✅ Adicionado: `Origem: Topo superior esquerdo é o ponto (0, 0)`
   - ✅ Já estava correto: `Y crescente de cima para baixo`

3. **Lógica de Processamento**:
   - ✅ **Mantida sem alteração** - A lógica já estava correta
   - `y_mm`: coordenada com origem superior esquerda (0,0)
   - `y_mm_cad`: coordenada compatível com COMOS (origem inferior esquerda, calculada como `H_mm - y_mm`)

## Sistema de Coordenadas Atual

### Folha A0 (Paisagem)
- **Largura (X)**: 1189 mm
- **Altura (Y)**: 841 mm
- **Origem**: Topo superior esquerdo = (0, 0)

### Coordenadas X
- X = 0.0: extrema esquerda
- X = 1189.0: extrema direita
- Direção: cresce da esquerda para direita →

### Coordenadas Y
- Y = 0.0: topo da página ⬆️
- Y = 841.0: base da página ⬇️
- Direção: cresce de cima para baixo ↓

### Compatibilidade COMOS
O campo `y_mm_cad` mantém a compatibilidade com o sistema COMOS (Siemens), que usa origem inferior esquerda:
- `y_mm_cad = H_mm - y_mm`
- Para Y=0 (topo): `y_mm_cad = 841.0` (topo no sistema COMOS)
- Para Y=841 (base): `y_mm_cad = 0.0` (base no sistema COMOS)

## Testes Implementados

Criado novo arquivo de teste: `test_coordinate_system.py`

### Validações:
✅ Origem superior esquerda especificada em ambos os prompts  
✅ Y crescente de cima para baixo em ambos os prompts  
✅ Descrição de ranges de coordenadas correta  
✅ Remoção de descrições antigas (origem inferior)  
✅ Processamento de coordenadas correto  
✅ Compatibilidade COMOS mantida  

## Resultado

- ✅ **Todos os testes passam** (`test_coordinate_system.py`, `test_generate_feature.py`)
- ✅ **Sistema consistente**: ambos os prompts agora especificam origem superior esquerda
- ✅ **Compatibilidade mantida**: COMOS continua recebendo coordenadas corretas via `y_mm_cad`
- ✅ **Solução mínima**: apenas 4 linhas alteradas + documentação explícita da origem

## Mudanças nos Arquivos

### `backend/backend.py`
```diff
# Linha 273: build_prompt
-- Orientação: X crescente da esquerda para direita, Y crescente de baixo para cima
++ Orientação: X crescente da esquerda para direita, Y crescente de cima para baixo
++ Origem: Topo superior esquerdo é o ponto (0, 0)

# Linha 327: build_prompt  
-- Y: 0.0 (base da página) até {height_mm} (topo da página)
++ Y: 0.0 (topo da página) até {height_mm} (base da página)
++ Origem: Topo superior esquerdo é o ponto (0, 0)

# Linha 658: build_generation_prompt
++ Origem: Topo superior esquerdo é o ponto (0, 0)
```

### Novo arquivo: `test_coordinate_system.py`
- Testes de validação do sistema de coordenadas
- Verificação de consistência entre prompts
- Validação de processamento de coordenadas
- Verificação de compatibilidade COMOS

## Conclusão

O problema foi resolvido com sucesso. Agora, **todas as coordenadas são calculadas considerando que o topo superior esquerdo é o ponto (0, 0)**, com Y crescente de cima para baixo, conforme solicitado no problema.
