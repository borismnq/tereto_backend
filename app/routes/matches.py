from fastapi import APIRouter, HTTPException, Body
from app.firestore import db
from app.models import Match
from app.models import Player
import uuid



router = APIRouter()

@router.post("/")
def create_match(match: Match):
    match_id = str(uuid.uuid4())
    match.id = match_id
    db.collection("Matches").document(match_id).set(match.model_dump())
    return {"message": "Reto creado", "id": match_id}

@router.get("/")
def list_matches():
    matches = db.collection("Matches").stream()
    return [doc.to_dict() for doc in matches]

@router.get("/{match_id}")
def get_match(match_id: str):
    doc = db.collection("Matches").document(match_id).get()
    if doc.exists:
        return doc.to_dict()
    raise HTTPException(status_code=404, detail="Reto no encontrado")


@router.put("/{match_id}")
def update_match(match_id: str, data: dict = Body(...)):
    ref = db.collection("Matches").document(match_id)
    if ref.get().exists:
        ref.update(data)
        return {"message": "Reto actualizado"}
    raise HTTPException(status_code=404, detail="Reto no encontrado")

@router.delete("/{match_id}")
def delete_match(match_id: str):
    ref = db.collection("Matches").document(match_id)
    if ref.get().exists:
        ref.delete()
        return {"message": "Reto eliminado"}
    raise HTTPException(status_code=404, detail="Reto no encontrado")

@router.post("/{match_id}/join")
def join_match(match_id: str, player: Player):
    doc_ref = db.collection("Matches").document(match_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Reto no encontrado")
    datos = doc.to_dict()
    players = datos.get("players", [])
    if any(j["user_id"] == player.user_id for j in players):
        raise HTTPException(status_code=400, detail="Jugador ya unido")
    players.append(player.model_dump())
    doc_ref.update({"players": players})
    return {"message": "Jugador unido"}

@router.post("/{match_id}/quit")
def quit_match(match_id: str, user_id: str = Body(...)):
    doc_ref = db.collection("Matches").document(match_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Reto no encontrado")
    data = doc.to_dict()
    players = [j for j in data.get("players", []) if j["user_id"] != user_id]
    doc_ref.update({"players": players})
    return {"message": "Jugador removido"}

@router.post("/{match_id}/confirm")
def confirm_player(match_id: str, user_id: str = Body(...)):
    doc_ref = db.collection("Matches").document(match_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Reto no encontrado")
    datos = doc.to_dict()
    players = datos.get("players", [])
    for j in players:
        if j["user_id"] == user_id:
            j["confirmed"] = True
    doc_ref.update({"players": players})
    return {"message": "Jugador confirmado"}

@router.post("/{match_id}/status")
def update_match_status(match_id: str, status: str = Body(...)):
    ref = db.collection("Matches").document(match_id)
    if not ref.get().exists:
        raise HTTPException(status_code=404, detail="Reto no encontrado")
    ref.update({"status": status})
    return {"message": f"Estado cambiado a {status}"}