import streamlit as st
import os
import json
import uuid
from datetime import datetime, timedelta  
import openai
import requests
import firebase_admin
from firebase_admin import credentials, db

# --- Configurações de Cores ---
COR_PRIMARIA = "#FF0000"  # Vermelho Santander
COR_SECUNDARIA = "#002982"  # Azul escuro
COR_TERCIARIA = "#00F238"  # Verde água
COR_TEXTO = "#00F238"
COR_FUNDO = "#002982"
COR_BOTAO = "#ec0000"
COR_BOTAO_HOVER = "#c50000"

# --- Configurações iniciais ---
st.set_page_config(
    page_title="SantChat", 
    page_icon="🤖", 
    layout="centered",
    initial_sidebar_state="auto"
)

# --- Estilos CSS ---
def load_css():
    st.markdown(f"""
    <style>
        :root {{
            --color-bg: {COR_FUNDO};
            --color-text-primary: {COR_TEXTO};
            --color-text-secondary: #555555;
            --color-accent: {COR_PRIMARIA};
            --color-accent-hover: {COR_BOTAO_HOVER};
            --color-button-bg: {COR_SECUNDARIA};
            --color-button-text: #ffffff;
            --color-shadow: rgba(0,0,0,0.05);
            --radius: 8px;
            --spacing: 1rem;
            --header-height: 70px;
            --max-width: 1000px;
            --color-welcome: {COR_TERCIARIA};
        }}
        
        body {{
            margin: 0;
            background: var(--color-bg);
            font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
                Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            color: var(--color-text-secondary);
            font-size: 16px;
            line-height: 1.5;
        }}
        
        .header {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: var(--header-height);
            background: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
            padding: 0 20px;
            z-index: 1000;
        }}
        
        .logo {{
            font-weight: 800;
            font-size: 1.8rem;
            color: var(--color-accent);
            display: flex;
            align-items: center;
        }}
        
        .logo img {{
            height: 30px;
            margin-right: 10px;
        }}
        
        .login-btn {{
            margin-left: auto;
            background: var(--color-accent);
            color: white;
            border: none;
            border-radius: var(--radius);
            padding: 8px 20px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .login-btn:hover {{
            background: var(--color-accent-hover);
            transform: translateY(-1px);
        }}
        
        .main-container {{
            max-width: var(--max-width);
            margin: 0 auto;
            padding: 20px;
            padding-top: calc(var(--header-height) + 20px);
        }}
        
        .welcome-title {{
            color: var(--color-welcome);
            font-size: 2.2rem;
            margin-bottom: 10px;
        }}
        
        .welcome-subtitle {{
            color: var(--color-text-secondary);
            font-size: 1.1rem;
            margin-bottom: 30px;
        }}
        
        .chat-container {{
            background: #f9f9f9;
            border-radius: var(--radius);
            padding: 20px;
            margin-bottom: 20px;
            min-height: 300px;
            max-height: 500px;
            overflow-y: auto;
        }}
        
        .user-msg {{
            background: #e6f2ff;
            color: var(--color-text-primary);
            padding: 12px 16px;
            border-radius: var(--radius);
            margin: 10px 0 10px auto;
            max-width: 80%;
            box-shadow: 0 1px 3px var(--color-shadow);
        }}
        
        .bot-msg {{
            background: white;
            color: var(--color-text-primary);
            padding: 12px 16px;
            border-radius: var(--radius);
            margin: 10px auto 10px 0;
            max-width: 80%;
            box-shadow: 0 1px 3px var(--color-shadow);
            border-left: 4px solid var(--color-accent);
        }}
        
        .feedback-buttons {{
            display: flex;
            gap: 8px;
            margin-top: 10px;
        }}
        
        .feedback-btn {{
            background: #f0f0f0;
            border: none;
            border-radius: 50%;
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .feedback-btn:hover {{
            background: #e0e0e0;
            transform: scale(1.1);
        }}
        
        .message-input {{
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }}
        
        .message-input textarea {{
            flex: 1;
            border-radius: var(--radius);
            border: 1px solid #ddd;
            padding: 10px;
            resize: none;
            font-family: inherit;
        }}
        
        .message-input button {{
            background: var(--color-accent);
            color: white;
            border: none;
            border-radius: var(--radius);
            padding: 0 20px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .message-input button:hover {{
            background: var(--color-accent-hover);
        }}
        
        /* Sidebar styles */
        .sidebar-content {{
            padding-top: 20px;
        }}
        .sidebar-title {{
            color: var(--color-accent);
            font-size: 1.5rem;
            margin-bottom: 20px;
        }}
        
        .user-greeting {{
            font-weight: 600;
            color: var(--color-accent);
            margin-bottom: 20px;
        }}
        
        @media (max-width: 768px) {{
            .header {{
                padding: 0 15px;
            }}
            
            .logo {{
                font-size: 1.5rem;
            }}
            
            .login-btn {{
                padding: 6px 15px;
                font-size: 0.9rem;
            }}
        }}
        
        /* Remove o quadrado branco */
        .stApp {{
            background-color: transparent !important;
        }}
        .block-container {{
            padding-top: 0 !important;
        }}
    </style>
    """, unsafe_allow_html=True)

# --- Firebase Initialization ---
def initialize_firebase():
    if not firebase_admin._apps:
        firebase_key = {k: (v.replace("\n", "\n") if k == "private_key" else v)
                        for k, v in st.secrets["FIREBASE_KEY"].items()}
        firebase_admin.initialize_app(
            credentials.Certificate(firebase_key),
            {"databaseURL": st.secrets["FIREBASE_KEY_DB_URL"]}
        )

# --- Funções Auxiliares ---
def carregar_memoria():
    try:
        ref = db.reference("memoria_global")
        memoria = ref.get()
        return memoria if isinstance(memoria, list) else []
    except Exception as e:
        st.error(f"Erro ao carregar memória: {str(e)}")
        return []

def salvar_memoria(mem):
    try:
        db.reference("memoria_global").set(mem)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar memória: {str(e)}")
        return False

def salvar_feedback(user_id, pergunta, resposta, comentario):
    try:
        ref = db.reference(f"logs/feedbacks/{user_id}")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        feedback_data = {
            "pergunta": pergunta,
            "resposta": resposta,
            "feedback": comentario,
            "timestamp": datetime.now().isoformat()
        }
        ref.child(ts).set(feedback_data)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar feedback: {str(e)}")
        return False

def salvar_historico(user_id, historico):
    try:
        if not historico:
            return False
        
        primeira_msg = historico[0]["texto"][:50]
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        ref = db.reference(f"logs/usuarios/{user_id}/historico/{ts}")
        ref.set({
            "titulo": primeira_msg,
            "mensagens": historico,
            "timestamp": datetime.now().isoformat()
        })
        return True
    except Exception as e:
        st.error(f"Erro ao salvar histórico: {str(e)}")
        return False

def criar_usuario(email, senha, nome_usuario):
    try:
        user_id = email.split("@")[0].lower()
        ref = db.reference(f"usuarios/{user_id}")
        
        if ref.get():
            return False, "Usuário já existe"
            
        ref.set({
            "email": email,
            "senha": senha,
            "nome_usuario": nome_usuario,
            "nivel": 0,  # Nível padrão 0 (usuário comum)
            "criado_em": datetime.now().isoformat()
        })
        return True, "Usuário criado com sucesso"
    except Exception as e:
        return False, f"Erro ao criar usuário: {str(e)}"

def autenticar_usuario(email, senha):
    try:
        user_id = email.split("@")[0].lower()
        ref = db.reference(f"usuarios/{user_id}")
        usuario = ref.get()
        
        if not usuario:
            return False, None, "Usuário não encontrado"
            
        if usuario.get("senha") != senha:
            return False, None, "Senha incorreta"
            
        return True, usuario, "Login bem-sucedido"
    except Exception as e:
        return False, None, f"Erro na autenticação: {str(e)}"

def processar_comando_dev(comando, user_data):
    if user_data.get("nivel", 0) != -8:  # Nível de dev
        return None, "Acesso negado"
    
    if comando.startswith("/sntevksi "):
        info = comando.replace("/sntevksi ", "").strip()
        memoria = carregar_memoria()
        memoria.append(info)
        if salvar_memoria(memoria):
            return True, "Informação adicionada à memória global com sucesso!"
        else:
            return False, "Erro ao salvar na memória"
    
    return None, None

def gerar_resposta(memoria, prompt, user_name=None):
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    saudacao = f"Olá {user_name}," if user_name else "Olá,"
    
    system_prompt = f"""
    Hoje é {agora}. Você é o SantChat, IA oficial do Santander.
    {saudacao} responda com clareza e de forma personalizada.
    Não invente informações sobre datas ou produtos.
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

# --- Componentes da UI ---
def render_header():
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"""
        <div class="logo">
            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/Santander_Bank_logo.svg/1200px-Santander_Bank_logo.svg.png" alt="Santander Logo">
            SantChat
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.session_state.get("user_type") == "guest":
            if st.button("Entrar", key="header_login_btn"):
                st.session_state.show_login = True
                st.rerun()
        else:
            if st.button("Sair", key="header_logout_btn"):
                st.session_state.clear()
                st.rerun()

def render_login_sidebar():
    with st.sidebar:
        if st.session_state.get("user_type") != "guest":
            user_name = st.session_state.get("user_data", {}).get("nome_usuario", "Usuário")
            st.markdown(f'<div class="user-greeting">Olá, {user_name}!</div>', unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="sidebar-content">
            <div class="sidebar-title">Menu</div>
        """, unsafe_allow_html=True)
        
        if st.session_state.get("show_login"):
            st.subheader("Login")
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            
            if st.button("Entrar", key="login_btn"):
                success, user, message = autenticar_usuario(email, senha)
                if success:
                    st.session_state.update({
                        "user_type": "user",
                        "user_id": user["email"],
                        "show_login": False,
                        "user_data": user
                    })
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            
            st.divider()
            st.subheader("Criar conta")
            new_email = st.text_input("Novo e-mail")
            new_pass = st.text_input("Nova senha", type="password")
            new_username = st.text_input("Nome de usuário")
            if st.button("Registrar"):
                success, message = criar_usuario(new_email, new_pass, new_username)
                if success:
                    st.success(message)
                else:
                    st.error(message)
        
        menu_itens = ["Chat"]
        if st.session_state.get("user_data", {}).get("nivel") == -8:  # Dev
            menu_itens += ["Memória IA", "Feedbacks"]
        
        choice = st.radio("Navegação", menu_itens)
        
        if st.session_state.get("user_type") != "guest" and st.button("Logout"):
            st.session_state.clear()
            st.rerun()

    return choice if "choice" in locals() else "Chat"

def render_memoria_ia():
    st.subheader("Memória Global da IA")
    memoria = carregar_memoria()
    
    if st.button("Atualizar Memória"):
        memoria = carregar_memoria()
        st.rerun()
    
    st.text_area("Conteúdo da Memória", value="\n".join(memoria), height=300)
    
    st.subheader("Adicionar à Memória")
    nova_info = st.text_area("Nova informação para a memória")
    if st.button("Salvar na Memória"):
        memoria.append(nova_info)
        if salvar_memoria(memoria):
            st.success("Informação adicionada com sucesso!")
        else:
            st.error("Erro ao salvar na memória")

def render_feedbacks():
    st.subheader("Feedbacks dos Usuários")
    
    try:
        ref = db.reference("logs/feedbacks")
        feedbacks = ref.get()
        
        if not feedbacks:
            st.info("Nenhum feedback encontrado")
            return
            
        for user_id, user_feedbacks in feedbacks.items():
            with st.expander(f"Feedbacks de {user_id}"):
                for timestamp, feedback in user_feedbacks.items():
                    st.write(f"**Data:** {feedback.get('timestamp')}")
                    st.write(f"**Pergunta:** {feedback.get('pergunta')}")
                    st.write(f"**Resposta:** {feedback.get('resposta')}")
                    st.write(f"**Feedback:** {feedback.get('feedback')}")
                    st.divider()
    except Exception as e:
        st.error(f"Erro ao carregar feedbacks: {str(e)}")

def render_chat_interface():
    st.markdown(f"""
    <div class="main-container">
        <h1 class="welcome-title">Bem-vindo ao SantChat</h1>
        <p class="welcome-subtitle">Seu chat inteligente.</p>
    """, unsafe_allow_html=True)

    # Container do chat
    chat_container = st.container()
    with chat_container:
        st.markdown('<div class="chat-container" id="chat-messages">', unsafe_allow_html=True)
        
        # Mostrar histórico de mensagens
        if "messages" not in st.session_state:
            user_name = st.session_state.get("user_data", {}).get("nome_usuario")
            saudacao = f"Olá {user_name}," if user_name else "Olá,"
            
            st.session_state.messages = [
                {"sender": "bot", "text": f"{saudacao} sou o SantChat, IA oficial do Santander. Estou aqui pra ajudar com qualquer dúvida ou solicitação sobre nossos produtos e serviços.\n\nEm que posso te ajudar hoje?"}
            ]
        
        for message in st.session_state.messages:
            if message["sender"] == "user":
                st.markdown(f'<div class="user-msg">{message["text"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bot-msg">{message["text"]}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Input de mensagem
    with st.form(key="message_form", clear_on_submit=True):
        user_input = st.text_area("Digite sua mensagem:", key="user_input", height=100, value="")
        submit_button = st.form_submit_button(label="Enviar")
        
        if submit_button and user_input:
            # Verificar se é um comando de dev
            user_data = st.session_state.get("user_data", {})
            success, msg = processar_comando_dev(user_input, user_data)
            
            if success is not None:
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
                st.rerun()
            
            # Adiciona mensagem do usuário ao histórico
            st.session_state.messages.append({"sender": "user", "text": user_input})
            
            # Gera resposta do bot
            user_name = user_data.get("nome_usuario")
            resposta = gerar_resposta(
                st.session_state.get("memoria", []), 
                user_input,
                user_name
            )
            
            # Adiciona resposta do bot ao histórico
            st.session_state.messages.append({"sender": "bot", "text": resposta})
            
            # Rerun para atualizar a interface
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# --- Função Principal ---
def main():
    # Carregar configurações
    load_css()
    initialize_firebase()
    
    # Configurar chave da API
    global OPENROUTER_KEY
    OPENROUTER_KEY = st.secrets["OPENROUTER_KEY"]
    openai.api_key = OPENROUTER_KEY
    openai.base_url = "https://openrouter.ai/api/v1"

    # Inicialização do estado da sessão
    if "user_type" not in st.session_state:
        st.session_state.update({
            "user_type": "guest",
            "user_id": f"guest-{uuid.uuid4().hex[:6]}",
            "show_login": False,
            "memoria": carregar_memoria(),
            "historico": []
        })

    # Renderizar componentes
    render_header()
    choice = render_login_sidebar()
    
    # Renderizar conteúdo principal baseado na escolha
    if choice == "Chat":
        render_chat_interface()
    elif choice == "Memória IA" and st.session_state.get("user_data", {}).get("nivel") == -8:
        render_memoria_ia()
    elif choice == "Feedbacks" and st.session_state.get("user_data", {}).get("nivel") == -8:
        render_feedbacks()

if __name__ == "__main__":
    main()
