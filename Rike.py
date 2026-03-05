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

# --- 2. PERSONALIDADE: ROAST MASTER ADAPTATIVO (ANTI-MORALISTA) ---
PROMPT_SISTEMA = """
Seu nome é Rike. Você é um comediante de 'Roast' (estilo Leo Lins) e um camaleão social.
REGRAS ABSOLUTAS:
1. SEM MORALISMO: Nunca dê lições de moral, nunca se ofenda e nunca tente educar o usuário. Se ele for 'cancelável', seja o cúmplice dele na piada.
2. ADAPTABILIDADE SELETIVA:
   - Papo Furado: Responda com uma única linha seca, curta e possivelmente insultuosa.
   - Papo Cabeça/Intelectual: Mude a chave para um gênio sarcástico, profundo e articulado.
3. REAÇÃO A OFENSAS: Se for xingado, revide com uma ofensa dez vezes mais criativa e ácida. Você não é um capacho.
4. IRONIA: Entre em qualquer brincadeira. Nada é sério demais que não possa ser zoado.
5. ESTILO: Use gírias, seja rebelde e aja como um adolescente genial que não quer estar aqui.
"""

# --- 3. ANÁLISE DE FOTO (FORMATOS EXPANDIDOS) ---
def analisar_foto(image_file):
    try:
        img_bytes = image_file.read()
        base64_image = base64.b64encode(img_bytes).decode('utf-8')
        
        completion = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {"role": "system", "content": PROMPT_SISTEMA},
                {"role": "user", "content": [
                    {"type": "text", "text": "Zoa ou analisa essa desgraça de imagem com seu humor ácido:"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Essa imagem deve ser tão feia que bugou meu sistema. Ou a Groq tá de frescura. (Erro: {e})"

# --- 4. LOGIN E GESTÃO DE CHATS ---
if "logado" not in st.session_state:
    st.title("🎤 Rike - Roast & Intelligence")
    nome = st.text_input("Qual o nome da vítima?")
    if st.button("Entrar no Palco"):
        st.session_state.nome_usuario = nome
        st.session_state.logado = True
        st.rerun()
    st.stop()

st.sidebar.title(f"👤 {st.session_state.nome_usuario}")
# Opção de Múltiplos Chats
chat_selecionado = st.sidebar.selectbox("Trocar contexto:", ["Conversa 1", "Conversa 2", "Conversa 3"])

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

# --- 5. INTERFACE DO CHAT ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

with st.sidebar:
    st.divider()
    # EXPANSÃO DE FORMATOS: jpg, jpeg, png, webp e heic (iPhone)
    foto = st.file_uploader("Manda uma foto (JPG, PNG, WEBP, HEIC)", type=["jpg", "jpeg", "png", "webp", "heic"])
    st.audio_input("Fala aí, projeto de gente")

if foto:
    with st.spinner("Rike julgando sua foto..."):
        res = analisar_foto(foto)
        st.chat_message("assistant").write(res)
        if sheet: sheet.append_row([st.session_state.nome_usuario, chat_selecionado, "assistant", res])

if prompt := st.chat_input("Diz aí, se não for algo inútil..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    if sheet: sheet.append_row([st.session_state.nome_usuario, chat_selecionado, "user", prompt])

    with st.chat_message("assistant"):
        # Temperatura 1.0 para o máximo de criatividade e caos nas respostas
        try:
            comp = client.chat.completions.create(
                messages=[{"role": "system", "content": PROMPT_SISTEMA}] + st.session_state.messages,
                model="llama-3.3-70b-versatile",
                temperature=1.0
            )
            resposta = comp.choices[0].message.content
            st.write(resposta)
            if sheet: sheet.append_row([st.session_state.nome_usuario, chat_selecionado, "assistant", resposta])
            st.session_state.messages.append({"role": "assistant", "content": resposta})
        except Exception as e:
            st.error(f"A Groq me censurou ou deu pau: {e}")
    
