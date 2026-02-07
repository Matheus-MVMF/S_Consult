import streamlit as st
import os
from datetime import datetime
import backend  # Importa sua lógica que já funciona
import zipfile  # <--- NOVO: Para zipar as fotos
import io       # <--- NOVO: Para criar o arquivo na memória

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="S Consult | Engenharia AI", page_icon="🏗️", layout="wide")

# Verifica chave de API (Usando a função do backend)
if not backend.verificar_chave():
    st.error("❌ ERRO CRÍTICO: Chave de API não encontrada! Verifique o arquivo .env")
    st.stop()

# --- CARREGAR CSS ---
try:
    with open("style.css", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except:
    pass # Se não achar o css, segue sem ele para não travar

# --- VARIÁVEIS DE MEMÓRIA ---
if 'historico' not in st.session_state: st.session_state.historico = []
if 'modelo_atual' not in st.session_state: st.session_state.modelo_atual = None

# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists("Logo.jpeg"):
        st.image("Logo.jpeg", use_container_width=True)
    elif os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.warning("⚠️ Logo não encontrado")
        st.title("S CONSULT")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Auto-Detecção (Backend)
    if not st.session_state.modelo_atual:
        st.session_state.modelo_atual = backend.obter_modelo_inteligente()
    
    st.markdown("### 🕒 Histórico Recente")
    if not st.session_state.historico:
        st.markdown("<span style='font-size:12px; color:#666;'>Nenhuma análise hoje.</span>", unsafe_allow_html=True)
    else:
        for item in reversed(st.session_state.historico[-5:]):
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
                        
                        # --- AQUI ESTÁ A MUDANÇA: 3 BOTÕES DE DOWNLOAD ---
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.subheader("📥 Central de Downloads")
                        
                        c1, c2, c3 = st.columns(3)
                        
                        # 1. Baixar TXT (O que já tinha)
                        with c1:
                            st.download_button(
                                label="📄 Baixar Resumo (.txt)",
                                data=resumo,
                                file_name=f"Resumo_SConsult_{os.path.basename(arquivo_selecionado)}.txt",
                                mime="text/plain",
                                use_container_width=True
                            )
                        
                        # 2. Baixar PDF Original (NOVO)
                        with c2:
                            with open(arquivo_selecionado, "rb") as pdf_file:
                                st.download_button(
                                    label="📑 Baixar PDF Original",
                                    data=pdf_file,
                                    file_name=os.path.basename(arquivo_selecionado),
                                    mime="application/pdf",
                                    use_container_width=True
                                )
                        
                        # 3. Baixar Fotos ZIP (NOVO - Automático)
                        with c3:
                            # Pega a pasta onde o PDF está
                            pasta_do_trecho = os.path.dirname(arquivo_selecionado)
                            # Procura imagens (jpg, png)
                            imagens = [f for f in os.listdir(pasta_do_trecho) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                            
                            if imagens:
                                # Cria o ZIP na memória
                                zip_buffer = io.BytesIO()
                                with zipfile.ZipFile(zip_buffer, "w") as zf:
                                    for img in imagens:
                                        caminho_img = os.path.join(pasta_do_trecho, img)
                                        zf.write(caminho_img, arcname=img)
                                
                                st.download_button(
                                    label=f"📸 Baixar {len(imagens)} Fotos (.zip)",
                                    data=zip_buffer.getvalue(),
                                    file_name="Fotos_Trecho.zip",
                                    mime="application/zip",
                                    use_container_width=True
                                )
                            else:
                                st.info("🚫 Sem fotos na pasta")
                        
                    else:
                        st.error("❌ Erro: PDF sem texto selecionável.")

# Rodapé
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("<center><span style='font-size:18px; color:#E0BC00;'>S CONSULT ENGENHARIA © 2026</span></center>", unsafe_allow_html=True)