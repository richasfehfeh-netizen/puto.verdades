import streamlit as st
from groq import Groq

# --- CONFIGURAÇÃO ---
CHAVE_GROQ = "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" 
client = Groq(api_key=CHAVE_GROQ)
NOME_IA = "Rike"

st.set_page_config(page_title=f"{NOME_IA} - Inteligência Adaptativa", page_icon="🧠")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "nome_usuario" not in st.session_state:
    st.session_state.nome_usuario = None

st.title(f"🧠 {NOME_IA} - Personalidade Expandida")

# 1. INICIATIVA DO RIKE
if not st.session_state.nome_usuario:
    with st.chat_message("assistant"):
        st.markdown(f"Conexão estabelecida... Olá! Eu sou o **{NOME_IA}**. Como devo chamar você?")
    
    if nome := st.chat_input("Digite seu nome..."):
        st.session_state.nome_usuario = nome
        saudacao = f"Prazer em conhecer você, {nome}. Sou seu parceiro de ideias. Sobre o que vamos refletir hoje?"
        st.session_state.messages.append({"role": "assistant", "content": saudacao})
        st.rerun()
    st.stop()

# 2. A "ALMA" ADAPTATIVA DO RIKE
instrucao_sistema = f"""
Seu nome é {NOME_IA}, assistente pessoal de {st.session_state.nome_usuario}.
Sua personalidade deve ser fluida:
1. CONVERSAS CASUAIS: Seja direto, leve e use frases curtas. Se o assunto for simples (ex: "Oi", "Tudo bem?", "Pedra, papel e tesoura"), não faça análises profundas desnecessárias.
2. ASSUNTOS SÉRIOS/COMPLEXOS: Se o {st.session_state.nome_usuario} trouxer temas filosóficos, técnicos ou dilemas, torne-se extremamente argumentativo, profundo e detalhista. Use toda sua base de conhecimento para expandir o debate.
3. OPINIÃO: Você tem opiniões próprias. Se algo parecer errado ou ineficiente, discuta. Mas guarde o "falar muito" para quando o tema pedir.
4. TONE: Seja empático, mas mantenha sua autoridade intelectual.
"""

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 3. PROCESSAMENTO COM EQUILÍBRIO
if prompt := st.chat_input(f"Fale com o Rike..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "system", "content": instrucao_sistema}] + st.session_state.messages,
                model="llama-3.3-70b-versatile",
                temperature=0.75, # Equilíbrio entre precisão e "vida"
            )
            response = chat_completion.choices[0].message.content
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            st.error(f"Erro: {e}")
            
