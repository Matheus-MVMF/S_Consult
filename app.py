import streamlit as st
import os
from datetime import datetime
import backend  # Importa nossa lógica separada

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="S Consult | Engenharia AI", page_icon="🏗️", layout="wide")

# Verifica chave de API (Usando a função do backend)
if not backend.verificar_chave():
    st.error("❌ ERRO CRÍTICO: Chave de API não encontrada! Verifique o arquivo .env")
    st.stop()

# --- CARREGAR CSS (CORREÇÃO AQUI: encoding="utf-8") ---
with open("style.css", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- VARIÁVEIS DE MEMÓRIA ---
if 'historico' not in st.session_state: st.session_state.historico = []
if 'modelo_atual' not in st.session_state: st.session_state.modelo_atual = None

# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists("Logo.jpeg"):
        st.image("Logo.jpeg", use_container_width=True)
    else:
        st.warning("⚠️ Salve a imagem 'Logo.jpeg' na pasta.")
        st.title("S CONSULT")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Auto-Detecção (Backend)
    if not st.session_state.modelo_atual:
        st.session_state.modelo_atual = backend.obter_modelo_inteligente()
    
    st.markdown("### 🕒 Histórico Recente")
    if not st.session_state.historico:
        st.markdown("<span style='font-size:12px; color:#666;'>Nenhuma análise hoje.</span>", unsafe_allow_html=True)
    else:
        for item in reversed(st.session_state.historico):
            with st.expander(f"📄 {item['hora']} - {item['trecho']}"):
                st.download_button("📥 Baixar TXT", item['conteudo'], file_name=f"Resumo_{item['trecho']}.txt")

# --- ÁREA CENTRAL ---
col_l, col_center, col_r = st.columns([1, 8, 1])

with col_center:
    st.markdown("# Portal de Engenharia")
    st.markdown("<h4 style='color: #888; font-weight: 400;'>Gerador de Relatórios Técnicos LVC</h4>", unsafe_allow_html=True)
    st.write("") 

    # --- BUSCA E BOTÃO ---
    col_input, col_btn = st.columns([5, 1], vertical_alignment="bottom") 
    
    with col_input:
        termo_busca = st.text_input("", placeholder="🔍 Digite o nome do trecho...", label_visibility="collapsed")
    
    with col_btn:
        btn_pesquisar = st.button("🔎 BUSCAR")

    # LÓGICA DE INTERAÇÃO
    if termo_busca:
        # Chama a função do backend
        arquivos = backend.encontrar_arquivos_pdf(termo_busca, os.getcwd())
        
        if not arquivos:
            st.warning(f"⚠️ Nenhum arquivo encontrado com: '{termo_busca}'")
        else:
            st.write("")
            st.markdown(f"**✅ {len(arquivos)} arquivo(s) localizado(s):**")
            
            # Seleção
            arquivo_selecionado = st.selectbox(
                "Selecione o arquivo:", 
                arquivos, 
                format_func=lambda x: os.path.basename(x), 
                label_visibility="collapsed"
            )
            
            st.write("") 
            
            # Botão de Gerar
            if st.button("✨ GERAR RELATÓRIO DETALHADO", type="primary"):
                with st.spinner("👷‍♂️ Engenharia AI processando dados..."):
                    
                    # Chama funções do backend para ler e gerar
                    texto_pdf = backend.ler_pdf(arquivo_selecionado)
                    
                    if texto_pdf and len(texto_pdf) > 50:
                        resumo = backend.gerar_resumo_tecnico(texto_pdf, st.session_state.modelo_atual)
                        
                        # Salva histórico
                        hora = datetime.now().strftime("%H:%M")
                        nome_curto = os.path.basename(arquivo_selecionado)[:20]
                        st.session_state.historico.append({"hora": hora, "trecho": nome_curto, "conteudo": resumo})
                        
                        # Mostra resultado
                        st.markdown("### 📝 Relatório Final")
                        st.markdown(f'<div class="result-container">{resumo}</div>', unsafe_allow_html=True)
                        
                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col2:
                            st.download_button(
                                label="📥 BAIXAR ARQUIVO .TXT",
                                data=resumo,
                                file_name=f"Resumo_SConsult_{os.path.basename(arquivo_selecionado)}.txt",
                                mime="text/plain",
                                use_container_width=True
                            )
                    else:
                        st.error("❌ Erro: PDF sem texto selecionável.")

# Rodapé
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("<center><span style='font-size:18px; color:#E0BC00;'>S CONSULT ENGENHARIA © 2026</span></center>", unsafe_allow_html=True)