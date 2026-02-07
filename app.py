import streamlit as st
import pdfplumber
import google.generativeai as genai
import os
import time
import zipfile
import io
from datetime import datetime
from dotenv import load_dotenv

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="S Consult - Sistema Integrado",
    page_icon="🏗️",
    layout="wide"
)

# --- 2. ESTILO VISUAL (DARK MODE) ---
st.markdown("""
<style>
    .result-container {
        background-color: #1E1E1E;
        padding: 25px;
        border-radius: 10px;
        border-left: 5px solid #F4B400;
        color: #E0E0E0;
        font-family: 'Segoe UI', sans-serif;
        margin-bottom: 20px;
    }
    .stButton>button {
        border-radius: 8px;
        height: 50px;
        font-weight: bold;
    }
    [data-testid="stSidebar"] {
        background-color: #111;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. CARREGAR CHAVES ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]

if api_key:
    genai.configure(api_key=api_key)
else:
    st.error("❌ Chave de API não encontrada! Verifique os Secrets.")
    st.stop()

# Inicializa memória
if 'historico' not in st.session_state:
    st.session_state.historico = []

# --- 4. FUNÇÕES DO SISTEMA ---

def listar_pdfs(diretorio='.'):
    """Procura PDFs em todas as subpastas."""
    lista_pdfs = []
    for root, dirs, files in os.walk(diretorio):
        if '.git' in root: continue
        for file in files:
            if file.lower().endswith(".pdf"):
                caminho_completo = os.path.join(root, file)
                lista_pdfs.append(caminho_completo)
    return lista_pdfs

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted: text += extracted + "\n"
    except:
        return None
    return text

def generate_summary(text):
    """Gera o resumo com inteligência artificial."""
    
    prompt = f"""
    ATUE COMO UM ENGENHEIRO CIVIL SÊNIOR DA S CONSULT.
    
    Analise o texto técnico abaixo extraído de um relatório de vistoria.
    Gere um relatório técnico formal.
    
    ESTRUTURA OBRIGATÓRIA:
    1. 🏢 OBJETO DA VISTORIA
    2. ⚠️ PRINCIPAIS ANOMALIAS IDENTIFICADAS (Bullet points)
    3. 🛠️ RECOMENDAÇÕES TÉCNICAS
    4. 📋 CONCLUSÃO TÉCNICA

    Texto do Relatório:
    {text}
    """
    
    # Tenta usar o modelo 1.5 Pro (Mais potente)
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # Se der erro, usa o modelo de backup
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            return response.text
        except Exception as e2:
            return f"❌ Erro na IA: {e}. Verifique sua chave API."

# --- 5. BARRA LATERAL (LOGO E HISTÓRICO) ---
with st.sidebar:
    # --- AQUI ESTÁ A MUDANÇA PARA O SEU LOGO ---
    if os.path.exists("Logo.jpeg"):
        st.image("Logo.jpeg", use_container_width=True)
    elif os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.header("🏗️ S Consult")
    # -------------------------------------------
    
    st.markdown("---")
    st.subheader("🕒 Histórico Recente")
    
    if len(st.session_state.historico) > 0:
        for item in reversed(st.session_state.historico[-5:]):
            st.text(f"⏱️ {item['hora']}")
            st.caption(f"📄 {item['trecho']}")
            st.markdown("---")
    else:
        st.info("Nenhuma análise feita hoje.")

# --- 6. ÁREA PRINCIPAL ---

st.title("Sistema de Engenharia Inteligente")
st.markdown("---")

# Seleção de Arquivo
todos_pdfs = listar_pdfs()

if not todos_pdfs:
    st.warning("⚠️ Nenhum PDF encontrado. Adicione arquivos na pasta do projeto.")
else:
    opcoes = {os.path.relpath(p): p for p in todos_pdfs}
    nome_arquivo = st.selectbox("📂 Selecione o Relatório:", list(opcoes.keys()))
    caminho_real = opcoes[nome_arquivo]
    
    chave_memoria = f"resumo_{caminho_real}"

    # Lógica de Geração
    if chave_memoria in st.session_state:
        resumo = st.session_state[chave_memoria]
        st.success("✅ Relatório recuperado da memória (Rápido!)")
    else:
        if st.button("✨ GERAR RELATÓRIO TÉCNICO", type="primary"):
            with st.spinner("👷‍♂️ A IA S-Consult está analisando o projeto..."):
                texto = extract_text_from_pdf(caminho_real)
                
                if texto and len(texto) > 50:
                    resumo = generate_summary(texto)
                    
                    st.session_state[chave_memoria] = resumo
                    hora_atual = datetime.now().strftime("%H:%M")
                    st.session_state.historico.append({
                        "hora": hora_atual,
                        "trecho": os.path.basename(caminho_real)[:25]+"..."
                    })
                    
                    st.toast("⏳ Pausa de 15s para proteger a cota...")
                    time.sleep(15) 
                    st.rerun()
                else:
                    st.error("Erro: O PDF parece ser uma imagem digitalizada.")

    # Downloads
    if chave_memoria in st.session_state:
        resumo = st.session_state[chave_memoria]
        
        st.markdown("### 📝 Relatório Final")
        st.markdown(f'<div class="result-container">{resumo}</div>', unsafe_allow_html=True)
        
        st.subheader("📥 Downloads do Trecho")
        
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.download_button("📄 Baixar Resumo (.txt)", resumo, file_name=f"Resumo_{os.path.basename(caminho_real)}.txt")
        with c2:
            with open(caminho_real, "rb") as f:
                st.download_button("📑 Baixar PDF Original", f, file_name=os.path.basename(caminho_real))
        with c3:
            pasta_pai = os.path.dirname(caminho_real)
            imgs = [f for f in os.listdir(pasta_pai) if f.lower().endswith(('.png','.jpg','.jpeg'))]
            
            if imgs:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zf:
                    for img in imgs:
                        zf.write(os.path.join(pasta_pai, img), arcname=img)
                st.download_button(f"📸 Baixar {len(imgs)} Fotos (.zip)", zip_buffer.getvalue(), file_name="Fotos_Trecho.zip", mime="application/zip")
            else:
                st.info("🚫 Sem fotos na pasta")
    
    st.markdown("---")
    if st.button("🔄 Nova Análise / Limpar"):
        if chave_memoria in st.session_state:
            del st.session_state[chave_memoria]
        st.rerun()

st.caption("S Consult Engenharia • Inteligência Artificial")