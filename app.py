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
    --color-text-primary: #111827;
    --color-text-secondary: #6b7280;
    --color-accent: #111827;
    --color-accent-hover: #374151;
    --color-button-bg: #111827;
    --color-button-text: #ffffff;
    --color-shadow: rgba(0,0,0,0.05);
    --radius: 0.75rem;
    --spacing: 1rem;
    --header-height: 64px;
    --max-width: 1200px;
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
  
  .logo {
    font-weight: 800;
    font-size: 1.75rem;
    color: var(--color-text-primary);
    user-select: none;
  }
  
  button#btn-entrar {
    background: var(--color-button-bg);
    color: var(--color-button-text);
    border: none;
    border-radius: var(--radius);
    padding: 0.5rem 1.25rem;
    font-weight: 700;
    cursor: pointer;
    transition: background-color 0.25s ease;
  }
  
  button#btn-entrar:hover,
  button#btn-entrar:focus {
    background-color: var(--color-accent-hover);
    outline: none;
  }
  
  /* Estilos para as mensagens do chat */
  .msg-user {
    background: #f3f4f6;
    color: var(--color-text-primary);
    padding: 10px 15px;
    border-radius: var(--radius);
    margin: 8px 0 8px auto;
    max-width: 80%;
    box-shadow: 0 1px 3px var(--color-shadow);
  }
  
  .msg-assistant {
    background: var(--color-accent);
    color: white;
    padding: 10px 15px;
    border-radius: var(--radius);
    margin: 8px auto 8px 0;
    max-width: 80%;
    box-shadow: 0 1px 3px var(--color-shadow);
  }
  
  /* Estilo para os botões de feedback */
  .feedback-buttons {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.5rem;
    margin-bottom: 1rem;
  }
  
  /* Container principal */
  .main-container {
    max-width: var(--max-width);
    margin: 0 auto;
    padding: var(--spacing);
    padding-top: calc(var(--header-height) + 1rem);
  }
  
  /* Header fixo */
  .stApp header {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: var(--header-height);
    background: var(--color-bg);
    box-shadow: 0 2px 8px var(--color-shadow);
    display: flex;
    align-items: center;
    padding: 0 var(--spacing);
    z-index: 1000;
  }
  
  /* Ajustes para o menu lateral */
  .stSidebar {
    padding-top: var(--header-height);
  }
  
  /* Esconder elementos padrão do Streamlit */
  .stApp header:first-child {
    display: none;
  }
  
  /* Menu responsivo */
  @media (max-width: 900px) {
    .stSidebar {
      width: 240px;
      transform: translateX(-100%);
      transition: transform 0.3s ease;
      position: fixed;
      z-index: 1100;
      background: var(--color-bg);
      height: 100vh;
      top: var(--header-height);
    }
    
    .stSidebar.open {
      transform: translateX(0);
    }
    
    .menu-toggle {
      display: flex !important;
      flex-direction: column;
      justify-content: center;
      width: 28px;
      height: 22px;
      cursor: pointer;
      margin-right: 1rem;
    }
    
    .menu-toggle span {
      display: block;
      height: 3px;
      background: var(--color-text-primary);
      border-radius: 2px;
      margin-bottom: 5px;
      transition: 0.3s;
    }
    
    .menu-toggle span:last-child {
      margin-bottom: 0;
    }
  }
</style>
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
    except:
        return []

def salvar_memoria(mem):
    db.reference("memoria_global").set(mem)

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
    # Cabeçalho personalizado
    st.markdown("""
    <div class="stApp">
        <header>
            <div style="display:flex; align-items:center;">
                <button class="menu-toggle" id="menuToggle" style="display:none;">
                    <span></span>
                    <span></span>
                    <span></span>
                </button>
                <div class="logo">SantChat</div>
            </div>
            <div style="margin-left:auto;">
                <button id="btn-entrar" onclick="handleLogin()">Entrar</button>
            </div>
        </header>
    </div>
    
    <script>
    function handleLogin() {
        // Lógica de login pode ser implementada aqui
        console.log("Botão de login clicado");
    }
    
    // Menu toggle para mobile
    document.addEventListener('DOMContentLoaded', function() {
        const menuToggle = document.getElementById('menuToggle');
        const sidebar = document.querySelector('.stSidebar');
        
        if (window.innerWidth <= 900) {
            menuToggle.style.display = 'flex';
            
            menuToggle.addEventListener('click', function() {
                sidebar.classList.toggle('open');
            });
        }
        
        window.addEventListener('resize', function() {
            if (window.innerWidth <= 900) {
                menuToggle.style.display = 'flex';
            } else {
                menuToggle.style.display = 'none';
                sidebar.classList.remove('open');
            }
        });
    });
    </script>
    """, unsafe_allow_html=True)

    # Inicialização do estado da sessão
    if "user_type" not in st.session_state:
        st.session_state["user_type"] = "guest"
        st.session_state["user_id"] = f"guest-{uuid.uuid4().hex[:6]}"
        st.session_state["show_login"] = False
        st.session_state["memoria"] = carregar_memoria()
        st.session_state["historico"] = []
        st.session_state["ultima_interacao"] = datetime.now()

    user_id = st.session_state["user_id"]
    is_dev = st.session_state.get("user_type") == "dev"

    # Menu lateral
    with st.sidebar:
        if st.session_state.get("show_login"):
            st.subheader("Login")
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            if st.button("Entrar"):
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
        
        menu_itens = ["Chat"]
        if is_dev:
            menu_itens += ["Memória IA", "Feedbacks"]
        
        choice = st.radio("Menu", menu_itens)
        
        if st.session_state["user_type"] != "guest" and st.button("Logout"):
            st.session_state.clear()
            st.rerun()

    # Conteúdo principal
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    if choice == "Chat":
        st.markdown("<h1 style='font-weight: 700; font-size: 2.5rem; color: var(--color-text-primary); margin-bottom: 0.5rem;'>Bem-vindo ao SantChat</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: var(--color-text-secondary); font-size: 1.125rem; max-width: 600px;'>Seu chat inteligente, com histórico, feedback e memória para usuários dev.</p>", unsafe_allow_html=True)
        
        # Exibir histórico de mensagens
        for i, msg in enumerate(st.session_state.historico):
            tipo = "msg-user" if msg["origem"] == "user" else "msg-assistant"
            st.markdown(f"<div class='{tipo}'>{msg['texto']}</div>", unsafe_allow_html=True)
            
            # Botões de feedback para respostas da IA
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
                
                # Campo de feedback expandido
                if st.session_state.get(f"fb_{i}"):
                    feedback = st.text_input("Seu feedback:", key=f"fb_text_{i}")
                    if st.button("Enviar feedback", key=f"send_fb_{i}"):
                        pergunta = st.session_state.historico[i-1]["texto"] if i > 0 else ""
                        salvar_feedback(user_id, pergunta, msg["texto"], feedback)
                        st.success("✅ Feedback enviado com sucesso!")
                        st.session_state[f"fb_{i}"] = False
        
        # Entrada do usuário
        entrada = st.chat_input("Digite sua mensagem")
        if entrada:
            st.session_state.ultima_interacao = datetime.now()
            
            # Comando especial para desenvolvedores
            if entrada.lower().startswith("/sntevksi") and is_dev:
                conteudo = entrada[len("/sntevksi"):].strip()
                if conteudo:
                    st.session_state.memoria.append(conteudo)
                    salvar_memoria(st.session_state.memoria)
                    st.success("🧠 Conhecimento adicionado à memória global!")
                else:
                    st.warning("⚠️ Digite algo após /sntevksi para ensinar à IA.")
            else:
                st.session_state.historico.append({"origem": "user", "texto": entrada})
                resposta = gerar_resposta(st.session_state.memoria, entrada)
                st.session_state.historico.append({"origem": "assistant", "texto": resposta})
                st.rerun()
    
    elif choice == "Memória IA" and is_dev:
        st.header("🧠 Memória Global da IA")
        memoria = carregar_memoria()
        st.write(memoria)
        
        # Opção para adicionar nova memória
        nova_memoria = st.text_area("Adicionar novo conhecimento à memória global")
        if st.button("Salvar na memória"):
            if nova_memoria:
                st.session_state.memoria.append(nova_memoria)
                salvar_memoria(st.session_state.memoria)
                st.success("Conhecimento adicionado com sucesso!")
            else:
                st.warning("Digite algo para adicionar à memória.")
    
    elif choice == "Feedbacks" and is_dev:
        st.header("📊 Feedbacks Recebidos")
        data = db.reference(f"logs/feedbacks").get() or {}
        
        for user_id, feedbacks in data.items():
            with st.expander(f"Usuário: {user_id}"):
                for timestamp, feedback in feedbacks.items():
                    try:
                        fb_data = json.loads(feedback)
                        st.write(f"**Pergunta:** {fb_data.get('pergunta', '')}")
                        st.write(f"**Resposta:** {fb_data.get('resposta', '')}")
                        st.write(f"**Feedback:** {fb_data.get('feedback', '')}")
                        st.write(f"*{timestamp}*")
                        st.divider()
                    except:
                        st.write(f"Feedback inválido: {feedback}")
    
    st.markdown('</div>', unsafe_allow_html=True)  # Fechar main-container

if __name__ == "__main__":
    main()
