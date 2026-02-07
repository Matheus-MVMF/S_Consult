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
    st.error("❌ ERRO: Chave de API não encontrada! Verifique o .env")
    st.stop()

# --- 2. CARREGAR CSS (VISUAL AMARELO/PRETO CLÁSSICO) ---
st.markdown("""
<style>
    /* Fundo e Textos */
    .stApp { background-color: #0b0b0b; color: #e0e0e0; }
    [data-testid="stSidebar"] { background-color: #141414; border-right: 1px solid #333; }
    
    /* Títulos Amarelos */
    h1, h2, h3, h4 { color: #ffffff !important; font-family: 'Segoe UI', sans-serif; }
    
    /* Botões Amarelos (Estilo Portal) */
    .stButton>button {
        background: linear-gradient(180deg, #F4B400 0%, #D49B00 100%);
        color: #000;
        border: none;
        border-radius: 8px;
        font-weight: 800;
        height: 50px;
        text-transform: uppercase;
    }
    .stButton>button:hover { background: #FFC107; color: black; }
    
    /* Campo de Busca */
    .stTextInput>div>div>input {
        background-color: #1f1f1f; color: white; border: 1px solid #333; height: 50px;
    }

    /* Card de Resultado */
    .result-container {
        background-color: #1a1a1a;
        border: 1px solid #333;
        border-left: 6px solid #F4B400;
        border-radius: 8px;
        padding: 30px;
        margin-top: 25px;
        color: #d1d1d1;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. MEMÓRIA E FUNÇÕES ---
if 'historico' not in st.session_state: st.session_state.historico = []

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
    """
    Usa o Gemini 1.5 Flash - O mais estável e rápido para contas gratuitas.
    """
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
    try:
        # Tenta o 1.5 Flash (Moderno)
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model.generate_content(prompt).text
    except Exception as e:
        # Se falhar, tenta o Pro antigo (Compatibilidade máxima)
        try:
            model = genai.GenerativeModel('gemini-pro')
            return model.generate_content(prompt).text
        except Exception as e2:
            return f"❌ ERRO NA IA: {e2}. Tente reiniciar o app no menu superior."

# --- 4. BARRA LATERAL (LOGO) ---
with st.sidebar:
    # Tenta achar o logo
    if os.path.exists("Logo.jpeg"): st.image("Logo.jpeg", use_container_width=True)
    elif os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    else: st.header("🏗️ S CONSULT")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🕒 Histórico")
    if st.session_state.historico:
        for item in reversed(st.session_state.historico[-5:]):
            st.caption(f"📄 {item['hora']} - {item['trecho']}")
    else:
        st.caption("Nenhuma análise hoje.")

# --- 5. ÁREA PRINCIPAL ---
col_l, col_center, col_r = st.columns([1, 8, 1])

with col_center:
    st.markdown("# Portal de Engenharia")
    st.markdown("<h4 style='color: #888; font-weight: 400;'>Gerador de Relatórios Técnicos LVC</h4>", unsafe_allow_html=True)
    st.write("") 

    # Busca
    col_input, col_btn = st.columns([5, 1], vertical_alignment="bottom") 
    with col_input:
        termo_busca = st.text_input("", placeholder="🔍 Digite o nome do trecho...", label_visibility="collapsed")
    with col_btn:
        btn_pesquisar = st.button("🔎 BUSCAR")

    if termo_busca:
        arquivos = encontrar_arquivos_pdf(termo_busca, os.getcwd())
        
        if not arquivos:
            st.warning(f"⚠️ Nenhum arquivo encontrado com: '{termo_busca}'")
        else:
            st.success(f"✅ {len(arquivos)} arquivo(s) localizado(s)")
            
            # Seleção
            arquivo_selecionado = st.selectbox("Selecione:", arquivos, format_func=lambda x: os.path.basename(x))
            chave_memoria = f"resumo_{arquivo_selecionado}"
            st.write("") 
            
            # Botão Gerar
            if chave_memoria in st.session_state:
                resumo = st.session_state[chave_memoria]
                st.info("📂 Relatório carregado da memória!")
            else:
                if st.button("✨ GERAR RELATÓRIO DETALHADO", type="primary"):
                    with st.spinner("👷‍♂️ Engenharia AI processando dados..."):
                        texto_pdf = ler_pdf(arquivo_selecionado)
                        
                        if texto_pdf and len(texto_pdf) > 50:
                            resumo = gerar_resumo_tecnico(texto_pdf)
                            
                            if "ERRO" not in resumo:
                                st.session_state[chave_memoria] = resumo
                                hora = datetime.now().strftime("%H:%M")
                                nome_curto = os.path.basename(arquivo_selecionado)[:20]
                                st.session_state.historico.append({"hora": hora, "trecho": nome_curto})
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(resumo)
                        else:
                            st.error("❌ Erro: PDF ilegível.")

            # Resultados e Downloads
            if chave_memoria in st.session_state:
                resumo = st.session_state[chave_memoria]
                
                st.markdown("### 📝 Relatório Final")
                st.markdown(f'<div class="result-container">{resumo}</div>', unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("### 📥 Downloads do Trecho")
                
                # --- AQUI ESTÃO OS BOTÕES NOVOS ---
                c1, c2, c3 = st.columns(3)
                
                # 1. Resumo TXT
                with c1:
                    st.download_button("📄 Baixar Resumo (.txt)", resumo, file_name="Resumo.txt", use_container_width=True)
                
                # 2. PDF Original
                with c2:
                    with open(arquivo_selecionado, "rb") as f:
                        st.download_button("📑 Baixar PDF Original", f, file_name=os.path.basename(arquivo_selecionado), mime="application/pdf", use_container_width=True)
                
                # 3. Fotos ZIP (Automático)
                with c3:
                    pasta_pai = os.path.dirname(arquivo_selecionado)
                    imgs = [f for f in os.listdir(pasta_pai) if f.lower().endswith(('.png','.jpg','.jpeg'))]
                    
                    if imgs:
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w") as zf:
                            for img in imgs:
                                zf.write(os.path.join(pasta_pai, img), arcname=img)
                        st.download_button(f"📸 Baixar {len(imgs)} Fotos (.zip)", zip_buffer.getvalue(), file_name="Fotos.zip", mime="application/zip", use_container_width=True)
                    else:
                        st.info("🚫 Sem fotos na pasta")

                # Limpar
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🔄 Nova Pesquisa / Limpar"):
                    if chave_memoria in st.session_state: del st.session_state[chave_memoria]
                    st.rerun()

st.markdown("<br><br><center><span style='color:#666;'>S CONSULT ENGENHARIA © 2026</span></center>", unsafe_allow_html=True)