import streamlit as st
import os
import json
import uuid
import openai
import requests
import firebase_admin
import streamlit.components.v1 as components
from firebase_admin import credentials, db
from datetime import datetime, timedelta  
from markdown import markdown

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
            font-size: 24px;
            color: #1976D2;
            text-decoration: none !important;
            pointer-events: none;
            cursor: default;
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
        /* Estilos para a interface de treinamento */
        .st-correction-card {{
        border: 1px solid #555 !important;
        border-radius: 8px !important;
        padding: 15px !important;
        margin-bottom: 15px !important;
        background: #2a2a2a !important;
        }}

        .st-correction-question {{
        font-weight: bold !important;
        color: #4CAF50 !important;
        margin-bottom: 5px !important;
        }}

        .st-correction-answer {{
        background: #333333 !important;
        padding: 10px !important;
        border-radius: 5px !important;
        margin: 10px 0 !important;
        }}

        .st-correction-buttons {{
        display: flex !important;
        justify-content: space-between !important;
        margin-top: 10px !important;
        }}

        .st-correction-form {{
        margin-top: 15px !important;
        padding: 10px !important;
        background: #333333 !important;
        border-radius: 5px !important;
        }}
    </style>
    """, unsafe_allow_html=True)

# --- Firebase Initialization ---

def initialize_firebase():
    if not firebase_admin._apps:
        raw_key = dict(st.secrets["FIREBASE_KEY"])

        # Corrigir a quebra de linha da chave privada
        raw_key["private_key"] = raw_key["private_key"].replace("\\n", "\n")

        cred = credentials.Certificate(raw_key)
        firebase_admin.initialize_app(cred, {
            "databaseURL": st.secrets["FIREBASE_KEY_DB_URL"]
        })


# --- Novas funções para o sistema RAG-like ---
def salvar_resposta_revisada(revisor_id, pergunta, resposta_original, resposta_revisada, categoria):
    try:
        ref = db.reference(f"respostas_revisadas/{revisor_id}")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        
        ref.child(timestamp).set({
            "pergunta": pergunta,
            "resposta_original": resposta_original,
            "resposta_revisada": resposta_revisada,
            "categoria": categoria,
            "revisor": st.session_state.user_data.get("nome_usuario", "admin"),
            "timestamp": datetime.now().isoformat(),
            "status": "revisado"
        })
        return True
    except Exception as e:
        st.error(f"❌ Erro ao salvar resposta revisada: {str(e)}")
        return False

def carregar_respostas_revisadas():
    try:
        ref = db.reference("respostas_revisadas")
        return ref.get() or {}
    except Exception as e:
        st.error(f"Erro ao carregar respostas revisadas: {str(e)}")
        return {}

def buscar_resposta_revisada(pergunta):
    try:
        respostas = carregar_respostas_revisadas()
        for user_id, user_respostas in respostas.items():
            for ts, resposta in user_respostas.items():
                if resposta['status'] == 'revisado' and similaridade_pergunta(pergunta, resposta['pergunta']) > 0.7:
                    return resposta['resposta_revisada']
        return None
    except Exception as e:
        st.error(f"Erro ao buscar resposta revisada: {str(e)}")
        return None

def similaridade_pergunta(pergunta1, pergunta2):
    """Função simplificada de similaridade - pode ser melhorada depois"""
    palavras1 = set(pergunta1.lower().split())
    palavras2 = set(pergunta2.lower().split())
    intersecao = palavras1.intersection(palavras2)
    return len(intersecao) / max(len(palavras1), len(palavras2), 1)

def carregar_interacoes():
    """Carrega todas as interações usuário-IA do Firebase"""
    try:
        # Referência para os dados no Firebase
        ref = db.reference("logs/usuarios")
        todos_usuarios = ref.get() or {}  # Retorna dict vazio se não existir
        
        todas_interacoes = []
        
        # Percorre todos os usuários
        for user_id, user_data in todos_usuarios.items():
            # Pega todos os chats do usuário
            chats = user_data.get("chats", {})
            
            # Percorre cada chat
            for chat_id, chat_data in chats.items():
                # Pega todas as mensagens do chat
                mensagens = chat_data.get("mensagens", [])
                
                # Verifica se há mensagens suficientes para formar pares
                if len(mensagens) < 2:
                    continue
                
                # Percorre as mensagens em pares (pergunta-resposta)
                for i in range(len(mensagens)-1):
                    msg_user = mensagens[i]
                    msg_bot = mensagens[i+1]
                    
                    # Verifica se é um par válido (usuário -> bot)
                    if msg_user["sender"] == "user" and msg_bot["sender"] == "bot":
                        # Adiciona à lista de interações
                        todas_interacoes.append({
                            "user_id": user_id,
                            "chat_id": chat_id,
                            "pergunta": msg_user.get("text", ""),
                            "resposta": msg_bot.get("text", ""),
                            "timestamp": chat_data.get("ultima_atualizacao", "sem data"),
                            "metadata": {
                                "modelo": msg_bot.get("model", "desconhecido"),
                                "feedback": msg_bot.get("feedback", None)
                            }
                        })
        
        # Ordena por timestamp (mais recente primeiro)
        return sorted(
            todas_interacoes,
            key=lambda x: x.get("timestamp", "1970-01-01"),
            reverse=True
        )
        
    except Exception as e:
        st.error(f"🔥 Erro ao carregar interações: {str(e)}")
        return []


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
        
        primeira_msg = next((msg["text"] for msg in historico if msg["sender"] == "user"), "Chat sem título")[:50]
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
        user_id = nome_usuario.lower()
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
        # Procurar todos os usuários e comparar e-mail e senha
        ref = db.reference("usuarios")
        usuarios = ref.get()

        if not usuarios:
            return False, None, "Nenhum usuário encontrado no banco de dados."

        for user_id, dados in usuarios.items():
            if dados.get("email") == email:
                if dados.get("senha") == senha:
                    return True, dados, "Login bem-sucedido"
                else:
                    return False, None, "Senha incorreta"

        return False, None, "Usuário não encontrado"
    except Exception as e:
        return False, None, f"Erro na autenticação: {str(e)}"


def processar_comando_dev(comando, user_data):
    if int(user_data.get("nivel", 0)) != -8:  # Nível de dev
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
    # Verifica se há uma resposta revisada para essa pergunta
    resposta_revisada = buscar_resposta_revisada(prompt)
    if resposta_revisada:
        return resposta_revisada
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
    
    nome_usuario = user_name or "usuário"

    system_prompt = f"""
    Hoje é {agora}. Você é o SantChat, IA oficial do Santander.

    Responda com clareza e de forma direta.
    Mantenha o contexto da conversa atual.
    Não invente informações sobre datas ou produtos.
    Se o usuário perguntar qual é o nome dele, diga: "Seu nome é {nome_usuario}".

    ⚠️ Importante: Quando quiser mostrar algo em **negrito**, use diretamente `**texto**`, sem colocar entre crases ou aspas.
    Evite usar o símbolo de crase (`) ao redor de exemplos de Markdown.
    Exemplo correto: Para negrito, use **assim**.
    Exemplo errado: Para negrito, use `**assim**`.

    Nunca explique Markdown como código, apenas mostre já formatado.
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
    st.markdown(f"""
    <div class="header">
        <div class="logo">
            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/Santander_Bank_logo.svg/1200px-Santander_Bank_logo.svg.png" alt="Santander Logo">
            <span style="color: {COR_PRIMARIA}">SantChat</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_login_sidebar():
    with st.sidebar:
        # Inicializa o modo de autenticação se ainda não estiver definido
        if "auth_mode" not in st.session_state:
            st.session_state.auth_mode = "login"
        if "mostrar_registro" not in st.session_state:
            st.session_state.mostrar_registro = False
        if "show_login" not in st.session_state:
            st.session_state.show_login = False
        if "show_register_form" not in st.session_state:
            st.session_state.show_register_form = False

        st.title("SantChat")

        if st.session_state.get("user_type") == "guest":
            if st.session_state.auth_mode == "login":
                st.subheader("Login")
                email = st.text_input("E-mail")
                senha = st.text_input("Senha", type="password")

                if st.button("Entrar", key="login_btn", use_container_width=True):
                    success, user, message = autenticar_usuario(email, senha)
                    if success:
                        st.session_state.update({
                            "user_type": "user",
                            "user_id": user["nome_usuario"].lower(),
                            "user_data": user,
                            "auth_mode": "login",
                            "messages": [{
                                "sender": "bot",
                                "text": "Olá! Sou o SantChat, IA oficial do Santander. Estou agora com você para o que precisar, me conta como posso te apoiar hoje?"
                            }],
                            "current_chat_id": str(uuid.uuid4())
                        })
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

                if st.button("Não tem conta? Criar uma", key="show_register_btn", use_container_width=True):
                    st.session_state.auth_mode = "register"
                    st.rerun()

            elif st.session_state.auth_mode == "register":
                st.subheader("Criar conta")
                new_email = st.text_input("Novo e-mail")
                new_pass = st.text_input("Nova senha", type="password")
                new_username = st.text_input("Nome de usuário")

                if st.button("Registrar", key="register_btn", use_container_width=True):
                    success, message = criar_usuario(new_email, new_pass, new_username)
                    if success:
                        st.success("Conta criada com sucesso!")
                        st.session_state.auth_mode = "login"
                        st.rerun()
                    else:
                        st.error(message)

                if st.button("Já tem conta? Logar", key="show_login_btn", use_container_width=True):
                    st.session_state.auth_mode = "login"
                    st.rerun()

        else:
            if st.button("+ Novo chat", key="new_chat_btn", use_container_width=True):
                if (
                    "current_chat_id" in st.session_state
                    and any(msg["sender"] == "user" for msg in st.session_state.get("messages", []))
                ):
                    salvar_historico_chat(
                        st.session_state.user_id,
                        st.session_state.current_chat_id,
                        st.session_state.messages
                    )

                new_chat_id = str(uuid.uuid4())
                st.session_state.current_chat_id = new_chat_id
                st.session_state.messages = [{
                    "sender": "bot",
                    "text": "Olá! Sou o SantChat, IA oficial do Santander. Estou agora com você para o que precisar, me conta como posso te apoiar hoje?"
                }]
                st.rerun()

            st.markdown('<div class="chat-history">', unsafe_allow_html=True)
            st.markdown('<div class="sidebar-title">Histórico de Chats</div>', unsafe_allow_html=True)

            chats = carregar_historico_chats(st.session_state.user_id)
            if chats:
                # Ordenar os chats por data (mais recentes primeiro)
                chats_ordenados = sorted(
                    chats.items(),
                    key=lambda item: item[1].get("ultima_atualizacao", ""),
                    reverse=True
                )

                for chat_id, chat_data in chats_ordenados:
                    if st.button(
                        chat_data.get("titulo", "Chat sem título"),
                        key=f"chat_{chat_id}",
                        help=f"Última atualização: {chat_data.get('ultima_atualizacao', '')}",
                        use_container_width=True
                    ):
                        st.session_state.current_chat_id = chat_id
                        st.session_state.messages = chat_data.get("mensagens", [])
                        st.rerun()
            else:
                st.markdown('<div style="color: #999; font-size: 0.9rem;">Nenhum chat anterior</div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

            if st.session_state.get("user_data"):
                user_name = st.session_state.user_data.get("nome_usuario", "Usuário")
                st.markdown(f'<div class="user-greeting">👋 Olá, {user_name}!</div>', unsafe_allow_html=True)

        st.markdown("""
        <div class="sidebar-content">
            <div class="sidebar-title">Menu</div>
        """, unsafe_allow_html=True)

        menu_itens = ["Chat"]
        if int(st.session_state.get("user_data", {}).get("nivel", 0)) == -8:
            menu_itens += ["Memória IA", "Feedbacks", "Treinar IA"]    # Adicione privilegios para dev

        choice = st.radio("Navegação", menu_itens, label_visibility="collapsed")

        if st.session_state.get("user_type") != "guest" and st.button("Logout", use_container_width=True):
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
    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
    st.subheader("Memória Global da IA")
    memoria = carregar_memoria()
    
    if st.button("Atualizar Memória"):
        memoria = carregar_memoria()
        st.rerun()
    
    if memoria:
        for idx, item in enumerate(memoria):
            st.markdown(f"**{idx + 1}.** {item}")
            st.divider()
    else:
        st.info("Nenhuma informação na memória ainda.")

    
    st.subheader("Adicionar à Memória")
    nova_info = st.text_area("Nova informação para a memória")
    if st.button("Salvar na Memória"):
        memoria.append(nova_info)
        if salvar_memoria(memoria):
            st.success("Informação adicionada com sucesso!")
        else:
            st.error("Erro ao salvar na memória")

def render_feedbacks():
    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
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

def render_treinar_ia():
    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
    st.subheader("📚 Treinar IA - Revisão de Respostas")

    # Carrega as interações
    interacoes = carregar_interacoes()
    
    if not interacoes:
        st.warning("Nenhuma interação encontrada para revisão")
        return

    # Filtros e configurações
    st.sidebar.subheader("Filtros")
    filtro_usuario = st.sidebar.text_input("Filtrar por usuário")
    filtro_data = st.sidebar.date_input("Filtrar por data")
    items_por_pagina = st.sidebar.selectbox("Itens por página", [10, 25, 50], index=0)

    # Aplica filtros
    if filtro_usuario:
        interacoes = [i for i in interacoes if filtro_usuario.lower() in i['user'].lower()]
    
    if filtro_data:
        interacoes = [i for i in interacoes if datetime.strptime(i['timestamp'], "%Y-%m-%dT%H:%M:%S").date() == filtro_data]

    # Paginação
    total_paginas = max(1, (len(interacoes) + items_por_pagina - 1) // items_por_pagina)
    pagina = st.number_input("Página", 1, total_paginas, 1)
    inicio = (pagina - 1) * items_por_pagina
    fim = pagina * items_por_pagina

    # Mostra as interações filtradas e paginadas
    for idx, interacao in enumerate(interacoes[inicio:fim], start=inicio):
        with st.expander(f"Interação {idx+1} - {interacao['user']} ({interacao['timestamp']})"):
            # Card de interação
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                **❓ Pergunta:**  
                {interacao['pergunta']}
                
                **🤖 Resposta Original:**  
                {interacao['resposta']}
                """)
            
            with col2:
                # Botões de ação
                if st.button("✅ Aprovar", key=f"aprovar_{idx}"):
                    if salvar_resposta_revisada(
                        st.session_state.user_id,
                        interacao['pergunta'],
                        interacao['resposta'],
                        interacao['resposta'],  # Mantém a mesma resposta
                        "aprovado"
                    ):
                        st.success("Aprovada! Esta resposta será usada como referência.")
                        st.rerun()
                
                if st.button("✏️ Corrigir", key=f"corrigir_{idx}"):
                    st.session_state[f'editando_{idx}'] = True
            
            # Formulário de edição (aparece apenas quando clicar em Corrigir)
            if st.session_state.get(f'editando_{idx}'):
                with st.form(key=f"form_correcao_{idx}"):
                    nova_resposta = st.text_area(
                        "Resposta corrigida:",
                        value=interacao['resposta'],
                        key=f"nova_resposta_{idx}"
                    )
                    
                    categoria = st.selectbox(
                        "Categoria:",
                        ["Geral", "Produtos", "Contas", "Investimentos", "Cartões"],
                        key=f"categoria_{idx}"
                    )
                    
                    if st.form_submit_button("💾 Salvar Correção"):
                        if salvar_resposta_revisada(
                            st.session_state.user_id,
                            interacao['pergunta'],
                            interacao['resposta'],
                            nova_resposta,
                            categoria
                        ):
                            st.success("Correção salva com sucesso!")
                            st.session_state.pop(f'editando_{idx}', None)
                            st.rerun()
                        else:
                            st.error("Erro ao salvar correção")

    # Estatísticas
    st.markdown(f"*Mostrando {len(interacoes[inicio:fim])} de {len(interacoes)} interações*")


def compensar_header_fixo():
    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)


def render_chat_interface():
    st.markdown(f"""
    <div class="main-container">
        <h1 class="welcome-title">SantChat</h1>
        <h3 class="welcome-subtitle">Sou uma IA criada para ajudar você em seus atendimentos</h3>
    """, unsafe_allow_html=True)

    # Container do chat
    chat_container = st.container()
    with chat_container:
        st.markdown('<div class="chat-container" id="chat-messages">', unsafe_allow_html=True)

        # Mostrar histórico de mensagens (primeira vez)
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {
                    "sender": "bot",
                    "text": "Olá! Sou o SantChat, IA oficial do Santander. Estou agora com você para o que precisar, me conta como posso te apoiar hoje?"
                }
            ]

        # Exibir todas as mensagens
        for idx, message in enumerate(st.session_state.messages):
            if message["sender"] == "user":
                st.markdown(f'<div class="user-msg">{message["text"]}</div>', unsafe_allow_html=True)
            else:
                raw_text = message.get("text", "")
                formatted_text = markdown(raw_text)
                st.markdown(f'<div class="bot-msg">{formatted_text}</div>', unsafe_allow_html=True)

                # Botões de feedback
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

    # Input do usuário
    with st.form(key="message_form", clear_on_submit=True):
        user_input = st.text_area(
            "Digite sua mensagem:",
            key="user_input",
            placeholder="Digite sua mensagem...",
            label_visibility="collapsed"
        )
        col1, col2 = st.columns([1, 0.2])
        with col1:
            submit_button = st.form_submit_button(label="Enviar", use_container_width=True)
        with col2:
            if st.form_submit_button("Limpar", use_container_width=True):
                user_input = ""
                st.rerun()

        # Quando o usuário envia uma mensagem
        if submit_button and user_input:
            user_data = st.session_state.get("user_data", {})

            # Verifica comando de dev
            success, msg = processar_comando_dev(user_input, user_data)
            if success is not None:
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
                st.rerun()

            # Cria novo chat ID somente após envio de mensagem
            if "current_chat_id" not in st.session_state:
                new_chat_id = str(uuid.uuid4())
                st.session_state.current_chat_id = new_chat_id

            # Adiciona mensagem do usuário
            st.session_state.messages.append({"sender": "user", "text": user_input})

            # Gera resposta da IA
            user_name = user_data.get("nome_usuario")
            resposta = gerar_resposta(
                st.session_state.get("memoria", []),
                user_input,
                user_name,
                st.session_state.messages
            )

            # Adiciona resposta do bot
            st.session_state.messages.append({"sender": "bot", "text": resposta})

            # Salva o chat após envio
            if "current_chat_id" in st.session_state and "user_id" in st.session_state:
                salvar_historico_chat(
                    st.session_state.user_id,
                    st.session_state.current_chat_id,
                    st.session_state.messages
                )

            st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)


        
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

# --- Função para aplicar estilo dinâmico ---
def aplicar_estilo_customizado():
    modo_tema = st.get_option("theme.base")

    if modo_tema == "dark":
        # Estilo para modo escuro
        st.markdown("""
            <style>
                .elemento-seletor {
                    color: white;
                    background-color: #1e1e1e;
                }
            </style>
        """, unsafe_allow_html=True)
    else:
        # Estilo para modo claro
        st.markdown("""
            <style>
                .elemento-seletor {
                    color: black;
                    background-color: #ffffff;
                }
            </style>
        """, unsafe_allow_html=True)

# --- Função Principal ---
def main():
    # Carregar configurações
    load_css()
    initialize_firebase()
    aplicar_estilo_customizado()

    
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
                {"sender": "bot", "text": "Olá! Sou o SantChat, IA oficial do Santander. Estou agora com você para o que precisar, me conta como posso te apoiar hoje?"}
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
    elif choice == "Treinar IA" and st.session_state.get("user_data", {}).get("nivel") == -8:
        render_treinar_ia()
        
        aplicar_estilo_customizado()

        # Mostra aviso se for visitante
        if st.session_state.get("user_type") == "guest":
            st.info("👤 Você está como visitante — suas conversas não serão salvas.", icon="⚠️")




if __name__ == "__main__":
    main()
