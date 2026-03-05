import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
import smtplib
import requests
import gspread
from google.oauth2.service_account import Credentials
from email.mime.text import MIMEText
from apscheduler.schedulers.background import BackgroundScheduler
from groq import Groq
import re

# --- 1. CONFIGURAÇÕES INICIAIS E FUSO ---
fuso_br = pytz.timezone('America/Sao_Paulo')
st.set_page_config(page_title="Calyo Assist", page_icon="🧠")

# --- 2. CONEXÃO COM A GROQ E PLANILHA (RESOLVE PRINT 8494) ---
client = Groq(api_key=st.secrets.get("GROQ_API_KEY"))

@st.cache_resource
def iniciar_motores():
    # Agendador
    sch = BackgroundScheduler(timezone=fuso_br)
    if not sch.running: sch.start()
    
    # Google Sheets (Memória RAG)
    sheet_obj = None
    try:
        if "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            )
            # Substitua pela sua ID Real da Planilha
            sheet_obj = gspread.authorize(creds).open_by_key("1WTM3bb9-l8_C4odgvFPLaNUJDnvvrHGCqyQwNCvEKNM").get_worksheet(0)
    except: pass
    return sch, sheet_obj

scheduler, sheet = iniciar_motores()

# --- 3. FUNÇÕES DE COMUNICAÇÃO REAIS ---
def enviar_push_real(msg):
    requests.post("https://ntfy.sh/calyo_push_notificator", data=msg.encode('utf-8'))

def enviar_email_real(assunto, corpo):
    try:
        msg = MIMEText(corpo)
        msg['Subject'] = assunto
        msg['From'] = st.secrets["EMAIL_USER"]
        msg['To'] = st.secrets["EMAIL_USER"]
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(st.secrets["EMAIL_USER"], st.secrets["EMAIL_PASS"])
            server.send_message(msg)
        return True
    except: return False

# --- 4. RELATÓRIO DIÁRIO (O QUE FALTAVA) ---
def job_relatorio():
    if sheet:
        historico = sheet.get_all_records()
        resumo = "\n".join([f"- {r['role']}: {r['content']}" for r in historico[-10:]])
        enviar_email_real("📊 Relatório Calyo Assist", f"Resumo das últimas interações:\n\n{resumo}")

if not scheduler.get_job('relatorio_diario'):
    scheduler.add_job(job_relatorio, 'cron', hour=23, minute=0, id='relatorio_diario')

# --- 5. INTERFACE E LÓGICA DE CHAT ---
st.title("🧠 Calyo Assist")
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibir histórico
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Fale com o Calyo..."):
    agora = datetime.now(fuso_br)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Lógica de Ações Reais (Push/Email/Agenda)
    status_acao = ""
    if any(x in prompt.lower() for x in ["agende", "avise", "notifique"]):
        num = re.findall(r'\d+', prompt)
        minutos = int(num[0]) if num else 5
        hora_f = agora + timedelta(minutes=minutos)
        scheduler.add_job(enviar_push_real, 'date', run_date=hora_f, args=[f"Lembrete: {prompt}"])
        status_acao = f"(SISTEMA: Notificação agendada para {hora_f.strftime('%H:%M')})"
        st.success(f"✅ Agendado para {hora_f.strftime('%H:%M')}")

    if "email" in prompt.lower():
        if enviar_email_real("Solicitação Richard", prompt):
            status_acao += " (SISTEMA: E-mail enviado)"
            st.success("📧 E-mail enviado!")

    # RESPOSTA DA IA (LLAMA 3.3)
    with st.chat_message("assistant"):
        contexto = f"Seu nome é Calyo Assist. Você é o assistente do Richard. Horário atual: {agora.strftime('%H:%M')}. Status: {status_acao}"
        try:
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": contexto}] + st.session_state.messages
            )
            texto_ia = resp.choices[0].message.content
            st.markdown(texto_ia)
            st.session_state.messages.append({"role": "assistant", "content": texto_ia})
            # Salva na planilha (Memória Permanente)
            if sheet: sheet.append_row([agora.isoformat(), "Richard", prompt, texto_ia])
        except Exception as e:
            st.error(f"Erro na Groq: {e}")
