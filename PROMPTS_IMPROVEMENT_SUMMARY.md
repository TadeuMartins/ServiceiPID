# Melhoria dos Prompts LLM - Sumário

## 📋 Visão Geral

Este documento descreve as melhorias implementadas nos prompts LLM para garantir:
1. **Dois prompts distintos e especializados** para diferentes funções
2. **Análise técnica aprofundada** de P&IDs existentes
3. **Geração completa e detalhada** de novos P&IDs
4. **Coordenadas globais consistentes** mesmo em análise por quadrantes
5. **Compatibilidade total com COMOS** (Siemens)

## ✨ Mudanças Implementadas

### 1. Prompt de Leitura de PDF (`build_prompt`)

**Objetivo:** Extrair TODOS os elementos de um P&ID existente com máxima precisão técnica.

**Melhorias Principais:**

#### 📐 Sistema de Coordenadas Global (CRÍTICO para COMOS)
- **Antes:** Instruções básicas sobre coordenadas globais
- **Agora:** 
  - Ênfase explícita em coordenadas ABSOLUTAS e GLOBAIS
  - Sistema de coordenadas detalhado (X esquerda→direita, Y baixo→topo)
  - Compatibilidade COMOS explicitamente mencionada
  - Para quadrantes: fórmula clara de conversão `X_global = X_local + origem_X`
  - Validação de limites (0 a width_mm, 0 a height_mm)

#### 🏭 Lista Abrangente de Equipamentos
**Antes:** Lista básica de equipamentos  
**Agora:** Lista técnica completa incluindo:
- **Equipamentos principais:** Bombas, tanques, vasos, trocadores, reatores, fornos, caldeiras, compressores, torres, ciclones, filtros, secadores, evaporadores, cristalizadores, misturadores
- **Instrumentação ISA completa:**
  - Pressão: PI, PT, PG, PS, PSH, PSL, PCV, PSV, PRV
  - Temperatura: TI, TT, TE, TW, TS, TSH, TSL, TCV
  - Vazão: FI, FT, FE, FQ, FS, FCV
  - Nível: LI, LT, LG, LS, LSH, LSL, LSHH, LSLL, LCV
  - Análise: AI, AT, AQ, QI, QT
  - Densidade/Viscosidade: DI, DT, VI, VT
  - pH/Condutividade: QI, QT, CI, CT
  - Velocidade/Rotação: SI, ST
- **Válvulas:** Controle (FCV, PCV, LCV, TCV), manuais (gate, globe, ball, butterfly, check), segurança (PSV, PRV, TSV), solenoides
- **Outros:** Tubulações, conexões, malhas de controle, sistemas de segurança

#### 📏 Normas e Padrões Técnicos
- **Normas ISA:** S5.1, S5.2, S5.3 explicitamente mencionadas
- **Nomenclatura técnica:** Terminologia ISA precisa obrigatória
- **TAGs completas:** Captura mesmo com prefixo e número separados
- **Sufixos importantes:** A/B (redundância), -1/-2 (numeração), H/L (high/low)

#### 🎯 Completude e Precisão
- Instrução para extrair TODOS os símbolos (mesmo sem TAG)
- Não omitir instrumentos auxiliares
- Capturar símbolos parcialmente visíveis
- Precisão de coordenadas até 0.1 mm

### 2. Prompt de Geração de P&ID (`build_generation_prompt`)

**Objetivo:** Gerar P&ID COMPLETO e DETALHADO a partir de descrição em linguagem natural.

**Melhorias Principais:**

#### 👨‍🔬 Papel Técnico Aprofundado
- **Antes:** "Especialista em P&ID"
- **Agora:** "Engenheiro de processos sênior especializado em elaboração de P&ID segundo normas ISA S5.1, S5.2, S5.3 e boas práticas de engenharia de processos industriais"

#### 🏗️ Especificações Técnicas Detalhadas
**EQUIPAMENTOS DE PROCESSO com requisitos específicos:**
- Bombas: tipo, capacidade, redundância A/B
- Tanques: nível, válvulas entrada/saída, vents, drenos
- Vasos: controles de pressão, nível, temperatura
- Trocadores: instrumentação em ambos os lados
- Reatores: agitação, controle temperatura/pressão, análise
- Torres: condensadores, refervedores, pratos/recheio, refluxo
- Compressores: lubrificação, resfriamento, anti-surge
- Fornos/Caldeiras: controles de combustão

#### 📊 Instrumentação Completa (ISA S5.1)
**Cada tipo de instrumento detalhado:**
- Pressão: Indicadores, transmissores (4-20mA para DCS), gauges, switches, válvulas
- Temperatura: Indicadores, transmissores (termopares, RTDs), elementos, poços termométricos
- Vazão: Indicadores, transmissores, elementos primários (orifício, venturi, turbina, magnético, Coriolis), totalizadores
- Nível: Indicadores, transmissores (radar, ultrassônico, diff pressure), visores, switches múltiplos
- Análise: pH, condutividade, O₂, turbidez, concentração, cromatografia

#### 🎯 Válvulas e Atuadores Detalhados
- Tipos: Controle, manuais, segurança, solenoides, diafragma
- Atuadores: Pneumáticos, elétricos, hidráulicos
- Ação na falha: FC (fail close), FO (fail open), FL (fail last)

#### 🗺️ Distribuição Espacial Inteligente
**Zonas definidas para folha A0 (1189mm x 841mm):**
- Zona de entrada/alimentação: X = 100-300 mm
- Zona de processamento principal: X = 300-800 mm
- Zona de separação/purificação: X = 800-1000 mm
- Zona de saída/produto: X = 1000-1100 mm
- Equipamentos principais: Y = 300-600 mm (centro)
- Instrumentos e válvulas: Y = 250-400 mm
- Espaçamentos mínimos: 100-150mm entre equipamentos, 30-50mm entre instrumentos

#### 📈 Requisitos de Completude
- **MÍNIMO ESPERADO:** 15-30 equipamentos para processo simples, 30-80 para processo completo
- Instrumentação redundante em sistemas críticos
- Elementos de segurança: PSVs, alarmes, intertravamentos
- Equipamentos auxiliares: bombas reserva, filtros
- Utilidades necessárias: vapor, água, ar, nitrogênio

#### 🔄 Sistemas Auxiliares e Utilidades
- Sistemas de vapor: linhas, traps, condensado
- Água de resfriamento: entrada/retorno
- Ar de instrumentos: distribuição, FRLs
- Nitrogen blanketing/inertização
- Drenagem e ventilação
- Sample points

#### 🎛️ Malhas de Controle e Automação
- Controles regulatórios: PID, cascata, feedforward
- Intertravamentos de segurança (SIS)
- Alarmes: PAH, PAL, TAH, TAL, FAH, FAL, LAH, LAL
- Indicação local vs. sala de controle

## 📊 Comparação: Antes vs. Agora

| Aspecto | Antes | Agora |
|---------|-------|-------|
| **Normas ISA** | Menção básica | S5.1, S5.2, S5.3 detalhadas |
| **Equipamentos (PDF)** | ~10 tipos | 30+ tipos categorizados |
| **Instrumentação (PDF)** | Básica | 50+ tipos ISA completos |
| **Equipamentos (Geração)** | ~8 tipos | 15+ tipos com especificações |
| **Instrumentação (Geração)** | Básica | Completa por categoria |
| **Coordenadas Globais** | Mencionado | Enfatizado + fórmulas |
| **COMOS** | Não mencionado | Explicitamente compatível |
| **Quadrantes** | Instrução básica | Fórmula conversão detalhada |
| **Completude** | Não especificado | Mínimo 15-30 equipamentos |
| **Layout Espacial** | Básico | Zonas definidas (mm) |
| **Válvulas** | Tipos básicos | Tipos + atuadores + fail-safe |
| **Papel LLM (Leitura)** | "Especialista" | "Engenheiro especialista ISA" |
| **Papel LLM (Geração)** | "Especialista" | "Eng. processos sênior ISA" |

## ✅ Validação e Testes

### Testes Executados:
1. ✅ Verificação de sintaxe Python
2. ✅ Testes originais do sistema (test_generate_feature.py)
3. ✅ Testes específicos dos prompts (test_prompts.py)

### Elementos Verificados:
- [x] ISA S5.1/S5.2/S5.3 mencionados
- [x] Compatibilidade COMOS
- [x] Coordenadas globais enfatizadas
- [x] Sistema de coordenadas absoluto
- [x] Lista abrangente de equipamentos
- [x] Transmissores e instrumentação
- [x] Válvulas de controle
- [x] Nomenclatura ISA
- [x] Exemplos de TAGs
- [x] Fórmula conversão coordenadas
- [x] Origem de quadrante
- [x] Papel de engenheiro sênior
- [x] Requisitos de completude
- [x] Distribuição espacial
- [x] Separação clara entre prompts

## 🎯 Resultados Esperados

### Para Leitura de PDF:
1. **Extração mais completa:** Captura de TODOS os equipamentos e instrumentos
2. **Coordenadas precisas:** Sistema global consistente para COMOS
3. **Nomenclatura correta:** TAGs ISA padronizadas
4. **Sem erros de importação:** Coordenadas globais mesmo em quadrantes

### Para Geração de P&ID:
1. **Diagramas mais completos:** Mínimo 15-30 equipamentos/instrumentos
2. **Tecnicamente corretos:** Normas ISA S5.1, S5.2, S5.3
3. **Bem distribuídos:** Zonas lógicas de processo
4. **Completos:** Instrumentação, válvulas, utilidades, segurança
5. **Prontos para COMOS:** Coordenadas globais válidas

## 📁 Arquivos Modificados

1. **backend/backend.py**
   - `build_prompt()` - Prompt de leitura de PDF aprimorado (linhas 263-385)
   - `build_generation_prompt()` - Prompt de geração aprimorado (linhas 643-819)

2. **test_prompts.py** (novo)
   - Testes de validação dos prompts melhorados

## 🔍 Como Verificar

```bash
# Testar sintaxe
python3 -m py_compile backend/backend.py

# Executar testes existentes
python3 test_generate_feature.py

# Executar novos testes de prompts
python3 test_prompts.py
```

## 📝 Notas Importantes

1. **Coordenadas Globais:** Crítico para COMOS - sempre no sistema global da página, mesmo ao dividir em quadrantes
2. **ISA Standards:** S5.1 (símbolos), S5.2 (lógica binária), S5.3 (símbolos gráficos)
3. **Completude:** LLM agora instruído a gerar P&IDs completos, não simplificados
4. **Precisão:** Coordenadas até 0.1mm, TAGs completas com sufixos

## 🚀 Próximos Passos Sugeridos

1. Testar com PDFs reais e verificar extração completa
2. Testar geração com processos complexos (clinquerização, destilação, etc.)
3. Validar importação no COMOS
4. Ajustar tolerâncias se necessário
5. Adicionar exemplos específicos de processos comuns

---

**Status:** ✅ Implementado e testado  
**Data:** 2025-10-10  
**Versão:** 1.0
