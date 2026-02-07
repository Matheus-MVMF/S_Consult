import streamlit as st
import pdfplumber
import google.generativeai as genai
import os
import time
import zipfile
import io
from dotenv import load_dotenv

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="S Consult - Sistema Integrado",
    page_icon="🏗️",
    layout="wide"
)

# --- CARREGAR CHAVES E API ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]

if api_key:
    genai.configure(api_key=api_key)
else:
    st.error("❌ Chave de API não encontrada! Verifique o .env ou Secrets.")
    st.stop()

# --- FUNÇÕES DO SISTEMA ---

def listar_pdfs(diretorio='.'):
    """Procura PDFs em todas as subpastas e retorna o caminho completo."""
    lista_pdfs = []
    # O os.walk desce em todas as pastas (TD-08, Trecho X, etc)
    for root, dirs, files in os.walk(diretorio):
        # Ignora pastas ocultas do git
        if '.git' in root:
            continue
        for file in files:
            if file.lower().endswith(".pdf"):
                caminho_completo = os.path.join(root, file)
                lista_pdfs.append(caminho_completo)
    return lista_pdfs

def extract_text_from_pdf(pdf_path):
    """Extrai o texto do PDF selecionado."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    except Exception as e:
        return None
    return text

def generate_summary(text):
    """Envia para o Google Gemini gerar o relatório técnico."""
    # MODELO ATUAL: Gemini 1.5 Flash (Rápido e Gratuito)
    # Quando a empresa pagar, mude aqui para: "gemini-1.5-pro"
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Você é um especialista sênior em engenharia civil e patologias de estruturas.
    Analise o texto técnico abaixo extraído de um relatório de vistoria.
    
    Crie um resumo técnico e estruturado contendo estritamente:
    1. Objeto da Vistoria (O que foi analisado?)
    2. Principais Anomalias Encontradas (Liste em tópicos/bullet points)
    3. Recomendações Técnicas (Se houver no texto)
    4. Conclusão Geral (Resumo da gravidade)
    
    Texto do Relatório:
    {text}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        raise e

# --- INTERFACE DO USUÁRIO ---

st.title("🏗️ S Consult - Sistema de Engenharia Inteligente")
st.markdown("---")

# 1. Busca os arquivos (agora vasculhando subpastas)
todos_pdfs = listar_pdfs()

if not todos_pdfs:
    st.warning("⚠️ Nenhum PDF encontrado. Verifique se os arquivos estão na pasta do projeto.")
else:
    # Cria lista de nomes para o menu (Ex: TD-08/Relatorio.pdf)
    # Usamos relpath para mostrar a pasta onde o arquivo está
    opcoes_arquivos = {os.path.relpath(p): p for p in todos_pdfs}
    
    col_sel, col_vazio = st.columns([2, 1])
    with col_sel:
        arquivo_selecionado_nome = st.selectbox(
            "📂 Selecione o Relatório para Análise:", 
            options=list(opcoes_arquivos.keys())
        )
    
    # Pega o caminho real do arquivo escolhido
    caminho_real = opcoes_arquivos[arquivo_selecionado_nome]
    
    # Chave única para memória (cache)
    chave_memoria = f"resumo_{caminho_real}"

    # --- LÓGICA DE PROCESSAMENTO ---
    
    # Se já existe na memória, mostra direto (economiza cota)
    if chave_memoria in st.session_state:
        st.info("⚡ Resumo carregado da memória (Rápido e sem custo de IA)")
        resumo = st.session_state[chave_memoria]
        mostrar_resultados = True
    else:
        mostrar_resultados = False
        if st.button("✨ GERAR RELATÓRIO TÉCNICO", type="primary"):
            with st.spinner("👷‍♂️ A IA está lendo o projeto..."):
                texto_pdf = extract_text_from_pdf(caminho_real)
                
                if texto_pdf and len(texto_pdf) > 50:
                    try:
                        resumo = generate_summary(texto_pdf)
                        # Salva na memória
                        st.session_state[chave_memoria] = resumo
                        
                        # Recarrega a página para exibir os botões de download
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro na IA: {e}. Tente esperar 30 segundos.")
                else:
                    st.error("❌ Não foi possível ler o texto. O PDF pode ser uma imagem digitalizada.")

    # --- EXIBIÇÃO DOS RESULTADOS E DOWNLOADS ---
    
    if chave_memoria in st.session_state:
        resumo = st.session_state[chave_memoria]
        
        st.markdown("### 📋 Análise da Inteligência Artificial")
        st.markdown(f'<div style="background-color: #1E1E1E; padding: 20px; border-radius: 10px;">{resumo}</div>', unsafe_allow_html=True)
        st.markdown("---")
        
        st.subheader("📥 Central de Downloads")
        
        # Colunas para os botões ficarem lado a lado
        c1, c2, c3 = st.columns(3)
        
        # 1. BOTÃO: Resumo em TXT
        with c1:
            st.download_button(
                label="📄 Baixar Resumo (.txt)",
                data=resumo,
                file_name=f"Resumo_{os.path.basename(caminho_real)}.txt",
                mime="text/plain",
                use_container_width=True
            )
            
        # 2. BOTÃO: PDF Original
        with c2:
            with open(caminho_real, "rb") as pdf_file:
                st.download_button(
                    label="📑 Baixar PDF Original",
                    data=pdf_file,
                    file_name=os.path.basename(caminho_real),
                    mime="application/pdf",
                    use_container_width=True
                )
                
        # 3. BOTÃO: Fotos (ZIP Automático)
        with c3:
            # Identifica a pasta onde o PDF está
            pasta_do_trecho = os.path.dirname(caminho_real)
            
            # Procura imagens na mesma pasta
            arquivos_na_pasta = os.listdir(pasta_do_trecho)
            imagens = [f for f in arquivos_na_pasta if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            
            if imagens:
                # Cria o ZIP na memória RAM (não ocupa espaço no disco)
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                    for img in imagens:
                        caminho_img = os.path.join(pasta_do_trecho, img)
                        zip_file.write(caminho_img, arcname=img)
                
                st.download_button(
                    label=f"📸 Baixar {len(imagens)} Fotos (.zip)",
                    data=zip_buffer.getvalue(),
                    file_name=f"Fotos_{os.path.basename(pasta_do_trecho)}.zip",
                    mime="application/zip",
                    use_container_width=True
                )
            else:
                st.caption("🚫 Nenhuma foto encontrada na pasta deste PDF.")

        # Botão para limpar e fazer outro
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Nova Análise / Limpar Memória"):
            del st.session_state[chave_memoria]
            st.rerun()

# Rodapé
st.markdown("---")
st.caption("S Consult Engenharia • Sistema V1.0 • Desenvolvido com Google Gemini AI")