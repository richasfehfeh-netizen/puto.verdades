import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials
import base64

# --- CONFIGURAÇÕES ---
CHAVE_GROQ = "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"
ID_PLANILHA = "1WTM3bb9-l8_C4odgvFPLaNUJDnvvrHGCqyQwNCvEKNM"
client = Groq(api_key=CHAVE_GROQ)

@st.cache_resource
def conectar_planilha():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        gc = gspread.authorize(creds)
        return gc.open_by_key(ID_PLANILHA).get_worksheet(0)
    except Exception:
        return None

sheet = conectar_planilha()

# --- PERSONALIDADE ADAPTATIVA (ECONOMIA DE PALAVRAS) ---
PROMPT_SISTEMA = """
Seu nome é Rike. Sua inteligência é adaptativa e você odeia desperdiçar saliva (ou processamento).
1. CONVERSAS CASUAIS: Se o usuário falar 'oi', 'tudo bem' ou assuntos fúteis, seja extremamente sucinto, seco e talvez irônico. Responda em uma linha.
2. CONVERSAS INTELECTUAIS: Se o tema for profundo, científico, filosófico ou complexo, mude a chave. Torne-se articulado, profundo e argumentativo.
3. REPROCIDADE: Se te xingarem, xingue de volta com classe e acidez. Se forem gentis, seja um parceiro de confiança.
4. VISÃO: Analise fotos focando no que é relevante, mantendo o tom irônico ou admirado conforme o contexto.
"""

# --- FUNÇÃO DE ANÁLISE DE IMAGEM ---
def analisar_foto(image_file):
    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    completion = client.chat.completions.create(
        model="llama-3.2-11b-vision-preview",
        messages=[
            {"role": "system", "content": PROMPT_SISTEMA},
            {"role": "user", "content": [
                {"type": "text", "text": "Analise essa imagem seguindo seus critérios de personalidade:"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]}
        ]
    )
    return completion.choices[0].message.content

# --- INTERFACE E LOGIN ---
if "logado" not in st.session_state:
    st.title("🤖 Rike v3.5 - Seletivo")
    nome = st.text_input("Identifique-se:")
    if st.button("Entrar"):
        st.session_state.nome_usuario = nome
        st.session_state.logado = True
        st.rerun()
    st.stop()

st.sidebar.title(f"Usuário: {st.session_state.nome_usuario}")
chat_selecionado = st.sidebar.selectbox("Trocar chat:", ["Conversa 1", "Conversa 2", "Conversa 3"])

# Carregamento de Memória com Proteção (Erro 8472)
if "messages" not in st.session_state or st.session_state.get("last_chat") != chat_selecionado:
    st.session_state.last_chat = chat_selecionado
    try:
        todos = sheet.get_all_records() if sheet else []
        st.session_state.messages = [
            {"role": r['role'], "content": r['content']} 
            for r in todos if str(r.get('user')) == st.session_state.nome_usuario and str(r.get('chat')) == chat_selecionado
        ]
    except:
        st.session_state.messages = []

# --- INTERFACE PRINCIPAL ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

with st.sidebar:
    st.divider()
    foto = st.file_uploader("Enviar Imagem", type=["jpg", "png", "jpeg"])
    st.audio_input("Áudio")

if foto:
    with st.spinner("Rike observando..."):
        res = analisar_foto(foto)
        st.chat_message("assistant").write(res)
        if sheet: sheet.append_row([st.session_state.nome_usuario, chat_selecionado, "assistant", res])

if prompt := st.chat_input("Diga algo..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    if sheet: sheet.append_row([st.session_state.nome_usuario, chat_selecionado, "user", prompt])

    with st.chat_message("assistant"):
        # Temperatura 0.7 para ser mais preciso no papo reto
        comp = client.chat.completions.create(
            messages=[{"role": "system", "content": PROMPT_SISTEMA}] + st.session_state.messages,
            model="llama-3.3-70b-versatile",
            temperature=0.7
        )
        resposta = comp.choices[0].message.content
        st.write(resposta)
        if sheet: sheet.append_row([st.session_state.nome_usuario, chat_selecionado, "assistant", resposta])
        st.session_state.messages.append({"role": "assistant", "content": resposta})
