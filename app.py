import streamlit as st
import os
import time
import zipfile
import io
import pdfplumber
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="S Consult | Engenharia AI", page_icon="🏗️", layout="wide")

# --- 1. CONFIGURAÇÃO DE CHAVES E API ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]

if api_key:
    genai.configure(api_key=api_key)
else:
    st.error("❌ ERRO CRÍTICO: Chave de API não encontrada! Verifique o arquivo .env ou Secrets.")
    st.stop()

# --- 2. CARREGAR CSS ---
# Tenta carregar seu arquivo style.css. Se falhar, usa um estilo de emergência.
try:
    with open("style.css", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except:
    st.markdown("""
    <style>
        .result-container { background-color: #1E1E1E; padding: 25px; border-radius: 10px; border-left: 5px solid #F4B400; color: #E0E0E0; }
        .stButton>button { width: 100%; font-weight: bold; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. VARIÁVEIS DE MEMÓRIA ---
if 'historico' not in st.session_state: st.session_state.historico = []

# --- 4. FUNÇÕES DO SISTEMA (INTEGRADAS) ---
def encontrar_arquivos_pdf(termo, diretorio):
    resultados = []
    for root, dirs, files in os.walk(diretorio):
        if '.git' in root: continue
        for file in files:
            if file.lower().endswith(".pdf"):
                if termo.lower() in file.lower():
                    resultados.append(os.path.join(root, file))
    return resultados

def ler_pdf(caminho_pdf):
    texto = ""
    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t: texto += t + "\n"
    except: return None
    return texto

def gerar_resumo_tecnico(texto):
    """Gera o resumo com IA - Tenta 1.5 Pro, se falhar usa 1.5 Flash"""
    prompt = f"""
    ATUE COMO UM ENGENHEIRO CIVIL SÊNIOR DA S CONSULT.
    Analise o texto abaixo e gere um relatório técnico formal.
    
    ESTRUTURA OBRIGATÓRIA:
    1. 🏢 OBJETO DA VISTORIA
    2. ⚠️ PRINCIPAIS ANOMALIAS (Bullet points)
    3. 🛠️ RECOMENDAÇÕES TÉCNICAS
    4. 📋 CONCLUSÃO TÉCNICA
    
    Texto: {texto[:40000]} 
    """
    
    # Tenta usar a Ferrari (1.5 Pro)
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        return model.generate_content(prompt).text
    except Exception as e:
        # Se der erro, tenta o Flash (Backup Rápido)
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            return model.generate_content(prompt).text
        except Exception as e2:
            return f"❌ Erro na IA: {e}. Verifique sua chave API."

# --- 5. SIDEBAR (LOGOTIPO E HISTÓRICO) ---
with st.sidebar:
    if os.path.exists("Logo.jpeg"):
        st.image("Logo.jpeg", use_container_width=True)
    elif os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.title("S CONSULT")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🕒 Histórico Recente")
    
    if not st.session_state.historico:
        st.caption("Nenhuma análise hoje.")
    else:
        for item in reversed(st.session_state.historico[-5:]):
            st.caption(f"📄 {item['hora']} - {item['trecho']}")

# --- 6. ÁREA CENTRAL (LAYOUT DO APP (1).PY) ---
col_l, col_center, col_r = st.columns([1, 8, 1])

with col_center:
    st.markdown("# Portal de Engenharia")
    st.markdown("<h4 style='color: #888; font-weight: 400;'>Gerador de Relatórios Técnicos LVC</h4>", unsafe_allow_html=True)
    st.write("") 

    # --- BUSCA E BOTÃO ---
    col_input, col_btn = st.columns([5, 1], vertical_alignment="bottom") 
    
    with col_input:
        termo_busca = st.text_input("", placeholder="🔍 Digite o nome do trecho (Ex: TD-09)...", label_visibility="collapsed")
    
    with col_btn:
        btn_pesquisar = st.button("🔎 BUSCAR")

    # LÓGICA DE INTERAÇÃO
    if termo_busca:
        arquivos = encontrar_arquivos_pdf(termo_busca, os.getcwd())
        
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
            
            chave_memoria = f"resumo_{arquivo_selecionado}"
            st.write("") 
            
            # --- BOTÃO DE GERAR ---
            if chave_memoria in st.session_state:
                resumo = st.session_state[chave_memoria]
                st.success("✅ Relatório carregado da memória!")
            else:
                if st.button("✨ GERAR RELATÓRIO DETALHADO", type="primary"):
                    with st.spinner("👷‍♂️ Engenharia AI processando dados..."):
                        texto_pdf = ler_pdf(arquivo_selecionado)
                        
                        if texto_pdf and len(texto_pdf) > 50:
                            resumo = gerar_resumo_tecnico(texto_pdf)
                            
                            # Salva memória
                            st.session_state[chave_memoria] = resumo
                            hora = datetime.now().strftime("%H:%M")
                            nome_curto = os.path.basename(arquivo_selecionado)[:20]
                            st.session_state.historico.append({"hora": hora, "trecho": nome_curto})
                            
                            # Pausa de segurança
                            st.toast("⏳ Pausa de 10s para proteger a cota...")
                            time.sleep(10)
                            st.rerun()
                        else:
                            st.error("❌ Erro: PDF ilegível (pode ser imagem scanneada).")

            # --- EXIBIÇÃO E DOWNLOADS ---
            if chave_memoria in st.session_state:
                resumo = st.session_state[chave_memoria]
                
                st.markdown("### 📝 Relatório Final")
                st.markdown(f'<div class="result-container">{resumo}</div>', unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.subheader("📥 Downloads do Trecho")
                
                c1, c2, c3 = st.columns(3)
                
                with c1:
                    st.download_button("📄 Baixar Resumo (.txt)", resumo, file_name=f"Resumo_{os.path.basename(arquivo_selecionado)}.txt", use_container_width=True)
                with c2:
                    with open(arquivo_selecionado, "rb") as f:
                        st.download_button("📑 Baixar PDF Original", f, file_name=os.path.basename(arquivo_selecionado), mime="application/pdf", use_container_width=True)
                with c3:
                    pasta_pai = os.path.dirname(arquivo_selecionado)
                    imgs = [f for f in os.listdir(pasta_pai) if f.lower().endswith(('.png','.jpg','.jpeg'))]
                    if imgs:
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w") as zf:
                            for img in imgs:
                                zf.write(os.path.join(pasta_pai, img), arcname=img)
                        st.download_button(f"📸 Baixar {len(imgs)} Fotos (.zip)", zip_buffer.getvalue(), file_name="Fotos_Trecho.zip", mime="application/zip", use_container_width=True)
                    else:
                        st.info("🚫 Sem fotos")

                # Botão Limpar
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🔄 Nova Pesquisa / Limpar"):
                    if chave_memoria in st.session_state:
                        del st.session_state[chave_memoria]
                    st.rerun()

# Rodapé
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("<center><span style='font-size:18px; color:#E0BC00;'>S CONSULT ENGENHARIA © 2026</span></center>", unsafe_allow_html=True)