
# backend/routes/auth.py
from fastapi import APIRouter, Request, HTTPException
from firebase_admin import auth
from app.firestore import db
from app.models import UserStats
from google.cloud.firestore_v1 import SERVER_TIMESTAMP

router = APIRouter()

@router.post("/login")
async def login_con_token(request: Request):
    body = await request.json()
    id_token = body.get("idToken")
    

    if not id_token:
        raise HTTPException(status_code=400, detail="idToken es requerido")

    try:
        decoded_token = auth.verify_id_token(id_token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")
    uid = decoded_token["uid"]
    email = decoded_token.get("email")
    name = decoded_token.get("name")
    picture = decoded_token.get("picture")

    try:
        # Referencia al documento del usuario
        user_ref = db.collection("Users").document(uid)
        user_doc = await user_ref.get()

        if not user_doc.exists:
            user_dict = {
                "id": uid,
                "email": email,
                "name": name,
                "username": None,
                "photo_url": picture,
                "created_at": SERVER_TIMESTAMP,
            }
            await user_ref.set(user_dict)
            print(f"🆕 Usuario {email} autenticado")
        else:
            print(f"✅ Usuario {email} ya existe")
        user_dict = user_doc.to_dict()
        print(f"{user_dict=}")
        return {
            "id": user_dict.get("id") or uid,
            "email": user_dict["email"],
            "name": user_dict["name"],
            "username": user_dict.get("username"),
            "photo_url": user_dict["photo_url"] 
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sincronizando usuario: {str(e)}")
