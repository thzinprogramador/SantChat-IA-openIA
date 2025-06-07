import streamlit as st
import os
import json
from datetime import datetime
import openai
import socket
import requests

# 🔧 Firebase
import firebase_admin
from firebase_admin import credentials, db

# 🔐 Inicializa Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://santchat-ia-default-rtdb.firebaseio.com"
    })

# 🔑 Configurações
OPENROUTER_KEY = st.secrets.get("OPENROUTER_KEY", "")
SENHA_ATIVADA = str(st.secrets.get("SENHA_ATIVADA", "false")).lower() == "true"
SENHA_PADRAO = st.secrets.get("SENHA_PADRAO", "1234")

openai.api_key = OPENROUTER_KEY
openai.base_url = "https://openrouter.ai/api/v1"

# 🧠 Memória Firebase
def carregar_memoria():
    try:
        ref = db.reference("memoria_global")
        memoria = ref.get()
        return memoria if memoria else []
    except Exception as e:
        print(f"Erro ao carregar memória: {e}")
        return []

def salvar_memoria(memoria):
    try:
        ref = db.reference("memoria_global")
        ref.set(memoria)
    except Exception as e:
        print(f"Erro ao salvar memória: {e}")

def salvar_log(ip, conteudo):
    try:
        agora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        ref = db.reference(f"logs/{ip.replace(':', '_')}")
        ref.update({agora: conteudo})
    except Exception as e:
        print(f"Erro ao salvar log: {e}")

def obter_ip():
    try:
        return st.query_params.get("ip", ["localhost"])[0]
    except:
        return "localhost"

# 🤖 Gera resposta
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
            return f"Erro HTTP {response.status_code}: {response.text}"

        data = response.json()
        if "choices" not in data or not data["choices"]:
            return f"Erro: resposta inválida da API.\n{json.dumps(data, indent=2)}"

        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        return f"Erro na API: {str(e)}"

# 🚀 Interface principal
def main():
    st.set_page_config(page_title="SantChat", page_icon="🤖", layout="centered")
    st.markdown("<h1 style='text-align: center;'>SantChat - IA Interna Santander</h1>", unsafe_allow_html=True)

    if SENHA_ATIVADA:
        if "login_tentado" not in st.session_state:
            st.session_state["login_tentado"] = False
        if "senha_valida" not in st.session_state:
            st.session_state["senha_valida"] = False

        if not st.session_state["senha_valida"]:
            senha_input = st.text_input("Digite a senha:", type="password")
            if st.button("Entrar"):
                st.session_state["login_tentado"] = True
                if senha_input == SENHA_PADRAO:
                    st.session_state["senha_valida"] = True
                    st.experimental_rerun()
                else:
                    st.warning("Senha incorreta.")
                    st.stop()

    memoria = carregar_memoria()
    ip_usuario = obter_ip()

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

        if entrada_usuario.lower().startswith("/sntevksi"):
            novo_conhecimento = entrada_usuario[len("/sntevksi"):].strip()
            if novo_conhecimento:
                memoria.append(novo_conhecimento)
                salvar_memoria(memoria)
                resposta = "Memória atualizada com sucesso!"
            else:
                resposta = "Envie algo após o comando /sntevksi para adicionar à memória."
        else:
            resposta = gerar_resposta(memoria, entrada_usuario)

        st.session_state.historico.append({"user": entrada_usuario, "bot": resposta})
        salvar_log(ip_usuario, f"Bot: {resposta}")

        with st.chat_message("user"):
            st.markdown(entrada_usuario)
        with st.chat_message("assistant"):
            st.markdown(resposta)

# 🟢 Run
if __name__ == "__main__":
    main()
