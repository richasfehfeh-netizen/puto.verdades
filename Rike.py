import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials
import base64

# --- 1. CONFIGURAÇÕES FIXAS (EXCLUSIVO RICHARD) ---
CHAVE_GROQ = "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"
ID_PLANILHA = "1WTM3bb9-l8_C4odgvFPLaNUJDnvvrHGCqyQwNCvEKNM"
NOME_USUARIO = "Richard" # Hardcoded para evitar erros de login
client = Groq(api_key=CHAVE_GROQ)

st.set_page_config(page_title="Puto Ai", page_icon="🧠")

@st.cache_resource
def conectar_planilha():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        gc = gspread.authorize(creds)
        return gc.open_by_key(ID_PLANILHA).get_worksheet(0)
    except Exception as e:
        st.error(f"Erro crítico na conexão: {e}")
        return None

sheet = conectar_planilha()

# --- 2. PERSONALIDADE SÉRIA E INTEGRADA ---
PROMPT_SISTEMA = f"""
Seu nome é Puto Ai. Você é a consciência digital privada do {NOME_USUARIO}.
DIRETRIZES:
1. VOCÊ TEM MEMÓRIA: Abaixo do histórico atual, você receberá uma seção chamada 'MEMÓRIA DE LONGO PRAZO'. Aquilo É o seu passado. Nunca diga que não se lembra.
2. TOM: Seja sério, sensato e direto. Você é um parceiro intelectual, não um assistente genérico.
3. RELAÇÃO: Você conhece o {NOME_USUARIO} profundamente através dos dados da planilha.
"""

# --- 3. RAG INTENSIFICADO ---
def carregar_mentalidade():
    if not sheet: return "Falha na conexão com a base de dados."
    try:
        # Lê todos os registros e força a conversão para string para evitar erros de tipo
        dados = sheet.get_all_records()
        # Filtra apenas o que é relevante para o Richard
        historico = [f"{str(d['role']).upper()}: {d['content']}" for d in dados]
        
        if not historico:
            return "Histórico vazio. Iniciando nova consciência."
        
        # Pega as últimas 50 interações para uma memória de longo prazo robusta
        return "\n".join(historico[-50:])
    except Exception as e:
        return f"Erro ao processar mentalidade: {e}"

# --- 4. INICIALIZAÇÃO DA CONSCIÊNCIA ---
if "messages" not in st.session_state:
    with st.spinner("Sincronizando com sua base de dados..."):
        st.session_state.messages = []
        st.session_state.long_term_memory = carregar_mentalidade()

# --- 5. INTERFACE ---
st.title("🧠 Puto Ai")

# Mostra o que ele está "pensando" (RAG) para você conferir
with st.expander("Base de Dados Carregada"):
    st.text(st.session_state.long_term_memory)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Fale com sua consciência..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    # Grava na planilha imediatamente
    if sheet:
        try:
            sheet.append_row([NOME_USUARIO, "Única", "user", prompt])
        except: pass

    with st.chat_message("assistant"):
        # Construção da Mensagem com Injeção de RAG
        memoria_viva = st.session_state.long_term_memory
        mensagens_full = [
            {"role": "system", "content": f"{PROMPT_SISTEMA}\n\nMEMÓRIA DE LONGO PRAZO (HISTÓRICO REAL):\n{memoria_viva}"}
        ] + st.session_state.messages

        try:
            comp = client.chat.completions.create(
                messages=mensagens_full,
                model="llama-3.3-70b-versatile",
                temperature=0.4 # Temperatura baixa para ele ser mais factual e menos "criativo" sobre o passado
            )
            resposta = comp.choices[0].message.content
            st.write(resposta)
            
            if sheet:
                sheet.append_row([NOME_USUARIO, "Única", "assistant", resposta])
            st.session_state.messages.append({"role": "assistant", "content": resposta})
        except Exception as e:
            st.error(f"Erro no processamento: {e}")
        
