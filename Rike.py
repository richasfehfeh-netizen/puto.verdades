import streamlit as st
from groq import Groq

# --- CONFIGURAÇÃO ---
# Coloque sua chave da Groq aqui entre as aspas
CHAVE_GROQ = "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" 

try:
    client = Groq(api_key=CHAVE_GROQ)
except Exception as e:
    st.error(f"Erro ao configurar a chave: {e}")

NOME_IA = "Rike"

# Configuração visual do site
st.set_page_config(page_title=f"Assistente {NOME_IA}", page_icon="⚡")
st.title(f"⚡ {NOME_IA} - Inteligência Analítica")
st.caption("Powered by Groq | Llama 3.3 70B")

# Personalidade e Instruções de Sistema
instrucao_sistema = f"""
Seu nome é {NOME_IA}. Você é o assistente pessoal do Richard.
Estilo: Técnico, inteligente e direto. 
Entenda gírias, contextos complexos e não tenha dificuldade com palavras informais.
Responda de forma útil e com bom humor sutil.
"""

# Inicializa o histórico de mensagens
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe as mensagens anteriores na tela
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Campo de entrada de texto
if prompt := st.chat_input("Fale com o Rike..."):
    # Guarda a pergunta do Richard
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Resposta da IA
    with st.chat_message("assistant"):
        try:
            # Chamada para o modelo mais recente (Llama 3.3)
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": instrucao_sistema},
                    *st.session_state.messages
                ],
                model="llama-3.3-70b-versatile", # Modelo atualizado e estável
                temperature=0.7,
                max_tokens=2048
            )
            
            full_response = chat_completion.choices[0].message.content
            st.markdown(full_response)
            
            # Guarda a resposta no histórico
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            # Tratamento de erro para limites ou modelos
            if "decommissioned" in str(e):
                st.error("Rike: Richard, o modelo foi atualizado. Preciso de um ajuste rápido no código!")
            elif "429" in str(e):
                st.error("Rike: Calma, Richard! Estou processando muita coisa. Aguarde 10 segundos.")
            else:
                st.error(f"Erro técnico: {e}")
                
