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

# --- 1. CONFIGURAÇÕES DE TEMPO E INTERFACE ---
fuso_br = pytz.timezone('America/Sao_Paulo')
st.set_page_config(page_title="Calyo Assist", page_icon="🧠")

# --- 2. MOTORES: IA E PLANILHA (O SISTEMA RAG) ---
@st.cache_resource
def iniciar_sistema():
    # A. Conectar IA (Groq) -
    client = None
    if "GROQ_API_KEY" in st.secrets:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    
    # B. Conectar Planilha (Google Sheets) -
    sheet = None
    try:
        if "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            )
            # COLOQUE AQUI A SUA ID DA PLANILHA (aquela longa da URL)
            ID_PLANILHA = "1WTM3bb9-l8_C4odgvFPLaNUJDnvvrHGCqyQwNCvEKNM" 
            sheet = gspread.authorize(creds).open_by_key(ID_PLANILHA).get_worksheet(0)
    except Exception as e:
        st.error(f"Erro na Planilha: {e}")

    # C. Agendador (Scheduler)
    sch = BackgroundScheduler(timezone=fuso_br)
    if not sch.running: sch.start()
    
    return client, sheet, sch

client, sheet, scheduler = iniciar_sistema()

# --- 3. FUNÇÕES DE EXECUÇÃO ---
def enviar_push_real(msg):
    requests.post("https://ntfy.sh/calyo_push_notificator", data=msg.encode('utf-8'))

def enviar_email_real(assunto, corpo):
    try:
        user = st.secrets["EMAIL_USER"]
        pw = st.secrets["EMAIL_PASS"]
        msg = MIMEText(corpo)
        msg['Subject'] = assunto
        msg['From'] = user
        msg['To'] = user
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(user, pw)
            s.send_message(msg)
        return True
    except: return False

# --- 4. LÓGICA DE MEMÓRIA (RAG) E RELATÓRIO ---
def job_relatorio_diario():
    if sheet:
        # O RAG lê as últimas interações para o e-mail
        dados = sheet.get_all_records()
        resumo = "\n".join([f"- {r['role']}: {r['content']}" for r in dados[-10:]])
        enviar_email_real("📊 Relatório Diário Calyo", f"Richard, aqui está a memória de hoje:\n\n{resumo}")

if not scheduler.get_job('relatorio_diario'):
    scheduler.add_job(job_relatorio_diario, 'cron', hour=23, minute=0, id='relatorio_diario')

# --- 5. INTERFACE DO CHAT ---
st.title("🧠 Calyo Assist")
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Fale com o Calyo..."):
    agora = datetime.now(fuso_br)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    status_ferramentas = ""

    # Ações em tempo real
    if "email" in prompt.lower():
        if enviar_email_real("Pedido Richard", prompt): 
            status_ferramentas += " [E-mail enviado]"
            st.success("📧 Enviado!")

    if any(x in prompt.lower() for x in ["agende", "avise", "notifique"]):
        num = re.findall(r'\d+', prompt)
        minutos = int(num[0]) if num else 5
        data_f = agora + timedelta(minutes=minutos)
        scheduler.add_job(enviar_push_real, 'date', run_date=data_f, args=[f"Alerta: {prompt}"])
        status_ferramentas += f" [Agendado para {data_f.strftime('%H:%M')}]"
        st.success(f"⏳ Agendado: {data_f.strftime('%H:%M')}")

    # RESPOSTA COM IA + SALVAMENTO NA PLANILHA (MEMÓRIA)
    with st.chat_message("assistant"):
        if client:
            # Buscando contexto na planilha (RAG Simples)
            memoria_contexto = ""
            if sheet:
                ultimos = sheet.get_all_records()[-3:]
                memoria_contexto = "Memória recente: " + "
            
