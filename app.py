import streamlit as st
import os
import json
import uuid
from datetime import datetime
import openai
import requests
import firebase_admin
from firebase_admin import credentials, db

# --- Configurações iniciais ---
st.set_page_config(page_title="SantChat", page_icon="🤖", layout="centered")

# --- Firebase Initialization ---
if not firebase_admin._apps:
    firebase_key = { k: (v.replace("\\n","\n") if k=="private_key" else v)
                     for k,v in st.secrets["FIREBASE_KEY"].items() }
    firebase_admin.initialize_app(credentials.Certificate(firebase_key),
                                  {"databaseURL": st.secrets["FIREBASE_KEY_DB_URL"]})

# --- API Key OpenRouter ---
OPENROUTER_KEY = st.secrets["OPENROUTER_KEY"]
openai.api_key = OPENROUTER_KEY
openai.base_url = "https://openrouter.ai/api/v1"

# --- Desenvolvedores autorizados ---
DEVS = ["thiago@santander.com.br", "T762981"]

# --- Funções Auxiliares ---
def obter_id_usuario():
    if "user_id" not in st.session_state:
        if st.session_state.get("use_microsoft"):
            # Simulação de login MSO
            email = "thiago@santander.com.br"
            st.session_state.user_id = email
        else:
            st.session_state.user_id = f"guest-{uuid.uuid4().hex[:6]}"
    return st.session_state.user_id

def carregar_memoria():
    try:
        ref = db.reference("memoria_global")
        memoria = ref.get()
        return memoria if isinstance(memoria, list) else []
    except:
        return []

def salvar_memoria(mem):
    db.reference("memoria_global").set(mem)

def gerar_resposta(memoria, prompt):
    msgs = [{"role":"system","content":"Sua IA inteligente."}]
    msgs += [{"role":"system","content": "\n".join(memoria)}] if memoria else []
    msgs.append({"role":"user","content": prompt})
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization":f"Bearer {OPENROUTER_KEY}",
                 "Content-Type":"application/json"},
        json={"model":"nousresearch/deephermes-3-mistral-24b-preview:free",
              "messages":msgs, "max_tokens":500, "temperature":0.7})
    if resp.status_code != 200:
        return f"Erro: {resp.status_code}"
    return resp.json()["choices"][0]["message"]["content"].strip()

def salvar_feedback(user_id, pergunta, resposta, comentario):
    ref = db.reference(f"logs/feedbacks/{user_id}")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ref.update({ts: json.dumps({
        "pergunta": pergunta,
        "resposta": resposta,
        "feedback": comentario
    })})


def desbloquear_memoria_e_feed(user_id):
    return user_id in DEVS

# --- Interface ---
def main():
    st.markdown("""<style>
    body{background:#111;color:#eee;}
    .chat-header{position:sticky;top:0;padding:10px;text-align:center;background:#111;z-index:999;}
    .chat-header h1{color:#ec0000;}
    .disclaimer{position:fixed;bottom:0;width:100%;text-align:center;color:#888;padding:8px 0;background:#111;}
    section.main > div:has(div[data-testid="stChatInput"]){padding-bottom:80px!important;}
    .msg-user{background:#333;color:#fff;padding:8px;border-radius:8px 0px 8px 8px;float:right;clear:both;max-width:80%;}
    .msg-assistant{background:#222;color:#eee;padding:8px;border-radius:0px 8px 8px 8px;float:left;clear:both;max-width:80%;}
    </style>""", unsafe_allow_html=True)

    st.markdown("<div class='chat-header'><h1>🤖 SantChat</h1></div>", unsafe_allow_html=True)

    # Sidebar
    user_id = obter_id_usuario()
    is_dev = desbloquear_memoria_e_feed(user_id)

    menu = ["Chat"]
    if is_dev:
        menu += ["Memória IA", "Feedbacks", "Configurações"]
    choice = st.sidebar.radio("Menu", menu)

    if choice == "Chat":
        if "memoria" not in st.session_state:
            st.session_state.memoria = carregar_memoria()
            st.session_state.historico = []
        for msg in st.session_state.historico:
            css = "msg-user" if msg["origem"]=="user" else "msg-assistant"
            st.markdown(f"<div class='{css}'>{msg['texto']}</div>", unsafe_allow_html=True)
        entrada = st.chat_input("Digite sua mensagem")
        if entrada:
            st.session_state.historico.append({"origem":"user","texto":entrada})
            respuesta = gerar_resposta(st.session_state.memoria, entrada)
            st.session_state.historico.append({"origem":"assistant","texto":respuesta})

            # Botões
            st.write(f"{respuesta}")
            co, cu, fe = st.columns([0.1,0.1,0.2])
            with co:
                if st.button("📋 Copiar"):
                    st.write(respuesta)
            with cu:
                if st.button("👍"):
                    pass
            with fe:
                txt = st.text_input("Feedback?")
                if st.button("Enviar"):
                    salvar_feedback(user_id, entrada, respuesta, txt)
                    st.success("Obrigado!")

    elif choice == "Memória IA":
        st.header("Memória Global")
        mem = carregar_memoria()
        st.write(mem)
    elif choice == "Feedbacks":
        st.header("Feedbacks Recebidos")
        for k, v in db.reference(f"logs/feedbacks/{user_id}").get(_,{}).items():
            st.write(json.loads(v))
    elif choice == "Configurações":
        st.header("Configurações")
        if st.button("Logout"):
            st.session_state.clear()
            st.experimental_rerun()

    st.markdown("<div class='disclaimer'>⚠️ O SantChat pode cometer erros.</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
