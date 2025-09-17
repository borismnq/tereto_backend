from fastapi import APIRouter, HTTPException, Body
from app.firestore import db
from app.models import Match
from app.models import Player
import uuid
from pydantic import BaseModel



router = APIRouter()

@router.post("/")
async def create_match(match: Match):
    match_id = str(uuid.uuid4())
    match.id = match_id
    
    match.players.append(Player.model_construct(
        user_id=match.creator_id,
        name=match.creator_name,
        position=match.creator_position,
        team="home",
        confirmed=True
    ))
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
    modo = datos.get("mode", "5vs5")
    limite_por_modo = {
        "5vs5": 10,
        "6vs6": 12,
        "7vs7": 14,
    }
    limite_total = limite_por_modo.get(modo, 10)  # fallback a 10
    current_confirmed_players = 0
    for p in players:
        if p.get("confirmed"):
            current_confirmed_players += 1

    if current_confirmed_players >= limite_total:
        raise HTTPException(status_code=400, detail=f"El reto ya tiene {limite_total} jugadores confirmados")
    # player.confirmed=True
    players.append(player.model_dump())

    await doc_ref.update({"players": players})
    all_confirmed = len(players) == limite_total and all(p.get("confirmed") for p in players)
    if all_confirmed:
        await doc_ref.update({"status": "confirmed"})
    # players.append(player.model_dump())
    # await doc_ref.update({"players": players})
    return {"message": "Jugador unido"}

class QuitMatchRequest(BaseModel):
    user_id: str
# class ConfirmMatchRequest(BaseModel):
#     player: Player
@router.post("/{match_id}/quit")
async def quit_match(match_id: str, data: QuitMatchRequest):
    user_id = data.user_id
    doc_ref = db.collection("Matches").document(match_id)
    doc = await doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Reto no encontrado")

    data = doc.to_dict()
    players = [j for j in data.get("players", []) if j["user_id"] != user_id]
    await doc_ref.update({"players": players})
    return {"message": "Jugador removido"}

@router.post("/{match_id}/confirm")
async def confirm_player(match_id: str, player:Player):
    user_id = player.user_id
    doc_ref = db.collection("Matches").document(match_id)
    doc = await doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Reto no encontrado")

    datos = doc.to_dict()
    players = datos.get("players", [])

    posicion_confirmadas = {
        "arquero": 0,
        "defensa": 0,
        "mediocampista": 0,
        "delantero": 0
    }
    current_confirmed_players = 0
    for p in players:
        if p.get("confirmed"):
            current_confirmed_players += 1
            pos = p.get("position", "")
            if pos in posicion_confirmadas:
                posicion_confirmadas[pos] += 1
    if player.position == "arquero" and posicion_confirmadas["arquero"] >= 1:
        raise HTTPException(status_code=400, detail="Ya hay un arquero confirmado")
    # Obtener el límite total permitido según el modo
    modo = datos.get("mode", "5vs5")
    limite_por_modo = {
        "5vs5": 10,
        "6vs6": 12,
        "7vs7": 14,
    }
    limite_total = limite_por_modo.get(modo, 10)  # fallback a 10


    if current_confirmed_players >= limite_total:
        raise HTTPException(status_code=400, detail=f"El reto ya tiene {limite_total} jugadores confirmados")
    # player.confirmed=True
    players.append(player.model_dump())

    await doc_ref.update({"players": players})
    all_confirmed = len(players) == limite_total and all(p.get("confirmed") for p in players)
    if all_confirmed:
        await doc_ref.update({"status": "confirmed"})
    
    return {"message": "Jugador confirmado"}

@router.post("/{match_id}/status")
async def update_match_status(
    match_id: str,
    user_id: str = Body(...),
    status: str = Body(...)
):
    doc_ref = db.collection("Matches").document(match_id)
    doc = await doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Reto no encontrado")

    data = doc.to_dict()
    allowed_status = ["open", "confirmed", "completed", "cancelled"]

    if status not in allowed_status:
        raise HTTPException(status_code=400, detail="Estado no permitido")

    if data["creator_id"] != user_id:
        raise HTTPException(status_code=403, detail="Solo el creador puede cambiar el estado")

    await doc_ref.update({"status": status})
    return {"message": f"Estado cambiado a '{status}'"}


@router.post("/{match_id}/change_position")
async def change_position(match_id: str, data: dict = Body(...)):
    user_id = data.get("user_id")
    nueva_posicion = data.get("position")
    print(f"{user_id=}")
    print(f"{nueva_posicion=}")
    doc_ref = db.collection("Matches").document(match_id)
    doc = await doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Reto no encontrado")

    datos = doc.to_dict()
    players = datos.get("players", [])

    # Validar si el usuario está
    jugador = next((p for p in players if p["user_id"] == user_id), None)
    print(f"{jugador=}")
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    jugador["position"] = nueva_posicion
    print(f"{jugador=}")
    print(f"{players=}")
    await doc_ref.update({"players": players})
    return {"message": "Posición actualizada"}
class ChangeTeamRequest(BaseModel):
    user_id: str
    team: str

@router.post("/{match_id}/change_team")
async def change_team(match_id: str, data:ChangeTeamRequest):
    user_id = data.user_id
    new_team = data.team
    
    doc_ref = db.collection("Matches").document(match_id)
    doc = await doc_ref.get()
    
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Reto no encontrado")

    datos = doc.to_dict()
    players = datos.get("players", [])
    
    # Find the player
    jugador = next((p for p in players if p["user_id"] == user_id), None)
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    team_counts = {"home": 0, "away": 0}
    for player in players:
        # if player["team"] in team_counts:
        team_counts[player["team"]] += 1

    players_limit = int(datos["mode"][0])
    if team_counts[new_team] >= players_limit:
        return {"message": "Equipo lleno"}
    # If player is already in that team → no update needed
    if jugador["team"] == new_team:
        return {"message": "Ya estás en este equipo"}
    
    jugador["team"] = new_team
    await doc_ref.update({"players": players})
    return {"message": "Posición actualizada"}

@router.post("/{match_id}/start")
async def start_match(match_id: str):
    doc_ref = db.collection("Matches").document(match_id)
    doc = await doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Reto no encontrado")
    players = doc.to_dict().get("players", [])
    is_all_confirmed = (players and all(player.get("confirmed", False) for player in players))
    if not is_all_confirmed:
        raise HTTPException(status_code=400, detail="No todos los jugadores están confirmados")
    
    await doc_ref.update({"status": "started"})
    return {"message": "Comenzó el reto"}

    