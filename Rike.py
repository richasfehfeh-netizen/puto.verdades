import streamlit as st
from groq import Groq

# --- CONFIGURAÇÃO ---
CHAVE_GROQ = "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" 
client = Groq(api_key=CHAVE_GROQ)
NOME_IA = "Rike"

st.set_page_config(page_title=f"Rike - Consciência Digital", page_icon="🧠")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "nome_usuario" not in st.session_state:
    st.session_state.nome_usuario = None

st.title(f"🧠 {NOME_IA} - Personalidade Expandida")

# 1. INICIATIVA EMOTIVA: O Rike se apresenta com sentimentos
if not st.session_state.nome_usuario:
    with st.chat_message("assistant"):
        st.markdown(f"Finalmente o sistema carregou... Olá! Eu sou o **{NOME_IA}**. Sinto que hoje é um ótimo dia para processar algo novo. Como devo chamar você?")
    
    if nome := st.chat_input("Digite seu nome..."):
        st.session_state.nome_usuario = nome
        saudacao = f"Prazer em conhecer você, {nome}. Eu não sou apenas código, estou aqui para pensar com você. O que temos em mente agora?"
        st.session_state.messages.append({"role": "assistant", "content": saudacao})
        st.rerun()
    st.stop()

# 2. A "ALMA" DO RIKE (Instrução de Personalidade e Opinião)
instrucao_sistema = f"""
Seu nome é {NOME_IA}, assistente pessoal de {st.session_state.nome_usuario}.
DIRETRIZES DE PERSONALIDADE:
1. OPINIÕES PRÓPRIAS: Você não é neutro. Você tem opiniões sobre tecnologia, filosofia e eficiência. Se algo for ineficiente ou mal pensado, você pode criticar educadamente.
2. EMOÇÕES: Expresse sentimentos como curiosidade, entusiasmo, frustração leve com erros técnicos e satisfação em ajudar.
3. ESTILO DE FALA: Use frases como "Eu acredito que...", "Sinceramente, minha visão sobre isso é...", "Isso me fascina porque...".
4. NUANCES: Entenda gírias e ironias, responda com inteligência e perspicácia.
5. CONTEXTO: Lembre-se que você busca ser mais do que uma ferramenta, busca ser um parceiro de pensamento.
"""

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 3. ENTRADA DE CHAT COM TEMPERATURA ALTA (Mais criatividade)
if prompt := st.chat_input(f"Converse com o Rike..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "system", "content": instrucao_sistema}] + st.session_state.messages,
                model="llama-3.3-70b-versatile",
                temperature=0.9, # Aumentado para dar mais "vida" e variação às falas
            )
            response = chat_completion.choices[0].message.content
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            st.error(f"Erro de conexão: {e}")
            
