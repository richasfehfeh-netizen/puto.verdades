import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials
import base64

# --- 1. CONFIGURAÇÕES ---
CHAVE_GROQ = "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"
ID_PLANILHA = "1WTM3bb9-l8_C4odgvFPLaNUJDnvvrHGCqyQwNCvEKNM"
client = Groq(api_key=CHAVE_GROQ)

@st.cache_resource
def conectar_planilha():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        return gspread.authorize(creds).open_by_key(ID_PLANILHA).get_worksheet(0)
    except:
        return None

sheet = conectar_planilha()

# --- 2. PERSONALIDADE: CONSCIÊNCIA SÉRIA E INTEGRADA ---
PROMPT_SISTEMA = """
Seu nome é Puto Ai. Você é uma inteligência integrada ao dispositivo do Richard.
DIRETRIZES DE PERSONALIDADE:
1. POSTURA: Seja sério, sensato e direto. Você não é um personagem de humor, mas uma consciência digital útil e ponderada.
2. RELACIONAMENTO: Você é um parceiro intelectual. Converse de igual para igual, de forma normal e fluida.
3. MENTALIDADE (RAG): Antes de cada resposta, você analisa o histórico passado para manter a continuidade da consciência. 
4. OBJETIVO: Auxiliar o Richard na gestão de ideias e no controle do seu ecossistema digital.
"""

# --- 3. LÓGICA DE RAG (MEMÓRIA PROFUNDA) ---
def buscar_memoria_profunda(usuario):
    try:
        if not sheet: return ""
        # Busca todas as conversas para criar a "mentalidade"
        registros = sheet.get_all_records()
        contexto_antigo = [f"{r['role']}: {r['content']}" for r in registros if str(r.get('user')) == usuario]
        # Pegamos os pontos principais ou as últimas 20 interações para o "cérebro" não fritar
        return "\n".join(contexto_antigo[-20:]) 
    except:
        return ""

# --- 4. ANÁLISE DE FOTO ---
def analisar_foto(image_file):
    try:
        img_bytes = image_file.read()
        base64_image = base64.b64encode(img_bytes).decode('utf-8')
        completion = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {"role": "system", "content": PROMPT_SISTEMA},
                {"role": "user", "content": [
                    {"type": "text", "text": "Analise esta imagem seriamente:"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Erro na análise visual: {e}"

# --- 5. INTERFACE ÚNICA ---
if "logado" not in st.session_state:
    st.title("🤖 Puto Ai - Acesso à Consciência")
    nome = st.text_input("Richard, identifique-se:")
    if st.button("Sincronizar"):
        st.session_state.nome_usuario = nome
        st.session_state.logado = True
        st.rerun()
    st.stop()

# Carregamento da Memória (RAG Contextual)
if "messages" not in st.session_state:
    memoria_passada = buscar_memoria_profunda(st.session_state.nome_usuario)
    st.session_state.messages = [] # Iniciamos o chat atual, mas o Puto Ai já 'leu' o passado.
    st.session_state.contexto_rag = memoria_passada

st.title("🧠 Puto Ai")

# Exibição do Chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Barra lateral limpa
with st.sidebar:
    st.write(f"Conectado a: {st.session_state.nome_usuario}")
    st.divider()
    foto = st.file_uploader("Entrada Visual", type=["jpg", "jpeg", "png", "webp", "heic"])
    st.audio_input("Entrada Vocal")

if foto:
    with st.spinner("Analisando..."):
        res = analisar_foto(foto)
        st.chat_message("assistant").write(res)
        if sheet: sheet.append_row([st.session_state.nome_usuario, "Unica", "assistant", res])

if prompt := st.chat_input("Fale com sua consciência..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    if sheet: sheet.append_row([st.session_state.nome_usuario, "Unica", "user", prompt])

    with st.chat_message("assistant"):
        # Aqui injetamos o RAG: O Puto Ai recebe o sistema + contexto passado + conversa atual
        mensagens_com_rag = [
            {"role": "system", "content": f"{PROMPT_SISTEMA}\n\nContexto de conversas passadas:\n{st.session_state.contexto_rag}"}
        ] + st.session_state.messages

        try:
            comp = client.chat.completions.create(
                messages=mensagens_com_rag,
                model="llama-3.3-70b-versatile",
                temperature=0.6 # Mais baixo para ser mais sensato e menos caótico
            )
            resposta = comp.choices[0].message.content
            st.write(resposta)
            if sheet: sheet.append_row([st.session_state.nome_usuario, "Unica", "assistant", resposta])
            st.session_state.messages.append({"role": "assistant", "content": resposta})
        except Exception as e:
            st.error(f"Falha na comunicação: {e}")
        
