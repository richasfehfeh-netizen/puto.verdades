import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
import smtplib
import requests
import gspread
import re
from email.mime.text import MIMEText
from apscheduler.schedulers.background import BackgroundScheduler
from google.oauth2.service_account import Credentials
from groq import Groq

# --- 1. CONFIGURAÇÃO DE TEMPO (RESOLVE PRINT 8507) ---
fuso_br = pytz.timezone('America/Sao_Paulo')

# --- 2. CONFIGURAÇÃO DA IA E MOTORES ---
# Tenta carregar a chave da Groq (Resolve erro do print 8508)
api_key_groq = st.secrets.get("GROQ_API_KEY")
client = Groq(api_key=api_key_groq) if api_key_groq else None

@st.cache_resource
def iniciar_motores():
    # Agendador com fuso horário correto
    sch = BackgroundScheduler(timezone=fuso_br)
    if not sch.running: sch.start()
    
    # Memória (Planilha)
    sheet_obj = None
    try:
        if "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            )
            # COLOQUE O ID DA SUA PLANILHA AQUI
            sheet_obj = gspread.authorize(creds).open_by_key("1WTM3bb9-l8_C4odgvFPLaNUJDnvvrHGCqyQwNCvEKNM").get_worksheet(0)
    except: pass
    return sch, sheet_obj

scheduler, sheet = iniciar_motores()

# --- 3. FUNÇÕES DE COMUNICAÇÃO ---
def enviar_push_real(msg):
    # Usa o tópico que vimos no print 8507
    requests.post("https://ntfy.sh/calyo_push_notificator", data=msg.encode('utf-8'))

def enviar_email_real(assunto, corpo):
    try:
        email_user = st.secrets.get("EMAIL_USER")
        email_pass = st.secrets.get("EMAIL_PASS")
        if not email_user or not email_pass: return False
        
        msg = MIMEText(corpo)
        msg['Subject'] = assunto
        msg['From'] = email_user
        msg['To'] = email_user
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(email_user, email_pass)
            server.send_message(msg)
        return True
    except: return False

# --- 4. RELATÓRIO DIÁRIO AUTOMÁTICO (ÀS 23:00) ---
def job_relatorio():
    if sheet:
        dados = sheet.get_all_records()
        resumo = "\n".join([f"- {r.get('role', 'IA')}: {r.get('content', '')}" for r in dados[-15:]])
        enviar_email_real("📊 Relatório Diário Calyo Assist", f"Resumo do dia:\n\n{resumo}")

if not scheduler.get_job('relatorio_diario'):
    scheduler.add_job(job_relatorio, 'cron', hour=23, minute=0, id='relatorio_diario')

# --- 5. INTERFACE DO CHAT ---
st.title("🧠 Calyo Assist")
st.caption(f"Horário de Brasília: {datetime.now(fuso_br).strftime('%H:%M')}")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. PROCESSAMENTO DE COMANDOS (RESOLVE PRINTS 8501, 8505) ---
if prompt := st.chat_input("Fale com o Calyo..."):
    agora = datetime.now(fuso_br)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    status_sistema = ""

    # Agendamento Real (Push)
    if any(x in prompt.lower() for x in ["agende", "avise", "notifique"]):
        num = re.findall(r'\d+', prompt)
        min = int(num[0]) if num else 5
        # Se for horário fixo (ex: 01:20), calcula a diferença
        hora_alerta = agora + timedelta(minutes=min)
        scheduler.add_job(enviar_push_real, 'date', run_date=hora_alerta, args=[f"Lembrete: {prompt}"])
        status_sistema += f" [SISTEMA: Notificação agendada para {hora_alerta.strftime('%H:%M')}]"
        st.success(f"✅ Agendado para {hora_alerta.strftime('%H:%M')}")

    # E-mail Real
    if "email" in prompt.lower() or "e-mail" in prompt.lower():
        if enviar_email_real("Aviso Calyo Assist", prompt):
            status_sistema += " [SISTEMA: E-mail enviado]"
            st.success("📧 E-mail enviado!")

    # RESPOSTA DA IA
    if client:
        with st.chat_message("assistant"):
            instrucao = f"Você é o Calyo Assist. Horário: {agora.strftime('%H:%M')}. Status: {status_sistema}"
            try:
                resp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": instrucao}] + st.session_state.messages
                )
                texto = resp.choices[0].message.content
                st.markdown(texto)
                st.session_state.messages.append({"role": "assistant", "content": texto})
                if sheet: sheet.append_row([agora.isoformat(), "Richard", prompt, texto])
            except Exception as e:
                st.error(f"Erro IA: {e}")
    else:
        st.warning("IA Offline: Configure 'GROQ_API_KEY' nos Secrets.")
