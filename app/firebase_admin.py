# app/firebase_admin.py

import firebase_admin
from firebase_admin import credentials, auth


# Inicializar Firebase Admin solo una vez
if not firebase_admin._apps:
    cred = credentials.Certificate("app/credentials.json")  # asegúrate de tener este archivo
    firebase_admin.initialize_app(cred)

def verify_token(id_token: str):
    """
    Verifica un Firebase ID Token y devuelve la información del usuario.
    Lanza un error si es inválido o expirado.
    """
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token  # contiene: uid, email, name, etc.
    except Exception as e:
        raise ValueError(f"Token inválido: {e}")
