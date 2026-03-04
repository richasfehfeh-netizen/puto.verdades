import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURAÇÃO ---
CHAVE_GROQ = "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"
client_groq = Groq(api_key=CHAVE_GROQ)

def conectar_planilha():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    # Busca os segredos que você configurou no painel do Streamlit
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    gc = gspread.authorize(creds)
    # Abre a planilha pelo nome exato
    return gc.open("Memoria_Rike").get_worksheet(0)

# Tenta estabelecer a conexão com a nuvem
try:
    sheet = conectar_planilha()
except Exception as e:
    st.error(f"Erro ao acessar a nuvem: {e}")
    st.info("Verifique se compartilhou a planilha com o e-mail da conta de serviço!")
    st.stop()

# --- LOGIN E CARREGAMENTO DE MEMÓRIA ---
if "logado" not in st.session_state:
    st.title("🔐 Rike - Memória de Nuvem")
    nome = st.text_input("Quem deseja acessar?")
    if st.button("Entrar"):
        st.session_state.nome_usuario = nome
        try:
            # Tenta ler os dados da planilha
            todos = sheet.get_all_records()
            st.session_state.messages = [
                {"role": r["role"], "content": r["content"]} 
                for r in todos if str(r.get("user", "")) == nome
            ]
        except Exception:
            # Se a planilha estiver sem dados abaixo dos títulos, começa vazio
            st.session_state.messages = []
            
        st.session_state.logado = True
        st.rerun()
    st.stop()

st.title(f"🧠 Rike - Parceiro de {st.session_state.nome_usuario}")

# Exibe o histórico salvo
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- ÁREA DE CHAT ---
if prompt := st.chat_input("Diga algo para minha memória..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Salva na Planilha Google
    sheet.append_row([st.session_state.nome_usuario, "user", prompt])

    with st.chat_message("assistant"):
        instrucao = f"Seu nome é Rike. Parceiro de {st.session_state.nome_usuario}. Use o histórico para ser adaptativo e profundo."
        
        comp = client_groq.chat.completions.create(
            messages=[{"role": "system", "content": instrucao}] + st.session_state.messages,
            model="llama-3.3-70b-versatile",
            temperature=0.8
        )
        
        resp = comp.choices[0].message.content
        st.markdown(resp)
        
        # Salva a resposta do Rike na Planilha
        sheet.append_row([st.session_state.nome_usuario, "assistant", resp])
        st.session_state.messages.append({"role": "assistant", "content": resp})
    
