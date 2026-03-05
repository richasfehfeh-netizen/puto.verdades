import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import pytz
import smtplib
import requests
import re
from email.mime.text import MIMEText
from apscheduler.schedulers.background import BackgroundScheduler

# --- 1. CONFIGURAÇÕES TÉCNICAS (API NO CÓDIGO) ---
# Resolve o erro de IA Offline (Print 8511)
CHAVE_GROQ = "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"
# Substitua pelo ID real da sua planilha
ID_PLANILHA = "1WTM3bb9-l8_C4odgvFPLaNUJDnvvrHGCqyQwNCvEKNM" 

fuso_br = pytz.timezone('America/Sao_Paulo')
st.set_page_config(page_title="Calyo Assist", page_icon="🧠")

# --- 2. INICIALIZAÇÃO DOS MOTORES ---
@st.cache_resource
def iniciar_motores():
    client = Groq(api_key=CHAVE_GROQ)
    sheet = None
    try:
        if "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            )
            sheet = gspread.authorize(creds).open_by_key(ID_PLANILHA).get_worksheet(0)
    except: pass

    sch = BackgroundScheduler(timezone=fuso_br)
    if not sch.running: sch.start()
    return client, sheet, sch

client_ia, sheet_rag, scheduler = iniciar_motores()

# --- 3. FUNÇÕES DE EXECUÇÃO ATUALIZADAS ---

def enviar_push_real(msg):
    """Envia notificação via ntfy com PRIORIDADE ALTA"""
    try:
        requests.post(
            "https://ntfy.sh/calyo_push_notificator", 
            data=msg.encode('utf-8'),
            headers={
                "Title": "⚠️ Calyo Assist",
                "Priority": "high",  # Prioridade alta solicitada
                "Tags": "brain,loud_speaker"
            }
        )
    except: pass

def enviar_email_real(assunto, corpo):
    """Método 587 + TLS para Gmail (Resolve Print 8509)"""
    try:
        user = st.secrets.get("EMAIL_USER")
        pw = st.secrets.get("EMAIL_PASS") # Senha de 16 dígitos
        if not user or not pw: return False
        
        msg = MIMEText(corpo)
        msg['Subject'] = assunto
        msg['From'] = user
        msg['To'] = user 
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(user, pw)
        server.send_message(msg)
        server.quit()
        return True
    except: return False

# --- 4. INTERFACE E LÓGICA DE CHAT ---
st.title("🧠 Calyo Assist")
# Mostra a hora certa para você conferir (Resolve Print 8507)
agora_agora = datetime.now(fuso_br).strftime('%H:%M')
st.caption(f"Horário de Brasília: {agora_agora}")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Fale com o Calyo..."):
    agora = datetime.now(fuso_br)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    status_extra = ""

    # Lógica de E-mail (Resolve Print 8521)
    if "email" in prompt.lower() or "e-mail" in prompt.lower():
        if enviar_email_real("Solicitação Richard", prompt):
            status_extra = " [SISTEMA: E-mail enviado com sucesso]"
            st.success("📧 E-mail enviado!")

    # Lógica de Agendamento (Resolve Print 8507)
    if any(x in prompt.lower() for x in ["agende", "avise", "notifique"]):
        num = re.findall(r'\d+', prompt)
        minutos = int(num[0]) if num else 5
        data_f = agora + timedelta(minutes=minutos)
        scheduler.add_job(enviar_push_real, 'date', run_date=data_f, args=[f"Lembrete: {prompt}"])
        status_extra += f" [SISTEMA: Notificação ALTA agendada para {data_f.strftime('%H:%M')}]"
        st.info(f"⏳ Agendado para {data_f.strftime('%H:%M')}")

    # RESPOSTA DA IA (LLAMA 3.3)
    with st.chat_message("assistant"):
        contexto_rag = ""
        if sheet_rag:
            try:
                # Resolve SyntaxError do Print 8510
                ultimos = sheet_rag.get_all_records()[-3:]
                contexto_rag = "Histórico: " + " | ".join([str(u['content']) for u in ultimos])
            except: pass

        # PROMPT DE SISTEMA: Aqui evitamos as desculpas do Calyo (Prints 8513 e 8521)
        sys_msg = (
            f"Você é o Calyo Assist. Seu dono é o Richard. "
            f"HORA ATUAL: {agora.strftime('%H:%M')}. "
            f"Você TEM capacidade de enviar e-mails e agendar notificações. "
            f"STATUS ATUAL: {status_extra}. {contexto_rag}. "
            "Se o status diz que algo foi enviado ou agendado, confirme isso ao usuário."
        )
        
        try:
            resp = client_ia.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages
            )
            txt = resp.choices[0].message.content
            st.markdown(txt)
            st.session_state.messages.append({"role": "assistant", "content": txt})
            
            if sheet_rag:
                sheet_rag.append_row([agora.isoformat(), "user", prompt, txt])
        except Exception as e:
            st.error(f"Erro IA: {e}")
            
