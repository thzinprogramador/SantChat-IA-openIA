import streamlit as st
import os
import json
from datetime import datetime
import openai
import socket
import requests

# 🔧 Firebase: Importa bibliotecas necessárias
import firebase_admin
from firebase_admin import credentials, db

# 🔐 Inicializa o Firebase apenas uma vez, usando a chave do projeto (firebase_key.json)
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_key.json")  # Arquivo gerado no Firebase Console
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://santchat-ia-default-rtdb.firebaseio.com"  # ⬅️ Substitua pela sua URL do Firebase Realtime Database
    })

# 📦 Configurações de segurança e chave da API OpenRouter
OPENROUTER_KEY = st.secrets.get("OPENROUTER_KEY", "")
SENHA_ATIVADA = str(st.secrets.get("SENHA_ATIVADA", "false")).lower() == "true"
SENHA_PADRAO = st.secrets.get("SENHA_PADRAO", "1234")

# 🔑 Define chave da API e URL base da OpenRouter
openai.api_key = OPENROUTER_KEY
openai.base_url = "https://openrouter.ai/api/v1"

# 📁 Pasta onde logs por IP são armazenados
LOGS_DIR = "logs"

# 🧠 Carrega a memória da IA do Firebase
def carregar_memoria():
    try:
        ref = db.reference("memoria_global")
        memoria = ref.get()
        if memoria is None:
            return []
        return memoria  # Deve retornar lista
    except Exception as e:
        print(f"Erro ao carregar memória do Firebase: {e}")
        return []

# 💾 Salva a memória da IA no Firebase
def salvar_memoria(memoria):
    try:
        ref = db.reference("memoria_global")
        ref.set(memoria)  # Espera uma lista, como: ["item1", "item2"]
    except Exception as e:
        print(f"Erro ao salvar memória no Firebase: {e}")

# 📝 Salva logs da conversa em arquivos separados por IP
def salvar_log(ip, conteudo):
    try:
        agora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        ref = db.reference(f"logs/{ip.replace(':', '_')}")
        ref.update({agora: conteudo})
    except Exception as e:
        print(f"Erro ao salvar log no Firebase: {e}")


# 🌐 Obtém o IP do usuário (via query string ou local)
def obter_ip():
    try:
        ip = st.query_params.get("ip", ["localhost"])[0]
    except:
        ip = "localhost"
    return ip

# 🧠 Gera resposta com base no histórico de memória e mensagem do usuário
def gerar_resposta(memoria, prompt):
    mensagens = [{"role": "system", "content": "Você é o SantChat, um assistente virtual inteligente. Sua função é responder perguntas sobre atendimento e dúvidas recorrentes no geral. Sempre responda de forma clara, profissional e empática. Evite repetir a pergunta e não invente informações. Seja preciso."}]
    
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
            return f"Erro na API OpenRouter: resposta inválida. Conteúdo bruto:\n{json.dumps(data, indent=2, ensure_ascii=False)}"

        resposta = data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        resposta = f"Erro na API OpenRouter: {str(e)}"

    return resposta

# 🚀 Função principal da interface
def main():
    st.set_page_config(page_title="SantChat", page_icon="🤖", layout="centered")
    st.markdown("<h1 style='text-align: center;'>SantChat - IA Interna Santander</h1>", unsafe_allow_html=True)

    # 🔐 Proteção por senha, se ativado via st.secrets
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
                    st.session_state["login_tentado"] = False
                    st.experimental_rerun()
                else:
                    st.session_state["senha_valida"] = False

            if st.session_state["login_tentado"] and senha_input != SENHA_PADRAO:
                st.warning("Senha incorreta.")
            st.stop()

    # 🧠 Memória e IP
    memoria = carregar_memoria()
    ip_usuario = obter_ip()

    if "historico" not in st.session_state:
        st.session_state.historico = []

    # 💬 Exibe histórico de mensagens estilo bolha
    for chat in st.session_state.historico:
        with st.chat_message("user"):
            st.markdown(chat["user"])
        with st.chat_message("assistant"):
            st.markdown(chat["bot"])

    # 📥 Input do usuário
    entrada_usuario = st.chat_input("Digite sua mensagem")

    if entrada_usuario:
        salvar_log(ip_usuario, f"Usuário: {entrada_usuario}")

        # 🧠 Comando para atualizar memória da IA
    if entrada_usuario.lower().startswith("/sntevksi"):
    # Extrai o conteúdo da mensagem após o comando
    novo_conhecimento = entrada_usuario[len("/sntevksi"):].strip()
    
    if novo_conhecimento:
        # Adiciona o novo conhecimento à memória e salva no Firebase
        memoria.append(novo_conhecimento)
        salvar_memoria(memoria)
        resposta = "Memória atualizada com sucesso!"
    else:
        resposta = "Por favor, envie uma frase para aprender após o comando /sntevksi."

    else:
        resposta = gerar_resposta(memoria, entrada_usuario)

    # 📦 Atualiza histórico e salva log da resposta
    st.session_state.historico.append({"user": entrada_usuario, "bot": resposta})
    salvar_log(ip_usuario, f"Bot: {resposta}")

    # 💬 Mostra nova mensagem em tempo real
    with st.chat_message("user"):
        st.markdown(entrada_usuario)
    with st.chat_message("assistant"):
        st.markdown(resposta)

# 🟢 Executa app
if __name__ == "__main__":
    main()
