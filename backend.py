# backend.py - A Lógica e Inteligência Artificial
import os
import pdfplumber
import google.generativeai as genai
from dotenv import load_dotenv

# Configuração Automática ao importar esse arquivo
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if api_key:
    genai.configure(api_key=api_key)

def verificar_chave():
    if not api_key:
        return False
    return True

def encontrar_arquivos_pdf(termo_busca, diretorio_raiz="."):
    arquivos = []
    for root, dirs, files in os.walk(diretorio_raiz):
        for file in files:
            if file.lower().endswith(".pdf") and termo_busca.lower() in file.lower():
                arquivos.append(os.path.join(root, file))
    return arquivos

def ler_pdf(caminho_arquivo):
    texto = ""
    try:
        with pdfplumber.open(caminho_arquivo) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted: texto += extracted + "\n"
    except: return None
    return texto

def obter_modelo_inteligente():
    try:
        modelos = genai.list_models()
        melhor = None
        for m in modelos:
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name: return m.name
                if 'pro' in m.name: melhor = m.name
        return melhor if melhor else 'models/gemini-1.5-flash'
    except:
        return 'models/gemini-1.5-flash'

def gerar_resumo_tecnico(texto_lvc, modelo_nome):
    prompt_sistema = """
    Você é um Engenheiro Rodoviário Sênior da S Consult.
    Sua tarefa é analisar os dados brutos de um LVC (Levantamento Visual Contínuo) e gerar um Relatório Técnico Detalhado.

    🚨 REGRAS DE OURO:
    1. **REGRA DO ZERO:** Se um defeito não for encontrado, escreva "Ocorrências: 0".
    2. **DETALHAMENTO:** Liste KM exato, Lado (LD/LE), Dimensões e Área/Volume.
    3. **MEIOS-FIOS:** Separe por estado (Bom, Regular, Ruim).
    4. **IMPLANTAÇÃO:** Liste onde precisa implantar.

    --- USE ESTE MODELO ---

    📍 Resumo Técnico – [Nome do Trecho]
    • Extensão aproximada: [X] km
    • Revestimento: [Tipo] com KMs
    • Acostamento: [Largura e tipo]

    > Pórticos
    [Listar ou "Não identificados"]

    ━━━━━━━━━━━━━━━
    > PISTA DE ROLAMENTO

    > Panelas Abertas (PA)
    • Ocorrências: [Total]
    • Área Total: [X] m²
    • Concentração crítica:
        [Listar KMs e quantidades]

    > Rebaixamentos Laterais (RL)
    • Ocorrências: [Total]
    • Área Total: [X] m²
    • Detalhes:
        * KM [X] | [Lado] | Dimensões: [X]m x [X]m | Área: [X] m²

    > Erosões
    • Ocorrências: [Total]
    • Volume Total: [X] m³
    • Detalhes:
        * KM [X] | [Lado] | Dimensões: [X]x[X]x[X]m | Volume: [X] m³

    > Áreas para Restauração
    • Ocorrências: [Total]
    • Extensão Total: [X] m
    • Trechos:
        * Km [X] a Km [Y] | Extensão: [X] m

    > Desgaste Superficial
    • Ocorrências: [Total]
    • Área Total: [X] m²
    • Trechos:
        * Km [X] a Km [Y] | Lado: [X] | Área: [X] m²

    ━━━━━━━━━━━━━━━
    > DRENAGEM & OBRAS DE ARTE

    > OAEs (Pontes/Viadutos)
    • Total: [X]
    • Localização: [Detalhes]

    > Passagens Molhadas
    • Total: [X]
    • Situação: [Detalhes]

    > Bueiros
    • Total: [X] unidades
    • Observação: [Resumo estados]

    > Meios-fios e Sarjetas (Existentes)
    • Total Geral: [X] m
    • Estado Meios-fios: Bom: [X]m | Regular: [X]m | Ruim: [X]m
    • Estado Sarjetas: Bom: [X]m | Regular: [X]m | Ruim: [X]m
    • Obs: [Comentários]

    > Meios-fios e Sarjetas (A Implantar)
    • Total Meios-fios: [X] m
    • Detalhamento:
        * Lado Esquerdo: [Listar KMs]
        * Lado Direito: [Listar KMs]

    ━━━━━━━━━━━━━━━
    > SINALIZAÇÃO RODOVIÁRIA

    > Horizontal (Existente)
    • Estado: [Situação]

    > Vertical (Existente)
    • Estado: [Situação]
    • Total de Placas: [X] unidades

    > Sinalização a Implantar
    • Placas de Regulamentação (R):
        * KM [X] | [Código] | [Lado]
    • Placas de Advertência (A):
        * KM [X] | [Código] | [Lado]

    ━━━━━━━━━━━━━━━
    > SERVIÇOS GERAIS
    > Roço Lateral
    • Extensão/Área: [X] ha
    • Obs: [Comentários]

    ━━━━━━━━━━━━━━━
    > OBSERVAÇÕES TÉCNICAS
    [Conclusão técnica]
    """

    try:
        model = genai.GenerativeModel(modelo_nome)
        response = model.generate_content(f"{prompt_sistema}\n\n--- DADOS BRUTOS DO PDF ---\n{texto_lvc}")
        return response.text
    except Exception as e:
        return f"Erro na IA: {e}"