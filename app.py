import streamlit as st
import os, json, uuid
from datetime import datetime, timedelta
import openai, requests
import firebase_admin
from firebase_admin import credentials, db

st.set_page_config(page_title="SantChat", page_icon="🤖", layout="centered")

# Firebase
if not firebase_admin._apps:
    firebase_key = {k: (v.replace("\n", "\n") if k == "private_key" else v)
                    for k, v in st.secrets["FIREBASE_KEY"].items()}
    firebase_admin.initialize_app(credentials.Certificate(firebase_key), {
        "databaseURL": st.secrets["FIREBASE_KEY_DB_URL"]
    })

OPENROUTER_KEY = st.secrets["OPENROUTER_KEY"]
openai.api_key = OPENROUTER_KEY
openai.base_url = "https://openrouter.ai/api/v1"
DEVS = ["thiago@santander.com.br", "T762981"]

def obter_id_usuario():
    if "user_id" not in st.session_state:
        st.session_state.user_id = f"guest-{uuid.uuid4().hex[:6]}"
    return st.session_state.user_id

def carregar_memoria():
    try:
        return db.reference("memoria_global").get() or []
    except:
        return []

def salvar_feedback(uid, pergunta, resposta, comentario):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    db.reference(f"logs/feedbacks/{uid}").update({
        ts: json.dumps({"pergunta": pergunta, "resposta": resposta, "feedback": comentario})
    })

def salvar_historico(uid, historico):
    if not historico:
        return
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    titulo = historico[0]["texto"][:50]
    db.reference(f"logs/usuarios/{uid}/historico/{ts}").set({
        "titulo": titulo, "mensagens": historico, "timestamp": ts
    })

def gerar_resposta(memoria, prompt):
    msgs = [{"role": "system", "content": "Você é o SantChat, IA do Santander."}]
    if memoria:
        msgs.append({"role": "system", "content": "\n".join(memoria)})
    msgs.append({"role": "user", "content": prompt})
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"},
            json={"model": "nousresearch/deephermes-3-mistral-24b-preview:free", "messages": msgs, "max_tokens": 500})
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Erro: {e}"

# Estilo
st.markdown("""<style>
body { background:#111; color:#eee; }
.chat-header { position:fixed; top:0; width:100%; padding:10px; text-align:center; background:#111; z-index:999; }
.chat-header h1 { color:#ec0000; }
.disclaimer { position:fixed; bottom:0; width:100%; text-align:center; color:#888; padding:10px; background:#111; }
section.main > div:has(div[data-testid="stChatInput"]) { padding-bottom:100px!important; padding-top:90px!important; }
.msg-user { background:#333; padding:10px; border-radius:10px; margin:8px 0 8px auto; max-width:80%; }
.msg-assistant { background:#222; padding:10px; border-radius:10px; margin:8px auto 8px 0; max-width:80%; }
button[kind="secondary"] {
  background-color:#222!important; color:#ccc!important; border-radius:6px!important;
  padding:4px 10px!important; font-size:20px!important; border:1px solid #444!important;
}
button[kind="secondary"]:hover { background-color:#333!important; color:#fff!important; }
</style>""", unsafe_allow_html=True)

st.markdown("<div class='chat-header'><h1>🤖 SantChat</h1><p>IA interna para colaboradores do Santander</p></div>", unsafe_allow_html=True)

uid = obter_id_usuario()
if "memoria" not in st.session_state:
    st.session_state.memoria = carregar_memoria()
if "historico" not in st.session_state:
    st.session_state.historico = []
if "ultima_interacao" not in st.session_state:
    st.session_state.ultima_interacao = datetime.now()

# Timeout: salva e limpa se passou 2h
now = datetime.now()
if now - st.session_state.ultima_interacao > timedelta(hours=2):
    salvar_historico(uid, st.session_state.historico)
    st.session_state.historico = []
    st.session_state.ultima_interacao = now

# Mostrar histórico
for i, chat in enumerate(st.session_state.historico):
    tipo = "msg-user" if chat["origem"] == "user" else "msg-assistant"
    st.markdown(f"<div class='{tipo}'>{chat['texto']}</div>", unsafe_allow_html=True)
    if chat["origem"] == "assistant":
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: st.button("📋", key=f"copy_{i}")
        with c2: st.button("🔈", key=f"voz_{i}")
        with c3: st.button("👍", key=f"like_{i}")
        with c4: st.button("👎", key=f"dislike_{i}")
        with c5:
            if st.button("💬", key=f"fb_btn_{i}"):
                st.session_state[f"fb_{i}"] = True
        if st.session_state.get(f"fb_{i}"):
            fb = st.text_input("Seu feedback:", key=f"fb_text_{i}")
            if st.button("Enviar feedback", key=f"send_{i}"):
                salvar_feedback(uid, st.session_state.historico[i-1]["texto"], chat["texto"], fb)
                st.success("✅ Enviado!")
                st.session_state[f"fb_{i}"] = False

entrada = st.chat_input("Digite sua mensagem")
if entrada:
    st.session_state.ultima_interacao = datetime.now()
    st.session_state.historico.append({"origem": "user", "texto": entrada})
    resposta = gerar_resposta(st.session_state.memoria, entrada)
    st.session_state.historico.append({"origem": "assistant", "texto": resposta})

st.markdown("<div class='disclaimer'>⚠️ O SantChat pode cometer erros. Verifique informações importantes antes de tomar decisões.</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
