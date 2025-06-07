import firebase_admin
from firebase_admin import credentials, db

def iniciar_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate("firebase_credentials.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': "https://santchat-ia-default-rtdb.firebaseio.com/"  # 🔁 coloque sua URL aqui!
        })

def salvar_memoria_firebase(memoria):
    iniciar_firebase()
    ref = db.reference("/memoria")
    ref.set(memoria)

def carregar_memoria_firebase():
    iniciar_firebase()
    ref = db.reference("/memoria")
    dados = ref.get()
    return dados if dados else []
