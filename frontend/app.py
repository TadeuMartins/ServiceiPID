import streamlit as st
import requests
import pandas as pd
import json
import tempfile
import os
import fitz  # PyMuPDF
import matplotlib.pyplot as plt
import io

API_URL = "http://localhost:8000/analyze"
GENERATE_URL = "http://localhost:8000/generate"
CHAT_URL = "http://localhost:8000/chat"
DESCRIBE_URL = "http://localhost:8000/describe"

# ======== Inicializa session state ========
if "pid_id" not in st.session_state:
    st.session_state.pid_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "show_chatbot" not in st.session_state:
    st.session_state.show_chatbot = False
if "process_description" not in st.session_state:
    st.session_state.process_description = None
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "last_uploaded_file" not in st.session_state:
    st.session_state.last_uploaded_file = None
if "generation_results" not in st.session_state:
    st.session_state.generation_results = None
if "last_prompt" not in st.session_state:
    st.session_state.last_prompt = None
if "chatbot_mode" not in st.session_state:
    st.session_state.chatbot_mode = "hybrid"

# ======== Layout inicial ========
st.set_page_config(page_title="P&ID Digitalizer DS Brazil - Siemens", layout="wide")

# Header customizado
col1, col2 = st.columns([1,5])
with col1:
    st.image("sie_logo.png", width=180)
with col2:
    st.markdown(
        "<h1 style='color:#009999; font-size:36px;'>🔎 P&ID Digitalizer DS Brazil - Siemens</h1>",
        unsafe_allow_html=True
    )
st.markdown("---")

# ======== Abas para diferentes modos ========
tab1, tab2 = st.tabs(["📂 Analisar PDF", "🎨 Gerar a partir de Prompt"])

with tab1:
    st.markdown("### Analise um P&ID existente")
    
    # Diagram type selector
    diagram_type_analyze = st.selectbox(
        "Tipo de Diagrama:",
        options=[("P&ID", "pid"), ("Diagrama Elétrico", "electrical")],
        format_func=lambda x: x[0],
        key="diagram_type_analyze",
        help="Selecione o tipo de diagrama para usar a referência apropriada no system matcher"
    )
    
    uploaded_file = st.file_uploader("📂 Envie um arquivo PDF de P&ID", type=["pdf"])

with tab2:
    st.markdown("### Gere um P&ID a partir de descrição em linguagem natural")
    
    # Diagram type selector
    diagram_type_generate = st.selectbox(
        "Tipo de Diagrama:",
        options=[("P&ID", "pid"), ("Diagrama Elétrico", "electrical")],
        format_func=lambda x: x[0],
        key="diagram_type_generate",
        help="Selecione o tipo de diagrama para usar a referência apropriada no system matcher"
    )
    
    st.markdown("""
    **Exemplo de prompt:**
    - "Gere um P&ID completo de um processo de clinquerização"
    - "Crie um diagrama P&ID para um sistema de destilação de petróleo"
    - "Gere P&ID de uma planta de tratamento de água"
    """)
    
    prompt_text = st.text_area(
        "Descreva o processo:",
        placeholder="Ex: gere um P&ID completo de um processo de clinquerização",
        height=100
    )
    
    generate_button = st.button("🎨 Gerar P&ID", type="primary", use_container_width=True)

# ======== Normalizador de resposta ========
def normalize_backend_result(data):
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            return []
    if isinstance(data, dict):
        if "pages" in data:
            return data["pages"]
        else:
            return [data]
    if isinstance(data, list):
        return data
    return []

# ======== Processamento ========
if uploaded_file:
    # Verifica se é um arquivo novo
    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    
    if st.session_state.last_uploaded_file != file_id:
        # Arquivo novo - processar
        st.session_state.last_uploaded_file = file_id
        
        with st.spinner("⏳ Processando com IA..."):
            try:
                files = {"file": uploaded_file.getvalue()}
                # Get diagram type value from the selectbox
                diagram_type_value = diagram_type_analyze[1]  # Extract the value from the tuple
                params = {"diagram_type": diagram_type_value}
                response = requests.post(API_URL, files=files, params=params, timeout=3600)
            except Exception as e:
                st.error(f"❌ Erro ao conectar com backend: {e}")
                st.stop()

            if response.status_code == 200:
                try:
                    data = response.json()
                except Exception:
                    st.error("❌ Backend não retornou JSON válido.")
                    st.stop()

                pages = normalize_backend_result(data)
                final_data = []
                
                # Captura pid_id se disponível
                if pages and len(pages) > 0:
                    pid_id = pages[0].get("pid_id")
                    if pid_id:
                        st.session_state.pid_id = pid_id
                        st.session_state.show_chatbot = True
                        st.session_state.chat_history = []
                        
                        # Busca descrição do processo (se não houver erro)
                        try:
                            desc_response = requests.get(f"{DESCRIBE_URL}?pid_id={pid_id}", timeout=60)
                            if desc_response.status_code == 200:
                                desc_data = desc_response.json()
                                st.session_state.process_description = desc_data.get("description", "")
                                st.success("✅ Descrição do processo gerada! Chatbot ativado para perguntas.")
                        except:
                            pass

                for page in pages:
                    if isinstance(page.get("resultado", []), list):
                        for item in page["resultado"]:
                            item["pagina"] = page.get("pagina", "?")
                            item["modelo"] = page.get("modelo", "desconhecido")
                            final_data.append(item)

                # Armazena os resultados no session state
                st.session_state.analysis_results = {
                    "data": data,
                    "pages": pages,
                    "final_data": final_data,
                    "uploaded_file_name": uploaded_file.name
                }
            else:
                st.error("❌ Erro ao processar PDF.")
                st.stop()
    
    # Usa os resultados armazenados no session state
    if st.session_state.analysis_results:
        data = st.session_state.analysis_results["data"]
        pages = st.session_state.analysis_results["pages"]
        final_data = st.session_state.analysis_results["final_data"]
        
        if final_data:
            df = pd.DataFrame(final_data)
            
            # ======== Descrição do Processo ========
            if st.session_state.process_description:
                with st.expander("📝 Descrição Completa do Processo", expanded=True):
                    st.markdown(st.session_state.process_description)
                    st.markdown("---")
                    st.info("💡 **Dica:** Role para baixo para usar o chatbot e fazer perguntas específicas sobre este P&ID!")

            # ======== KPIs ========
            st.subheader("📊 Resumo da Análise")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Total de Equipamentos", len(df))
            with c2:
                st.metric("Páginas Processadas", df["pagina"].nunique())
            with c3:
                st.metric("Modelos Usados", ", ".join(df["modelo"].unique().tolist()))

            # ======== Filtro ========
            st.subheader("🔍 Filtrar Resultados")
            paginas = sorted(df["pagina"].unique())
            pagina_sel = st.selectbox("Selecione a Página", ["Todas"] + list(map(str, paginas)))

            if pagina_sel != "Todas":
                df_filtered = df[df["pagina"].astype(str) == str(pagina_sel)]
            else:
                df_filtered = df

            st.dataframe(df_filtered, use_container_width=True)

            # ======== Exportação ========
            st.subheader("📥 Exportar Resultados")

            # Nome base do PDF (sem extensão)
            pid_name = os.path.splitext(st.session_state.analysis_results["uploaded_file_name"])[0]
            safe_name = pid_name.replace(" ", "_").replace("/", "_")

            # Excel
            tmp_excel = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            df.to_excel(tmp_excel.name, index=False)
            tmp_excel.close()
            with open(tmp_excel.name, "rb") as f:
                excel_data = f.read()
            try:
                os.unlink(tmp_excel.name)
            except OSError:
                pass  # File will be cleaned up by OS eventually
            st.download_button(
                "💾 Baixar Excel",
                excel_data,
                file_name=f"{safe_name}_analysis.xlsx",
                use_container_width=True
            )

            # ======== Preview PDF ========
            with st.expander("👁️ Pré-visualizar páginas anotadas"):
                tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                tmp_pdf.write(uploaded_file.getvalue())
                tmp_pdf.close()
                doc = fitz.open(tmp_pdf.name)

                for page in pages:
                    page_num = int(page.get("pagina", 1))
                    st.markdown(f"**Página {page_num}**")
                    pix = doc[page_num - 1].get_pixmap(dpi=150)
                    img_bytes = pix.tobytes("png")

                    fig, ax = plt.subplots(figsize=(8, 6))
                    ax.imshow(plt.imread(io.BytesIO(img_bytes)), cmap="gray")

                    for it in page.get("resultado", []):
                        x, y = it.get("x_mm"), it.get("y_mm")
                        if x and y:
                            ax.plot(x, y, "rx", markersize=6)
                            ax.text(x, y, it.get("tag", ""), fontsize=6, color="red")

                    ax.axis("off")
                    st.pyplot(fig)
                doc.close()
                try:
                    os.unlink(tmp_pdf.name)
                except OSError:
                    pass  # File will be cleaned up by OS eventually

            # ======== Raw JSON (debug opcional) ========
            with st.expander("📂 Ver JSON bruto do backend"):
                st.json(data)

        else:
            st.warning("⚠️ Nenhum equipamento identificado.")


# ======== Processamento para Geração ========
if generate_button and prompt_text:
    # Verifica se é um novo prompt
    if st.session_state.last_prompt != prompt_text:
        # Novo prompt - processar
        st.session_state.last_prompt = prompt_text
        
        with st.spinner("⏳ Gerando P&ID com IA..."):
            try:
                # Get diagram type value from the selectbox
                diagram_type_value = diagram_type_generate[1]  # Extract the value from the tuple
                params = {"prompt": prompt_text, "diagram_type": diagram_type_value}
                response = requests.post(GENERATE_URL, params=params, timeout=600)
            except Exception as e:
                st.error(f"❌ Erro ao conectar com backend: {e}")
                st.stop()

            if response.status_code == 200:
                try:
                    data = response.json()
                except Exception:
                    st.error("❌ Backend não retornou JSON válido.")
                    st.stop()

                pages = normalize_backend_result(data)
                final_data = []
                
                # Captura pid_id se disponível
                if pages and len(pages) > 0:
                    pid_id = pages[0].get("pid_id")
                    if pid_id:
                        st.session_state.pid_id = pid_id
                        st.session_state.show_chatbot = True
                        st.session_state.chat_history = []
                        
                        # Busca descrição do processo
                        try:
                            desc_response = requests.get(f"{DESCRIBE_URL}?pid_id={pid_id}", timeout=60)
                            if desc_response.status_code == 200:
                                desc_data = desc_response.json()
                                st.session_state.process_description = desc_data.get("description", "")
                                st.success("✅ Descrição do processo gerada! Chatbot ativado para perguntas.")
                        except:
                            pass

                for page in pages:
                    if isinstance(page.get("resultado", []), list):
                        for item in page["resultado"]:
                            item["pagina"] = page.get("pagina", "?")
                            item["modelo"] = page.get("modelo", "desconhecido")
                            final_data.append(item)

                # Armazena os resultados no session state
                st.session_state.generation_results = {
                    "data": data,
                    "pages": pages,
                    "final_data": final_data,
                    "prompt": prompt_text
                }
            else:
                st.error("❌ Erro ao gerar P&ID.")
                st.stop()
    
    # Usa os resultados armazenados no session state
    if st.session_state.generation_results:
        data = st.session_state.generation_results["data"]
        pages = st.session_state.generation_results["pages"]
        final_data = st.session_state.generation_results["final_data"]
        prompt_text = st.session_state.generation_results["prompt"]
        
        if final_data:
            df = pd.DataFrame(final_data)
            
            # ======== Descrição do Processo ========
            if st.session_state.process_description:
                with st.expander("📝 Descrição Completa do Processo", expanded=True):
                    st.markdown(st.session_state.process_description)
                    st.markdown("---")
                    st.info("💡 **Dica:** Role para baixo para usar o chatbot e fazer perguntas específicas sobre este P&ID!")

            # ======== KPIs ========
            st.subheader("📊 Resumo da Geração")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Total de Equipamentos", len(df))
            with c2:
                st.metric("Folha", "A0 (1189mm x 841mm)")
            with c3:
                st.metric("Modelo Usado", df["modelo"].iloc[0] if len(df) > 0 else "N/A")

            # ======== Tabela ========
            st.subheader("📋 Equipamentos e Instrumentos Gerados")
            st.dataframe(df, use_container_width=True)

            # ======== Exportação ========
            st.subheader("📥 Exportar Resultados")

            # Nome baseado no prompt (primeiras palavras)
            prompt_words = "_".join(prompt_text.split()[:5])
            safe_name = prompt_words.replace(" ", "_").replace("/", "_")

            # Excel
            tmp_excel = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            df.to_excel(tmp_excel.name, index=False)
            tmp_excel.close()
            with open(tmp_excel.name, "rb") as f:
                excel_data = f.read()
            try:
                os.unlink(tmp_excel.name)
            except OSError:
                pass  # File will be cleaned up by OS eventually
            st.download_button(
                "💾 Baixar Excel",
                excel_data,
                file_name=f"{safe_name}_gerado.xlsx",
                use_container_width=True
            )

            # ======== Visualização 2D ========
            with st.expander("📐 Visualizar Layout (A0)"):
                fig, ax = plt.subplots(figsize=(16, 11))
                
                # Desenha borda da folha A0
                ax.add_patch(plt.Rectangle((0, 0), 1189, 841, fill=False, edgecolor='black', linewidth=2))
                
                # Plota equipamentos
                for _, item in df.iterrows():
                    x, y = item.get("x_mm", 0), item.get("y_mm", 0)
                    tag = item.get("tag", "N/A")
                    tipo = item.get("tipo", "")
                    
                    # Cor por tipo
                    color = "blue" if "instrumento" in tipo.lower() else "red"
                    marker = "o" if "instrumento" in tipo.lower() else "s"
                    
                    ax.plot(x, y, marker=marker, color=color, markersize=10)
                    ax.text(x + 10, y + 10, tag, fontsize=8, color=color)
                
                ax.set_xlim(0, 1189)
                ax.set_ylim(0, 841)
                ax.invert_yaxis()  # Inverte Y para origem superior esquerda (0,0)
                ax.set_xlabel("X (mm)")
                ax.set_ylabel("Y (mm)")
                ax.set_title("Layout do P&ID Gerado (Folha A0) - Origem: Topo Superior Esquerdo")
                ax.grid(True, alpha=0.3)
                ax.set_aspect('equal')
                
                st.pyplot(fig)

            # ======== Raw JSON (debug opcional) ========
            with st.expander("📂 Ver JSON bruto do backend"):
                st.json(data)

        else:
            st.warning("⚠️ Nenhum equipamento gerado.")


elif generate_button and not prompt_text:
    st.warning("⚠️ Por favor, descreva o processo antes de gerar.")


# ============================================================
# CHATBOT MINIMIZÁVEL
# ============================================================
if st.session_state.pid_id:
    st.markdown("---")
    st.markdown("") # Adiciona espaçamento
    
    # Container para o chatbot com opção de minimizar
    chatbot_col1, chatbot_col2 = st.columns([6, 1])
    
    with chatbot_col1:
        st.markdown("### 💬 Assistente P&ID - Faça perguntas sobre este diagrama")
        if st.session_state.show_chatbot:
            st.markdown("*Chatbot ativado! Faça perguntas sobre o processo analisado.*")
    
    with chatbot_col2:
        if st.button("🔽 Minimizar" if st.session_state.show_chatbot else "🔼 Expandir", key="toggle_chatbot"):
            st.session_state.show_chatbot = not st.session_state.show_chatbot
            st.rerun()
    
    if st.session_state.show_chatbot:
        # Container do chatbot
        chatbot_container = st.container()
        
        with chatbot_container:
            st.markdown(f"**P&ID ID:** `{st.session_state.pid_id}`")
            
            # Área de histórico do chat
            if st.session_state.chat_history:
                st.markdown("#### 📜 Histórico de Conversação")
                for i, entry in enumerate(st.session_state.chat_history):
                    with st.chat_message("user"):
                        st.write(entry["question"])
                    with st.chat_message("assistant"):
                        st.write(entry["answer"])
                        # Mostra modo usado (se disponível)
                        mode_used = entry.get("mode_used", "unknown")
                        mode_emoji = "🖼️" if mode_used == "vision" else "📝"
                        mode_label = "Vision" if mode_used == "vision" else "Text"
                        st.caption(f"{mode_emoji} Modo: {mode_label}")
            
            # Input para nova pergunta
            st.markdown("#### ❓ Faça uma pergunta")
            
            col1, col2 = st.columns([5, 1])
            
            with col1:
                user_question = st.text_input(
                    "Pergunta:",
                    placeholder="Ex: Quais são os principais equipamentos? Onde está localizado o tanque T-101?",
                    key="chat_input",
                    label_visibility="collapsed"
                )
            
            with col2:
                ask_button = st.button("📤 Enviar", use_container_width=True)
            
            # Seletor de modo (opcional - usa hybrid por padrão)
            with st.expander("⚙️ Configurações Avançadas do Chatbot", expanded=False):
                chatbot_mode = st.radio(
                    "Modo de resposta:",
                    options=["hybrid", "text", "vision"],
                    index=0,
                    horizontal=True,
                    help="""
                    - **hybrid**: Decide automaticamente (recomendado) - usa vision para perguntas visuais, text para outras
                    - **text**: Sempre usa descrição ultra-completa + lista de equipamentos (mais rápido, mais barato)
                    - **vision**: Sempre envia imagem do P&ID (mais preciso para layout, mais caro)
                    """
                )
                st.info(f"🤖 Modo atual: **{chatbot_mode}**")
            
            # Exemplos de perguntas
            st.markdown("**💡 Exemplos de perguntas:**")
            example_col1, example_col2, example_col3 = st.columns(3)
            
            with example_col1:
                if st.button("📋 Listar equipamentos principais", use_container_width=True):
                    user_question = "Quais são os equipamentos principais identificados neste P&ID?"
                    ask_button = True
            
            with example_col2:
                if st.button("🎛️ Instrumentação do processo", use_container_width=True):
                    user_question = "Quais instrumentos de controle e medição estão presentes?"
                    ask_button = True
            
            with example_col3:
                if st.button("🔄 Descrever fluxo", use_container_width=True):
                    user_question = "Explique o fluxo do processo neste P&ID."
                    ask_button = True
            
            # Novo exemplo - pergunta visual
            example_col4, example_col5, example_col6 = st.columns(3)
            
            with example_col4:
                if st.button("📍 Localização de equipamento", use_container_width=True):
                    user_question = "Onde estão localizados os principais equipamentos no diagrama?"
                    ask_button = True
            
            with example_col5:
                if st.button("🔗 Conexões entre equipamentos", use_container_width=True):
                    user_question = "Quais equipamentos estão conectados entre si?"
                    ask_button = True
            
            with example_col6:
                if st.button("🛡️ Elementos de segurança", use_container_width=True):
                    user_question = "Quais são os elementos de segurança (PSVs, alarmes)?"
                    ask_button = True
            
            # Processa pergunta
            if ask_button and user_question:
                with st.spinner("🤔 Processando sua pergunta..."):
                    try:
                        # Pega o modo selecionado pelo usuário (se não existe chatbot_mode no escopo, usa hybrid)
                        selected_mode = chatbot_mode if 'chatbot_mode' in locals() else "hybrid"
                        
                        response = requests.post(
                            CHAT_URL,
                            params={
                                "pid_id": st.session_state.pid_id,
                                "question": user_question,
                                "mode": selected_mode
                            },
                            timeout=120  # Aumentado para 120s para permitir processamento de imagens
                        )
                        
                        if response.status_code == 200:
                            chat_data = response.json()
                            answer = chat_data.get("answer", "Desculpe, não consegui gerar uma resposta.")
                            mode_used = chat_data.get("mode_used", "unknown")
                            
                            # Adiciona ao histórico com informação do modo
                            st.session_state.chat_history.append({
                                "question": user_question,
                                "answer": answer,
                                "mode_used": mode_used
                            })
                            
                            # Recarrega a página para mostrar a nova mensagem
                            st.rerun()
                        else:
                            st.error(f"❌ Erro ao processar pergunta: {response.status_code} - {response.text}")
                    
                    except Exception as e:
                        st.error(f"❌ Erro ao conectar com o chatbot: {e}")
            
            # Botão para limpar histórico
            if st.session_state.chat_history:
                if st.button("🗑️ Limpar histórico de conversação"):
                    st.session_state.chat_history = []
                    st.rerun()










