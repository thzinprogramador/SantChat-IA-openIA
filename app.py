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

# Aplicar o CSS personalizado
st.markdown("""
<style>
  :root {
    --color-bg: #ffffff;
    --color-text-primary: #222222;
    --color-text-secondary: #555555;
    --color-accent: #ec0000;  /* Vermelho Santander */
    --color-accent-hover: #c50000;
    --color-button-bg: #222222;  /* Azul escuro Santander */
    --color-button-text: #ffffff;
    --color-shadow: rgba(0,0,0,0.05);
    --radius: 8px;
    --spacing: 1rem;
    --header-height: 70px;
    --max-width: 1000px;
    --color-welcome: #00a5a8;  /* Verde água Santander */
  }
  
  body {
    margin: 0;
    background: var(--color-bg);
    font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
      Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
    color: var(--color-text-secondary);
    font-size: 16px;
    line-height: 1.5;
  }
  
  .header {
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
  }
  
  .logo {
    font-weight: 800;
    font-size: 1.8rem;
    color: var(--color-accent);
    display: flex;
    align-items: center;
  }
  
  .logo img {
    height: 30px;
    margin-right: 10px;
  }
  
  .login-btn {
    margin-left: auto;
    background: var(--color-accent);
    color: white;
    border: none;
    border-radius: var(--radius);
    padding: 8px 20px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .login-btn:hover {
    background: var(--color-accent-hover);
    transform: translateY(-1px);
  }
  
  .main-container {
    max-width: var(--max-width);
    margin: 0 auto;
    padding: 20px;
    padding-top: calc(var(--header-height) + 20px);
  }
  
  .welcome-title {
    color: var(--color-welcome);
    font-size: 2.2rem;
    margin-bottom: 10px;
  }
  
  .welcome-subtitle {
    color: var(--color-text-secondary);
    font-size: 1.1rem;
    margin-bottom: 30px;
  }
  
  .chat-container {
    background: #f9f9f9;
    border-radius: var(--radius);
    padding: 20px;
    margin-bottom: 20px;
  }
  
  .user-msg {
    background: #e6f2ff;
    color: var(--color-text-primary);
    padding: 12px 16px;
    border-radius: var(--radius);
    margin: 10px 0 10px auto;
    max-width: 80%;
    box-shadow: 0 1px 3px var(--color-shadow);
  }
  
  .bot-msg {
    background: white;
    color: var(--color-text-primary);
    padding: 12px 16px;
    border-radius: var(--radius);
    margin: 10px auto 10px 0;
    max-width: 80%;
    box-shadow: 0 1px 3px var(--color-shadow);
    border-left: 4px solid var(--color-accent);
  }
  
  .feedback-buttons {
    display: flex;
    gap: 8px;
    margin-top: 10px;
  }
  
  .feedback-btn {
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
  }
  
  .feedback-btn:hover {
    background: #e0e0e0;
    transform: scale(1.1);
  }
  
  .sidebar {
    background: white;
    padding: 20px;
    border-right: 1px solid #eee;
  }
  
  @media (max-width: 768px) {
    .header {
      padding: 0 15px;
    }
    
    .logo {
      font-size: 1.5rem;
    }
    
    .login-btn {
      padding: 6px 15px;
      font-size: 0.9rem;
    }
  }
</style>
""", unsafe_allow_html=True)

# --- Header Fixo ---
header = st.container()
with header:
    st.markdown("""
    <div class="header">
        <div class="logo">
            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/Santander_Bank_logo.svg/1200px-Santander_Bank_logo.svg.png" alt="Santander Logo">
            SantChat
        </div>
        <button class="login-btn" onclick="window.loginClicked()">Entrar</button>
    </div>
    <div style="height: 80px;"></div>
    """, unsafe_allow_html=True)

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

def criar_usuario(email, senha):
    try:
        nome_usuario = email.split("@")[0].lower()
        ref = db.reference(f"usuarios/{nome_usuario}")
        
        if ref.get():
            return False, "Usuário já existe"
            
        ref.set({
            "email": email,
            "senha": senha,
            "nivel": 0,  # Nível padrão 0 (usuário comum)
            "criado_em": datetime.now().isoformat()
        })
        return True, "Usuário criado com sucesso"
    except Exception as e:
        return False, f"Erro ao criar usuário: {str(e)}"

def autenticar_usuario(email, senha):
    try:
        nome_usuario = email.split("@")[0].lower()
        ref = db.reference(f"usuarios/{nome_usuario}")
        usuario = ref.get()
        
        if not usuario:
            return False, None, "Usuário não encontrado"
            
        if usuario.get("senha") != senha:
            return False, None, "Senha incorreta"
            
        return True, usuario, "Login bem-sucedido"
    except Exception as e:
        return False, None, f"Erro na autenticação: {str(e)}"

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
    # Inicialização do estado da sessão
    if "user_type" not in st.session_state:
        st.session_state.update({
            "user_type": "guest",
            "user_id": f"guest-{uuid.uuid4().hex[:6]}",
            "show_login": False,
            "memoria": carregar_memoria(),
            "historico": []
        })

    # JavaScript para o botão de login
    st.markdown("""
    <script>
    window.loginClicked = function() {
        window.parent.postMessage({
            type: 'LOGIN_CLICKED'
        }, '*');
    }
    
    window.addEventListener('message', function(event) {
        if (event.data.type === 'LOGIN_CLICKED') {
            window.parent.document.dispatchEvent(new Event('LOGIN_CLICKED'));
        }
    });
    </script>
    """, unsafe_allow_html=True)

    # Verificar clique no botão de login
    if st.session_state.get("login_clicked"):
        st.session_state.show_login = True
        st.session_state.login_clicked = False
        st.rerun()

    # Menu lateral (login)
    with st.sidebar:
        st.markdown("""
        <style>
            .sidebar-content {
                padding-top: 20px;
            }
            .sidebar-title {
                color: var(--color-accent);
                font-size: 1.5rem;
                margin-bottom: 20px;
            }
        </style>
        <div class="sidebar-content">
            <div class="sidebar-title">Menu</div>
        """, unsafe_allow_html=True)
        
        if st.session_state.get("show_login"):
            st.subheader("Login")
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            
            if st.button("Entrar", key="login_btn"):
                # Lógica de autenticação aqui
                st.session_state.show_login = False
                st.success("Login realizado com sucesso!")
                st.rerun()
            
            st.divider()
            st.subheader("Criar conta")
            new_email = st.text_input("Novo e-mail")
            new_pass = st.text_input("Nova senha", type="password")
            if st.button("Registrar"):
                # Lógica de criação de conta aqui
                st.success("Conta criada com sucesso!")
        
        menu_itens = ["Chat"]
        if st.session_state.get("user_type") == "dev":
            menu_itens += ["Memória IA", "Feedbacks"]
        
        choice = st.radio("Navegação", menu_itens)
        
        if st.session_state.get("user_type") != "guest" and st.button("Logout"):
            st.session_state.clear()
            st.rerun()

    # Conteúdo principal
    st.markdown("""
    <div class="main-container">
        <h1 class="welcome-title">Bem-vindo ao SantChat</h1>
        <p class="welcome-subtitle">Seu chat inteligente, com histórico, feedback e memória para usuários dev.</p>
    """, unsafe_allow_html=True)

    if choice == "Chat":
        # Lógica do chat aqui
        st.markdown("""
        <div class="chat-container">
            <div class="bot-msg">
                Sou o SantChat, IA oficial do Santander. Estou aqui pra ajudar com qualquer dúvida ou solicitação sobre nossos produtos e serviços.
                <br><br>
                Em que posso te ajudar hoje?
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
