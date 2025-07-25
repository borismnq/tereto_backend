from fastapi import APIRouter, HTTPException, Body
from app.firestore import db
from app.models import Match
from app.models import Player
import uuid



router = APIRouter()

@router.post("/")
async def create_match(match: Match):
    match_id = str(uuid.uuid4())
    match.id = match_id
    await db.collection("Matches").document(match_id).set(match.model_dump())
    return {"message": "Reto creado", "id": match_id}

@router.get("/")
async def list_matches():
    matches = db.collection("Matches").stream()
    return [doc.to_dict() async for doc in matches]

@router.get("/{match_id}")
async def get_match(match_id: str):
    doc = await db.collection("Matches").document(match_id).get()
    if doc.exists:
        return doc.to_dict()
    raise HTTPException(status_code=404, detail="Reto no encontrado")


@router.put("/{match_id}")
async def update_match(match_id: str, data: dict = Body(...)):
    ref = db.collection("Matches").document(match_id)
    doc = await ref.get()
    if doc.exists:
        await ref.update(data)
        return {"message": "Reto actualizado"}
    raise HTTPException(status_code=404, detail="Reto no encontrado")

@router.delete("/{match_id}")
async def delete_match(match_id: str):
    ref = db.collection("Matches").document(match_id)
    doc = await ref.get()
    if doc.exists:
        await ref.delete()
        return {"message": "Reto eliminado"}
    raise HTTPException(status_code=404, detail="Reto no encontrado")

@router.post("/{match_id}/join")
async def join_match(match_id: str, player: Player):
    doc_ref = db.collection("Matches").document(match_id)
    doc = await doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Reto no encontrado")

    datos = doc.to_dict()
    players = datos.get("players", [])
    if any(j["user_id"] == player.user_id for j in players):
        raise HTTPException(status_code=400, detail="Jugador ya unido")

    players.append(player.model_dump())
    await doc_ref.update({"players": players})
    return {"message": "Jugador unido"}

@router.post("/{match_id}/quit")
async def quit_match(match_id: str, user_id: str = Body(...)):
    doc_ref = db.collection("Matches").document(match_id)
    doc = await doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Reto no encontrado")

    data = doc.to_dict()
    players = [j for j in data.get("players", []) if j["user_id"] != user_id]
    await doc_ref.update({"players": players})
    return {"message": "Jugador removido"}

@router.post("/{match_id}/confirm")
async def confirm_player(match_id: str, user_id: str = Body(...)):
    doc_ref = db.collection("Matches").document(match_id)
    doc = await doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Reto no encontrado")

    datos = doc.to_dict()
    players = datos.get("players", [])
    if not any(j["user_id"] == user_id for j in players):
        raise HTTPException(status_code=400, detail="Usuario no está en el reto")

    for j in players:
        if j["user_id"] == user_id:
            j["confirmed"] = True

    await doc_ref.update({"players": players})

    confirmed_players = datos.get("confirmed_players", [])
    if user_id not in confirmed_players:
        confirmed_players.append(user_id)
        await doc_ref.update({"confirmed_players": confirmed_players})
    # ¿Están todos confirmados?
    all_confirmed = all(p.get("confirmed_players") for p in players) and len(players) > 0
    if all_confirmed:
        await doc_ref.update({"status": "confirmed"})
    return {"message": "Jugador confirmado"}

@router.post("/{match_id}/status")
async def update_match_status(match_id: str, status: str = Body(...)):
    doc_ref = db.collection("Matches").document(match_id)
    doc = await doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Reto no encontrado")

    await doc_ref.update({"status": status})
    return {"message": f"Estado cambiado a {status}"}
