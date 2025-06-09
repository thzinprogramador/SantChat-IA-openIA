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
COR_PRIMARIA = "#ec0000"  # Vermelho Santander
COR_SECUNDARIA = "#222222"  # Azul escuro
COR_TERCIARIA = "#00F238"  # Verde água
COR_TEXTO = "#FFFFFF"  # Texto branco para contraste com fundo escuro
COR_FUNDO = "#292A2D"  # Fundo escuro
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
            --color-text-secondary: #CCCCCC;
            --color-accent: {COR_PRIMARIA};
            --color-accent-hover: {COR_BOTAO_HOVER};
            --color-button-bg: {COR_SECUNDARIA};
            --color-button-text: #ffffff;
            --color-shadow: rgba(0,0,0,0.05);
            --radius: 8px;
            --spacing: 1rem;
            --header-height: 70px;
            --max-width: 1000px;
            --color-welcome: #FF0000;
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
            background: {COR_FUNDO};
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
            padding: 0 20px;
            z-index: 1000;
            border-bottom: 1px solid #444;
        }}
        
        .logo {{
            font-weight: 800;
            font-size: 1.8rem;
            color: {COR_PRIMARIA};
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
            background-color: {COR_FUNDO};
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
            background: #333333;
            border-radius: var(--radius);
            overflow-y: auto;
            box-shadow: rgba(0,0,0,0.1);
            border: 1px solid #444;
        }}
        
        .user-msg {{
            background: #444444;
            color: var(--color-text-primary);
            padding: 12px 16px;
            border-radius: var(--radius);
            margin: 10px 0 10px auto;
            max-width: 80%;
            box-shadow: 0 1px 3px var(--color-shadow);
            border: 1px solid #555;
        }}
        
        .bot-msg {{
            background: #3A3A3A;
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
            justify-content: flex-end;
        }}
        
        .feedback-btn {{
            background: #555;
            border: none;
            border-radius: 50%;
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s;
            color: white;
        }}
        
        .feedback-btn:hover {{
            background: #666;
            transform: scale(1.1);
        }}
        
        .message-input {{
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            width: 80%;
            max-width: 800px;
            display: flex;
            gap: 10px;
            margin-top: 20px;
            background: {COR_FUNDO};
            padding: 10px;
            border-radius: var(--radius);
            z-index: 100;
        }}
        
        .message-input textarea {{
            flex: 1;
            border-radius: var(--radius);
            border: 1px solid #555;
            padding: 10px;
            resize: none;
            font-family: inherit;
            background-color: #333;
            color: white;
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
        .sidebar .sidebar-content {{
            background-color: {COR_FUNDO};
            padding: 20px;
            border-right: 1px solid #444;
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
            font-size: 1.2rem;
        }}
        
        .new-chat-btn {{
            background: var(--color-accent);
            color: white;
            border: none;
            border-radius: var(--radius);
            padding: 10px;
            width: 100%;
            font-weight: 600;
            cursor: pointer;
            margin-bottom: 20px;
            transition: all 0.2s;
        }}
        
        .new-chat-btn:hover {{
            background: var(--color-accent-hover);
        }}
        
        .chat-history {{
            margin-top: 20px;
        }}
        
        .chat-history-item {{
            padding: 8px 12px;
            margin-bottom: 5px;
            border-radius: var(--radius);
            cursor: pointer;
            background-color: #333;
            color: white;
            transition: all 0.2s;
        }}
        
        .chat-history-item:hover {{
            background-color: #444;
        }}
        
        .chat-history-item.active {{
            background-color: var(--color-accent);
            color: white;
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
            
            .message-input {{
                width: 90%;
            }}
        }}
        
        /* Remove o quadrado branco */
        .stApp {{
            background-color: {COR_FUNDO} !important;
        }}
        .block-container {{
            padding-top: 0 !important;
            background-color: {COR_FUNDO} !important;
        }}
        
        /* Estilo das abas */
        .stRadio > div {{
            flex-direction: column;
            align-items: flex-start;
        }}
        
        .stRadio > div > label {{
            margin-bottom: 10px;
            padding: 8px 12px;
            border-radius: var(--radius);
            transition: all 0.2s;
            color: white;
        }}
        
        .stRadio > div > label:hover {{
            background-color: #444;
        }}
        
        .stRadio > div > label > div:first-child {{
            padding-left: 8px;
        }}
        
        /* Remove borda branca do chat */
        .stChatMessage {{
            background-color: transparent !important;
        }}
        
        /* Centralizar conteúdo */
        .st-emotion-cache-1v0mbdj {{
            margin: 0 auto;
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

def salvar_feedback(user_id, pergunta, resposta, feedback, tipo):
    try:
        ref = db.reference(f"logs/feedbacks/{user_id}")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        feedback_data = {
            "pergunta": pergunta,
            "resposta": resposta,
            "tipo_feedback": tipo,
            "timestamp": datetime.now().isoformat()
        }
        ref.child(ts).set(feedback_data)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar feedback: {str(e)}")
        return False

def salvar_historico_chat(user_id, chat_id, historico):
    try:
        if not historico:
            return False
        
        primeira_msg = historico[0]["text"][:50]
        ref = db.reference(f"logs/usuarios/{user_id}/chats/{chat_id}")
        ref.set({
            "titulo": primeira_msg,
            "mensagens": historico,
            "ultima_atualizacao": datetime.now().isoformat()
        })
        return True
    except Exception as e:
        st.error(f"Erro ao salvar histórico: {str(e)}")
        return False

def carregar_historico_chats(user_id):
    try:
        ref = db.reference(f"logs/usuarios/{user_id}/chats")
        chats = ref.get()
        return chats if chats else {}
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {str(e)}")
        return {}

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

def gerar_resposta(memoria, prompt, user_name=None, historico_conversa=None):
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    # Construir contexto da conversa
    contexto_conversa = ""
    if historico_conversa and len(historico_conversa) > 1:
        contexto_conversa = "\nContexto da conversa atual:\n"
        for msg in historico_conversa[-5:]:  # Pegar as últimas 5 mensagens como contexto
            if msg["sender"] == "user":
                contexto_conversa += f"Usuário: {msg['text']}\n"
            else:
                contexto_conversa += f"Assistente: {msg['text']}\n"
    
    system_prompt = f"""
    Hoje é {agora}. Você é o SantChat, IA oficial do Santander.
    Responda com clareza e de forma direta.
    Não invente informações sobre datas ou produtos.
    Mantenha o contexto da conversa atual.
    {contexto_conversa}
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
                "max_tokens": 50000,
                "temperature": 0.7
            },
            timeout=10
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
    st.markdown(f"""
    <div class="header">
        <div class="logo">
            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/Santander_Bank_logo.svg/1200px-Santander_Bank_logo.svg.png" alt="Santander Logo">
            <span style="color: {COR_PRIMARIA}">SantChat</span>
            <h1> Sou uma IA criada para ajudar você em seus atendimentos</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_login_sidebar():
    with st.sidebar:
        if st.session_state.get("user_type") != "guest":
            # Novo chat
            if st.button("+ Novo chat", key="new_chat_btn", use_container_width=True):
                if "current_chat_id" in st.session_state:
                    # Salva o chat atual antes de criar um novo
                    salvar_historico_chat(
                        st.session_state.user_id,
                        st.session_state.current_chat_id,
                        st.session_state.messages
                    )
                
                # Cria novo chat
                new_chat_id = str(uuid.uuid4())
                st.session_state.current_chat_id = new_chat_id
                st.session_state.messages = [
                    {"sender": "bot", "text": "Olá! Sou o SantChat, IA oficial do Santander. Como posso te ajudar hoje?"}
                ]
                st.rerun()
            
            # Exibir histórico de chats
            st.markdown('<div class="chat-history">', unsafe_allow_html=True)
            st.markdown('<div class="sidebar-title">Histórico de Chats</div>', unsafe_allow_html=True)
            
            chats = carregar_historico_chats(st.session_state.user_id)
            if chats:
                for chat_id, chat_data in chats.items():
                    if st.button(
                        chat_data.get("titulo", "Chat sem título"),
                        key=f"chat_{chat_id}",
                        help=f"Última atualização: {chat_data.get('ultima_atualizacao', '')}",
                        use_container_width=True
                    ):
                        # Carrega o chat selecionado
                        st.session_state.current_chat_id = chat_id
                        st.session_state.messages = chat_data.get("mensagens", [])
                        st.rerun()
            else:
                st.markdown('<div style="color: #999; font-size: 0.9rem;">Nenhum chat anterior</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            if st.session_state.get("user_data"):
                user_name = st.session_state.user_data.get("nome_usuario", "Usuário")
                st.markdown(f'<div class="user-greeting">👋 Olá, {user_name}!</div>', unsafe_allow_html=True)
        
        # Menu de navegação
        st.markdown(f"""
        <div class="sidebar-content">
            <div class="sidebar-title">Menu</div>
        """, unsafe_allow_html=True)
        
        if st.session_state.get("show_login"):
            st.subheader("Login")
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            
            if st.button("Entrar", key="login_btn", use_container_width=True):
                success, user, message = autenticar_usuario(email, senha)
                if success:
                    # Cria um novo chat para o usuário logado
                    new_chat_id = str(uuid.uuid4())
                    
                    st.session_state.update({
                        "user_type": "user",
                        "user_id": user["email"],
                        "show_login": False,
                        "user_data": user,
                        "current_chat_id": new_chat_id,
                        "messages": [
                            {"sender": "bot", "text": "Olá! Sou o SantChat, IA oficial do Santander. Como posso te ajudar hoje?"}
                        ]
                    })
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            
            st.divider()
            st.subheader("Criar conta")
            new_email = st.text_input("Novo e-mail", key="new_email")
            new_pass = st.text_input("Nova senha", type="password", key="new_pass")
            new_username = st.text_input("Nome de usuário", key="new_username")
            if st.button("Registrar", key="register_btn", use_container_width=True):
                success, message = criar_usuario(new_email, new_pass, new_username)
                if success:
                    st.success(message)
                else:
                    st.error(message)
        
        menu_itens = ["Chat"]
        if st.session_state.get("user_data", {}).get("nivel") == -8:  # Dev
            menu_itens += ["Memória IA", "Feedbacks"]
        
        choice = st.radio("Navegação", menu_itens, label_visibility="collapsed")
        
        if st.session_state.get("user_type") != "guest" and st.button("Logout", use_container_width=True):
            # Salva o chat atual antes de fazer logout
            if "current_chat_id" in st.session_state:
                salvar_historico_chat(
                    st.session_state.user_id,
                    st.session_state.current_chat_id,
                    st.session_state.messages
                )
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
                    st.write(f"**Tipo Feedback:** {feedback.get('tipo_feedback')}")
                    st.divider()
    except Exception as e:
        st.error(f"Erro ao carregar feedbacks: {str(e)}")

def render_chat_interface():
    st.markdown(f"""
    <div class="main-container">
        <h1 class="welcome-title">SantChat</h1>
    """, unsafe_allow_html=True)

    # Container do chat
    chat_container = st.container()
    with chat_container:
        st.markdown('<div class="chat-container" id="chat-messages">', unsafe_allow_html=True)
        
        # Mostrar histórico de mensagens
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"sender": "bot", "text": "Olá! Sou o SantChat, IA oficial do Santander. Como posso te ajudar hoje?"}
            ]
        
        for idx, message in enumerate(st.session_state.messages):
            if message["sender"] == "user":
                st.markdown(f'<div class="user-msg">{message["text"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bot-msg">{message["text"]}</div>', unsafe_allow_html=True)
                
                # Adicionar botões de feedback apenas para mensagens do bot
                if idx > 0 and st.session_state.get("user_type") != "guest":
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("👍", key=f"like_{idx}"):
                            ultima_msg_user = next(
                                (msg["text"] for msg in reversed(st.session_state.messages[:idx]) 
                                if msg["sender"] == "user"), ""
                            )
                            salvar_feedback(
                                st.session_state.user_id,
                                ultima_msg_user,
                                message["text"],
                                "like",
                                "positive"
                            )
                            st.success("Feedback enviado!")
                    with col2:
                        if st.button("👎", key=f"dislike_{idx}"):
                            ultima_msg_user = next(
                                (msg["text"] for msg in reversed(st.session_state.messages[:idx]) 
                                if msg["sender"] == "user"), ""
                            )
                            salvar_feedback(
                                st.session_state.user_id,
                                ultima_msg_user,
                                message["text"],
                                "dislike",
                                "negative"
                            )
                            st.success("Feedback enviado!")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Input de mensagem (fixo na parte inferior)
    with st.form(key="message_form", clear_on_submit=True):
        user_input = st.text_area(
            "Digite sua mensagem:", 
            key="user_input", 
            height=100, 
            value="", 
            placeholder="Digite sua mensagem e pressione Enter ou clique em Enviar",
            label_visibility="collapsed"
        )
        col1, col2 = st.columns([1, 0.2])
        with col1:
            submit_button = st.form_submit_button(label="Enviar", use_container_width=True)
        with col2:
            if st.form_submit_button("Limpar", use_container_width=True):
                user_input = ""
                st.rerun()
        
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
                user_name,
                st.session_state.messages  # Passa o histórico da conversa
            )
            
            # Adiciona resposta do bot ao histórico
            st.session_state.messages.append({"sender": "bot", "text": resposta})
            
            # Salva o chat atual no Firebase
            if "current_chat_id" in st.session_state and "user_id" in st.session_state:
                salvar_historico_chat(
                    st.session_state.user_id,
                    st.session_state.current_chat_id,
                    st.session_state.messages
                )
            
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
            "current_chat_id": str(uuid.uuid4()),
            "messages": [
                {"sender": "bot", "text": "Olá! Sou o SantChat, IA oficial do Santander. Como posso te ajudar hoje?"}
            ]
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
