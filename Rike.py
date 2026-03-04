import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURAÇÃO ---
CHAVE_GROQ = "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" # Coloque sua chave Groq aqui
client_groq = Groq(api_key=CHAVE_GROQ)

def conectar_planilha():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    # Puxa os dados do Secrets do Streamlit
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    gc = gspread.authorize(creds)
    
    # SUBSTITUA ABAIXO PELO ID DA SUA PLANILHA
    ID_PLANILHA = "COLE_AQUI_O_ID_DA_SUA_PLANILHA" 
    return gc.open_by_key(ID_PLANILHA).sheet1

# Tenta estabelecer a conexão
try:
    sheet = conectar_planilha()
except Exception as e:
    st.error(f"Erro de Conexão: {e}")
    st.stop()

# --- LOGIN E MEMÓRIA ---
if "logado" not in st.session_state:
    st.title("🔐 Rike - Memória de Nuvem")
    nome = st.text_input("Quem está acessando?")
    if st.button("Entrar"):
        st.session_state.nome_usuario = nome
        try:
            # Tenta ler as mensagens
            todos = sheet.get_all_records()
            st.session_state.messages = [
                {"role": r["role"], "content": r["content"]} 
                for r in todos if str(r.get("user", "")) == nome
            ]
        except:
            st.session_state.messages = []
            
        st.session_state.logado = True
        st.rerun()
    st.stop()

st.title(f"🧠 Rike - Parceiro de {st.session_state.nome_usuario}")

# Exibe histórico
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- CHAT ---
if prompt := st.chat_input("Fale com o Rike..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Salva na Planilha
    try:
        sheet.append_row([st.session_state.nome_usuario, "user", prompt])
    except:
        st.warning("Erro ao salvar mensagem na nuvem, mas vou responder!")

    with st.chat_message("assistant"):
        instrucao = f"Seu nome é Rike. Parceiro de {st.session_state.nome_usuario}. Seja adaptativo."
        
        comp = client_groq.chat.completions.create(
            messages=[{"role": "system", "content": instrucao}] + st.session_state.messages,
            model="llama-3.3-70b-versatile",
            temperature=0.8
        )
        
        resp = comp.choices[0].message.content
        st.markdown(resp)
        
        try:
            sheet.append_row([st.session_state.nome_usuario, "assistant", resp])
        except:
            pass
            
        st.session_state.messages.append({"role": "assistant", "content": resp})
        
