import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials
import requests # Necessário para as notificações

# --- 1. CONFIGURAÇÃO ---
CHAVE_GROQ = "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"
ID_PLANILHA = "1WTM3bb9-l8_C4odgvFPLaNUJDnvvrHGCqyQwNCvEKNM"
TOPICO_NTFY = "calyo_assist_richard_2024" # O nome que criaste na app ntfy
NOME_DONO = "Richard" 

client = Groq(api_key=CHAVE_GROQ)

st.set_page_config(page_title="Calyo Assist", page_icon="🧠", layout="centered")

# --- 2. FUNÇÃO DE NOTIFICAÇÃO ---
def enviar_notificacao(titulo, mensagem):
    try:
        requests.post(f"https://ntfy.sh/{TOPICO_NTFY}", 
            data=mensagem.encode('utf-8'),
            headers={
                "Title": titulo,
                "Priority": "high",
                "Tags": "brain"
            })
        return True
    except:
        return False

# --- 3. CONEXÃO E RAG (Resumo do Código Anterior) ---
@st.cache_resource
def conectar_base_de_dados():
    if "gcp_service_account" in st.secrets:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_key(ID_PLANILHA).get_worksheet(0)
    return None

sheet = conectar_base_de_dados()

def carregar_mentalidade():
    if not sheet: return "Base offline."
    try:
        registros = sheet.get_all_records()
        historico = [f"{str(r.get('role', '')).upper()}: {r.get('content', '')}" for r in registros]
        return "\n".join(historico[-50:])
    except: return "Erro na memória."

# --- 4. INTERFACE ---
st.title("🧠 Calyo Assist")

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.memoria_rag = carregar_mentalidade()

# Barra lateral com botão de teste
with st.sidebar:
    st.write(f"Operador: {NOME_DONO}")
    if st.button("Teste de Alerta 🚨"):
        if enviar_notificacao("Calyo Assist", "Conexão de alerta estabelecida, Richard."):
            st.success("Notificação enviada!")
        else:
            st.error("Falha no envio.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. LOGICA DE CONVERSA ---
if prompt := st.chat_input("Comando..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    if sheet:
        try: sheet.append_row([NOME_DONO, "Unica", "user", prompt])
        except: pass

    with st.chat_message("assistant"):
        memoria = st.session_state.get("memoria_rag", "")
        # Instrução para o Calyo decidir se envia notificação
        instrucao_alerta = "\nIMPORTANTE: Se o Richard pedir para ser lembrado ou se algo for urgente, termine a resposta com '[ALERTA: mensagem]'."
        
        try:
            comp = client.chat.completions.create(
                messages=[{"role": "system", "content": "Seu nome é Calyo Assist. Seja sério e sensato." + instrucao_alerta + "\n\nMEMÓRIA:\n" + memoria}] + st.session_state.messages,
                model="llama-3.3-70b-versatile",
                temperature=0.4
            )
            resposta = comp.choices[0].message.content
            
            # Verificar se a IA decidiu enviar um alerta
            if "[ALERTA:" in resposta:
                msg_alerta = resposta.split("[ALERTA:")[1].split("]")[0]
                enviar_notificacao("Calyo Assist - Urgente", msg_alerta)
                resposta = resposta.split("[ALERTA:")[0] # Remove o código do texto final

            st.write(resposta)
            if sheet: sheet.append_row([NOME_DONO, "Unica", "assistant", resposta])
            st.session_state.messages.append({"role": "assistant", "content": resposta})
        except Exception as e:
            st.error(f"Erro: {e}")
            
