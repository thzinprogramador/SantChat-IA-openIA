import streamlit as st
import os
import json
from datetime import datetime
import openai
import socket

# Configurações de segurança e chave API via st.secrets
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")
SENHA_ATIVADA = str(st.secrets.get("SENHA_ATIVADA", "false")).lower() == "true"
SENHA_PADRAO = st.secrets.get("SENHA_PADRAO", "1234")

openai.api_key = OPENAI_API_KEY

# Arquivo para salvar memória global da IA
MEMORIA_FILE = "memoria_global.json"

# Pasta logs
LOGS_DIR = "logs"

def carregar_memoria():
    try:
        with open(MEMORIA_FILE, "r", encoding="utf-8") as f:
            memoria = json.load(f)
    except:
        memoria = []
    return memoria

def salvar_memoria(memoria):
    with open(MEMORIA_FILE, "w", encoding="utf-8") as f:
        json.dump(memoria, f, indent=2, ensure_ascii=False)

def salvar_log(ip, conteudo):
    pasta_ip = os.path.join(LOGS_DIR, ip.replace(":", "_"))
    os.makedirs(pasta_ip, exist_ok=True)
    agora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    arquivo_log = os.path.join(pasta_ip, f"{agora}.txt")
    with open(arquivo_log, "a", encoding="utf-8") as f:
        f.write(conteudo + "\n")

def obter_ip():
    # Streamlit Cloud não disponibiliza IP real do usuário via request.
    # Como alternativa temporária, pode usar o hostname ou ip local.
    # Aqui usamos localhost porque IP real do cliente não é acessível.
    try:
        ip = st.experimental_get_query_params().get("ip", ["localhost"])[0]
    except:
        ip = "localhost"
    return ip

def gerar_resposta(memoria, prompt):
    mensagens = [{"role": "system", "content": "Você é uma IA superinteligente e direta."}]
    # Inserir memória global no contexto
    if memoria:
        memoria_texto = "\n".join(memoria)
        mensagens.append({"role": "system", "content": f"Memória global da IA:\n{memoria_texto}"})
    mensagens.append({"role": "user", "content": prompt})

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=mensagens,
            max_tokens=500,
            temperature=0.7,
        )
        resposta = response.choices[0].message.content.strip()
    except Exception as e:
        resposta = f"Erro na API OpenAI: {str(e)}"
    return resposta

def main():
    st.title("SantChat - IA Interna Santander")

    if SENHA_ATIVADA:
        senha = st.text_input("Digite a senha:", type="password")
        if senha != SENHA_PADRAO:
            st.warning("Senha incorreta.")
            st.stop()

    memoria = carregar_memoria()
    ip_usuario = obter_ip()

    if "historico" not in st.session_state:
        st.session_state.historico = []

    entrada_usuario = st.text_input("Digite sua mensagem:")

    if entrada_usuario:
        # Salvar no log
        salvar_log(ip_usuario, f"Usuário: {entrada_usuario}")

        # Verifica se comando de aprendizado
        if entrada_usuario.lower().startswith("/sntevksi"):
            novo_conhecimento = entrada_usuario[len("/sntevksi"):].strip()
            if novo_conhecimento:
                memoria.append(novo_conhecimento)
                salvar_memoria(memoria)
                resposta = "Memória atualizada com sucesso!"
            else:
                resposta = "Por favor, envie uma frase para aprender após o comando /sntevksi."
        else:
            resposta = gerar_resposta(memoria, entrada_usuario)

        st.session_state.historico.append({"user": entrada_usuario, "bot": resposta})
        salvar_log(ip_usuario, f"Bot: {resposta}")

    for chat in st.session_state.historico:
        st.markdown(f"**Você:** {chat['user']}")
        st.markdown(f"**IA:** {chat['bot']}")

if __name__ == "__main__":
    main()
