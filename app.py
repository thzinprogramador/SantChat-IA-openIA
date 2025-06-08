import streamlit as st
import os
import json
from datetime import datetime
import openai
import socket
import requests

# ⬇️ Este deve vir aqui (antes de qualquer `st.` abaixo)
st.set_page_config(page_title="SantChat", page_icon="🤖", layout="centered")


# 🔧 Firebase
import firebase_admin
from firebase_admin import credentials, db

# 🔐 Inicializa Firebase (apenas uma vez)
if not firebase_admin._apps:
    firebase_key = {
        "type": st.secrets.FIREBASE_KEY["type"],
        "project_id": st.secrets.FIREBASE_KEY["project_id"],
        "private_key_id": st.secrets.FIREBASE_KEY["private_key_id"],
        "private_key": st.secrets.FIREBASE_KEY["private_key"].replace("\\n", "\n"),
        "client_email": st.secrets.FIREBASE_KEY["client_email"],
        "client_id": st.secrets.FIREBASE_KEY["client_id"],
        "auth_uri": st.secrets.FIREBASE_KEY["auth_uri"],
        "token_uri": st.secrets.FIREBASE_KEY["token_uri"],
        "auth_provider_x509_cert_url": st.secrets.FIREBASE_KEY["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets.FIREBASE_KEY["client_x509_cert_url"],
        "universe_domain": st.secrets.FIREBASE_KEY.get("universe_domain", "googleapis.com")
    }

    cred = credentials.Certificate(firebase_key)
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://santchat-ia-default-rtdb.firebaseio.com"
    })

# 🔑 Configurações de segurança e API
OPENROUTER_KEY = st.secrets["OPENROUTER_KEY"]
SENHA_ATIVADA = str(st.secrets.get("SENHA_ATIVADA", "false")).lower() == "true"
SENHA_PADRAO = st.secrets.get("SENHA_PADRAO", "1234")

openai.api_key = OPENROUTER_KEY
openai.base_url = "https://openrouter.ai/api/v1"

# 📥 Carrega memória do Firebase
def carregar_memoria():
    try:
        ref = db.reference("memoria_global")
        memoria = ref.get()
        return memoria if isinstance(memoria, list) else []
    except Exception as e:
        print(f"Erro ao carregar memória: {e}")
        return []

# 📤 Salva memória no Firebase
def salvar_memoria(memoria):
    try:
        ref = db.reference("memoria_global")
        ref.set(memoria)
    except Exception as e:
        st.error(f"Erro ao salvar memória: {e}")
        print(f"Erro ao salvar memória: {e}")

# 🛠 Salva erros globais no Firebase
def salvar_erro(erro, contexto="geral"):
    try:
        agora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        ref = db.reference(f"logs/erros/{contexto}")
        ref.update({agora: str(erro)})
    except Exception as e:
        print(f"Falha ao salvar log de erro: {e}")

# 📝 Log por IP
def salvar_log(ip, conteudo):
    try:
        agora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        ref = db.reference(f"logs/{ip.replace(':', '_')}")
        ref.update({agora: conteudo})
    except Exception as e:
        st.error(f"Erro ao salvar log: {e}")
        print(f"Erro ao salvar log: {e}")

# 🌐 IP do usuário
def obter_ip():
    try:
        return st.query_params.get("ip", ["localhost"])[0]
    except:
        return "localhost"

# 🤖 Gera resposta com contexto de memória
def gerar_resposta(memoria, prompt):
    mensagens = [{
        "role": "system",
        "content": "Você é o SantChat, um assistente virtual inteligente. Responda com clareza e empatia."
    }]

    if memoria:
        memoria_texto = "\n".join(memoria)
        mensagens.append({"role": "system", "content": f"Memória global da IA:\n{memoria_texto}"})

    mensagens.append({"role": "user", "content": prompt})

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://santchat.streamlit.app/",
                "X-Title": "SantChat",
            },
            json={
                "model": "nousresearch/deephermes-3-mistral-24b-preview:free",
                "messages": mensagens,
                "max_tokens": 500,
                "temperature": 0.7,
            },
        )

        if response.status_code != 200:
            erro_msg = f"Erro HTTP {response.status_code}: {response.text}"
            salvar_erro(erro_msg, contexto="resposta_ia")
            return erro_msg

        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        salvar_erro(e, contexto="resposta_ia")
        return f"Erro na API: {str(e)}"

# 🚀 Interface principal
def main():
        # 🎨 Tema escuro + estilo fixo
    st.markdown("""
    <style>
        /* Redefine fundo e fonte */
        html, body {
            background-color: #111111;
            color: #ffffff;
            font-family: 'Segoe UI', sans-serif;
        }

        /* Cabeçalho fixo no topo real */
        .chat-header {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            background-color: #111111;
            padding: 16px 0 8px 0;
            border-bottom: 1px solid #444;
            z-index: 1000;
        }

        .chat-header h1 {
            color: #ec0000; /* Vermelho Santander */
            font-size: 1.8em;
            margin: 0;
        }

        .chat-header p {
            color: #aaa;
            margin: 4px 0 0;
            font-size: 0.9em;
        }

        /* Espaço extra para o conteúdo não ficar embaixo do cabeçalho */
        .block-container {
            padding-top: 100px !important;
            padding-bottom: 100px !important;
        }

        /* Rodapé com aviso estilo ChatGPT */
        .disclaimer {
            font-size: 0.85em;
            color: #999;
            text-align: center;
            padding-top: 25px;
            border-top: 1px solid #333;
            margin-top: 40px;
        }

        /* Caixa de entrada ajustada para não cobrir rodapé */
        section.main > div:has(div[data-testid="stChatInput"]) {
            margin-bottom: 30px;
        }
    </style>
""", unsafe_allow_html=True)


    # 🎯 Cabeçalho fixo
    st.markdown("""
    <div class='chat-header'>
        <h1>🤖 <strong>SantChat</strong></h1>
        <p>IA interna para colaboradores do Santander</p>
    </div>
""", unsafe_allow_html=True)



    # 🔒 Validação da senha (opcional)
    if SENHA_ATIVADA:
        if "senha_valida" not in st.session_state:
            senha_input = st.text_input("Digite a senha:", type="password")
            if st.button("Entrar"):
                if senha_input == SENHA_PADRAO:
                    st.session_state["senha_valida"] = True
                    st.experimental_rerun()
                else:
                    st.warning("Senha incorreta.")
                    st.stop()
        elif not st.session_state["senha_valida"]:
            st.stop()

    # 📡 IP do usuário
    ip_usuario = obter_ip()

    # 📖 Memória persistente
    if "memoria" not in st.session_state:
        st.session_state.memoria = carregar_memoria()

    # 💬 Histórico de conversa
    if "historico" not in st.session_state:
        st.session_state.historico = []

    for chat in st.session_state.historico:
        with st.chat_message("user"):
            st.markdown(chat["user"])
        with st.chat_message("assistant"):
            st.markdown(chat["bot"])

    entrada_usuario = st.chat_input("Digite sua mensagem")

    if entrada_usuario:
        salvar_log(ip_usuario, f"Usuário: {entrada_usuario}")

        # 🧠 Comando especial para aprendizado global
        if entrada_usuario.lower().startswith("/sntevksi"):
            novo_conhecimento = entrada_usuario[len("/sntevksi"):].strip()
            if novo_conhecimento:
                try:
                    st.session_state.memoria.append(novo_conhecimento)
                    st.write("🧠 Novo conhecimento adicionado à memória:", novo_conhecimento)
                    salvar_memoria(st.session_state.memoria)
                    memoria_check = carregar_memoria()
                    st.write("📦 Memória após salvar:", memoria_check)
                    resposta = "✅ Conhecimento adicionado à memória global!"
                except Exception as e:
                    st.error(f"❌ Erro ao salvar memória: {e}")
                    resposta = "⚠️ Ocorreu um erro ao tentar salvar a memória."
            else:
                resposta = "⚠️ Por favor, escreva algo após o comando /sntevksi."
        else:
            resposta = gerar_resposta(st.session_state.memoria, entrada_usuario)

        # 🧾 Atualiza histórico e log
        st.session_state.historico.append({"user": entrada_usuario, "bot": resposta})
        salvar_log(ip_usuario, f"Bot: {resposta}")

        with st.chat_message("user"):
            st.markdown(entrada_usuario)
        with st.chat_message("assistant"):
            st.markdown(resposta)

# ⚠️ Rodapé 
st.markdown("""
    <div class="disclaimer">
        ⚠️ O SantChat pode cometer erros. Verifique informações importantes antes de tomar decisões.
    </div>
""", unsafe_allow_html=True)

# 🟢 Inicia app
if __name__ == "__main__":
    main()
