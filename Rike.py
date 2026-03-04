import streamlit as st
import google.generativeai as genai

# Configuração
CHAVE_API = "AIzaSyBqZ7u990v8ngaYtXihrro3DvLCOgeqHmc"
genai.configure(api_key=CHAVE_API)

# Título do Site
st.set_page_config(page_title="Rike Assistente", page_icon="🤖")
st.title("🌐 Rike - Inteligência Analítica")

# Função para garantir que o modelo certo seja carregado sem erro 404
@st.cache_resource
def carregar_modelo():
    # Busca o melhor modelo disponível na sua chave
    modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    nome_modelo = modelos[0]
    
    # Instrução para ele não ter dificuldade com palavras e ser preciso
    instrucao = (
        "Seu nome é Rike. Você é o assistente pessoal do Richard. "
        "Você deve ser extremamente inteligente, entender gírias, contextos técnicos e "
        "analisar profundamente cada palavra que o Richard disser. Seja direto e útil."
    )
    
    return genai.GenerativeModel(model_name=nome_modelo, system_instruction=instrucao)

model = carregar_modelo()

# Histórico de Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrada do Richard
if prompt := st.chat_input("Fale com o Rike..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # Inicia o chat e envia a mensagem
            chat = model.start_chat(history=[])
            response = chat.send_message(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            # Se estourar o limite de novo, ele avisa com educação
            if "429" in str(e) or "ResourceExhausted" in str(e):
                st.error("Rike: Richard, recebi muitas ordens em pouco tempo! Aguarde 30 segundos e tente novamente.")
            else:
                st.error(f"Erro: {e}")
                
