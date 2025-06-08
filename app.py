import streamlit as st
import os
import json
import uuid
from datetime import datetime, timedelta  
import openai
import requests
import firebase_admin
from firebase_admin import credentials, db

# --- Configurações iniciais ---
st.set_page_config(page_title="SantChat", page_icon="🤖", layout="centered")

# --- Firebase Initialization ---
if not firebase_admin._apps:
    firebase_key = {k: (v.replace("\n", "\n") if k == "private_key" else v)
                    for k, v in st.secrets["FIREBASE_KEY"].items()}
    firebase_admin.initialize_app(credentials.Certificate(firebase_key),
                                  {"databaseURL": st.secrets["FIREBASE_KEY_DB_URL"]})

OPENROUTER_KEY = st.secrets["OPENROUTER_KEY"]
openai.api_key = OPENROUTER_KEY
openai.base_url = "https://openrouter.ai/api/v1"

# --- Funções Auxiliares ---
def carregar_memoria():
    try:
        ref = db.reference("memoria_global")
        memoria = ref.get()
        return memoria if isinstance(memoria, list) else []
    except:
        return []

def salvar_feedback(user_id, pergunta, resposta, comentario):
    ref = db.reference(f"logs/feedbacks/{user_id}")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ref.update({ts: json.dumps({
        "pergunta": pergunta,
        "resposta": resposta,
        "feedback": comentario
    })})

def salvar_historico(user_id, historico):
    if not historico:
        return
    primeira_msg = historico[0]["texto"][:50]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ref = db.reference(f"logs/usuarios/{user_id}/historico/{ts}")
    ref.set({
        "titulo": primeira_msg,
        "mensagens": historico,
        "timestamp": ts
    })

def gerar_resposta(memoria, prompt):
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    system_prompt = f"""
    Hoje é {agora}. Você é o SantChat, IA oficial do Santander.
    Responda com clareza, sem inventar informações sobre datas.
    """
    msgs = [{"role": "system", "content": system_prompt.strip()}]
    if memoria:
        msgs.append({"role": "system", "content": "\n".join(memoria)})
    msgs.append({"role": "user", "content": prompt})

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek/deepseek-r1-0528:free",
                "messages": msgs,
                "max_tokens": 500,
                "temperature": 0.7
            },
            timeout=15
        )

        if resp.status_code != 200:
            return f"Erro na API OpenRouter: {resp.status_code} - {resp.text}"

        data = resp.json()
        if "choices" in data and data["choices"]:
            return data["choices"][0]["message"]["content"].strip()
        else:
            return "⚠️ A resposta da IA veio vazia ou incompleta."

    except Exception as e:
        return f"⚠️ Erro ao gerar resposta: {str(e)}"

def main():
 # 🎨 Estilo visual (tema escuro + layout fixo)
    st.markdown("""<style>
    body { background:#111; color:#eee; }
    .chat-header {
    position: sticky;  /* em vez de fixed */
    top: 0;
    background: #111;
    z-index: 1000;
    }

    .chat-header h1 { color:#ec0000; }
    .disclaimer { position:fixed; bottom:0; width:100%; text-align:center; color:#888; padding:10px; background:#111; }
    section.main > div:has(div[data-testid="stChatInput"]) {
        padding-bottom:100px!important; padding-top:90px!important;
    }
    .msg-user {
        background:#333; color:#fff; padding:10px;
        border-radius:10px; margin:8px 0 8px auto; max-width:80%;
    }
    .msg-assistant {
        background:#222; color:#eee; padding:10px;
        border-radius:10px; margin:8px auto 8px 0; max-width:80%;
    }
    /* Botões mais compactos */
    button[kind="secondary"] {
        padding: 0.2rem 0.5rem !important;
        margin: 0.1rem !important;
    }
    /* Espaçamento entre colunas */
    .stColumns > div {
        gap: 0.5rem;
    }
    button[kind="secondary"]:hover {
        background-color:#333!important; color:#fff!important;
    }
    </style>""", unsafe_allow_html=True)

    # 🧢 Cabeçalho fixo
    st.markdown("<div class='chat-header'><h1>🤖 SantChat</h1><p>IA interna para colaboradores do Santander</p></div>", unsafe_allow_html=True)

    # 🧑 Identificação do usuário
    user_id = obter_id_usuario()
    is_dev = desbloquear_memoria_e_feed(user_id)

    # 🧠 Inicializa estados
    if "memoria" not in st.session_state:
        st.session_state.memoria = carregar_memoria()
    if "historico" not in st.session_state:
        st.session_state.historico = []
    if "ultima_interacao" not in st.session_state:
        st.session_state.ultima_interacao = datetime.now()

    # ⏱ Timeout de inatividade (2h)
    if datetime.now() - st.session_state.ultima_interacao > timedelta(hours=2):
        if st.session_state.historico:
            salvar_historico(user_id, st.session_state.historico)
            st.session_state.historico = []
        st.session_state.ultima_interacao = datetime.now()
        print("Salvando histórico por timeout")
        salvar_historico(user_id, st.session_state.historico)

    # 📂 Menu lateral (com base no tipo de usuário)
    menu = ["Chat"]
    if is_dev:
        menu += ["Memória IA", "Feedbacks", "Configurações"]
    choice = st.sidebar.radio("Menu", menu)

    if choice == "Chat":
        # 🧾 Mostrar histórico de mensagens
        for i, msg in enumerate(st.session_state.historico):
            tipo = "msg-user" if msg["origem"] == "user" else "msg-assistant"
            st.markdown(f"<div class='{tipo}'>{msg['texto']}</div>", unsafe_allow_html=True)

            # 🎯 Botões para a resposta da IA
            if msg["origem"] == "assistant":
                col1, col2, col3 = st.columns([1, 1, 1])

                with col1:
                    if st.button("👍", key=f"like_{i}", help="Gostei"):
                        pergunta = st.session_state.historico[i-1]["texto"] if i > 0 else ""
                        salvar_feedback(user_id, pergunta, msg["texto"], "👍 Gostei")
                        st.success("✅ Avaliação positiva enviada!")

                with col2:
                    if st.button("👎", key=f"dislike_{i}", help="Não gostei"):
                        pergunta = st.session_state.historico[i-1]["texto"] if i > 0 else ""
                        salvar_feedback(user_id, pergunta, msg["texto"], "👎 Não gostei")
                        st.warning("⚠️ Avaliação negativa registrada.")

                with col3:
                    if st.button("💬", key=f"fb_btn_{i}", help="Enviar feedback"):
                        st.session_state[f"fb_{i}"] = True

                # 💬 Campo de feedback (expande ao clicar)
                if st.session_state.get(f"fb_{i}"):
                    feedback = st.text_input("Seu feedback:", key=f"fb_text_{i}")
                    if st.button("Enviar feedback", key=f"send_fb_{i}"):
                        pergunta = st.session_state.historico[i-1]["texto"] if i > 0 else ""
                        salvar_feedback(user_id, pergunta, msg["texto"], feedback)
                        st.success("✅ Feedback enviado com sucesso!")
                        st.session_state[f"fb_{i}"] = False

    # --- Novo controle de login ---
    if "user_type" not in st.session_state:
        st.session_state["user_type"] = "guest"
        st.session_state["user_id"] = f"guest-{uuid.uuid4().hex[:6]}"

    st.title("🤖 SantChat")

    if st.session_state["user_type"] == "guest":
        if st.button("Entrar"):
            st.session_state["show_login"] = True

    if st.session_state.get("show_login"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        if st.button("Fazer login"):
            nome_usuario = email.split("@")[0].lower()
            dados = db.reference(f"usuarios/{nome_usuario}").get()
            if dados and dados.get("email") == email and dados.get("senha") == senha:
                st.session_state["user_type"] = "dev" if dados.get("nivel") == 8 else "comum"
                st.session_state["user_id"] = email
                st.session_state["show_login"] = False
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Login inválido. Verifique seus dados.")

    if "memoria" not in st.session_state:
        st.session_state.memoria = carregar_memoria()
    if "historico" not in st.session_state:
        st.session_state.historico = []
    if "ultima_interacao" not in st.session_state:
        st.session_state.ultima_interacao = datetime.now()

    user_id = st.session_state["user_id"]
    is_dev = st.session_state.get("user_type") == "dev"

    st.markdown("<h3>Chat</h3>", unsafe_allow_html=True)
    for i, msg in enumerate(st.session_state.historico):
        tipo = "Usuário" if msg["origem"] == "user" else "SantChat"
        st.markdown(f"**{tipo}:** {msg['texto']}")

            # 💬 Entrada do usuário
        entrada = st.chat_input("Digite sua mensagem")
        if entrada:
            st.session_state.ultima_interacao = datetime.now()
            st.session_state.historico.append({"origem": "user", "texto": entrada})
            resposta = gerar_resposta(st.session_state.memoria, entrada)
            st.session_state.historico.append({"origem": "assistant", "texto": resposta})
            st.rerun()

    elif choice == "Memória IA":
        st.header("🧠 Memória Global da IA")
        memoria = carregar_memoria()
        st.write(memoria)

    elif choice == "Feedbacks":
        st.header("📊 Feedbacks Recebidos")
        data = db.reference(f"logs/feedbacks/{user_id}").get() or {}
        for k, v in data.items():
            st.write(json.loads(v))

    elif choice == "Configurações":
        st.header("⚙️ Configurações")
        if st.button("Logout"):
            st.session_state.clear()
            st.experimental_rerun()


            # 🧠 Comando de aprendizado global
    if entrada.lower().startswith("/sntevksi"):
        conteudo = entrada[len("/sntevksi"):].strip()
        if conteudo:
            st.session_state.memoria.append(conteudo)
            salvar_memoria(st.session_state.memoria)
            st.success("🧠 Conhecimento adicionado à memória global!")
            return
        else:
            st.warning("⚠️ Digite algo após /sntevksi para ensinar à IA.")
        return

if __name__ == "__main__":
    main()
