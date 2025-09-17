from fastapi import APIRouter, Header, HTTPException, Depends
from app.firebase_admin import verify_token
from pydantic import BaseModel
from typing import Optional
from typing import List

from app.firestore import db
from app.models import UserStats
from app.models import UserFriend
from app.models import UserInvite
from google.cloud.firestore_v1 import SERVER_TIMESTAMP


router = APIRouter()


@router.get("/{user_id}/matches")
async def get_matches_by_user(user_id: str):
    matches_docs = db.collection("Matches").stream()
    matches = [match_doc.to_dict() async for match_doc in matches_docs]
    created = [r for r in matches if r["creator_id"] == user_id]
    match_players = {match["id"]:match.get("players",[]) for match in matches}
    participating = [match for match in matches if user_id in [player["user_id"] for player in match_players[match["id"]]]]
    return {"created": created, "participating": participating}


def get_current_user(authorization: str = Header(...)):
    """Extrae y verifica el token Firebase del header Authorization"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token no proporcionado correctamente")
    
    token = authorization.split(" ")[1]
    try:
        user = verify_token(token)
        return user  # puedes devolver user["uid"], user["email"], etc.
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.get("/protected")
def ruta_protegida(user_data: dict = Depends(get_current_user)):
    return {
        "message": "Bienvenido, usuario autenticado",
        "user_id": user_data["uid"],
        "email": user_data.get("email", "no-email"),
    }

@router.get("/{username}/stats")
async def get_user_stats(username:str):
    doc_ref = db.collection("UserStats").document(username)
    doc = await doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return doc.to_dict()

class UpdateUserStats(BaseModel):
    pref_position: Optional[str] = ""
    photo_url: Optional[str] = ""

@router.post("/{username}/stats")
async def update_user_stats(username:str,data:UpdateUserStats):
    update_data = {}
    if data.pref_position:
        update_data["pref_position"] = data.pref_position
    if data.photo_url:
        update_data["photo_url"] = data.photo_url
    if not update_data:
        return {"successfull": True}
        
    doc_ref = db.collection("UserStats").document(username)
    doc = await doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    await doc_ref.update(update_data)

    return {"successfull": True}

class FriendResponseDTO(BaseModel):
    user_id: str
    username: str
    photo_url: str

class FriendsResponseDTO(BaseModel):
    friends: List[FriendResponseDTO]

@router.get("/{user_id}/friends")
async def get_user_friends(user_id:str):
    matches_docs = db.collection("UserFriends").where("user_id","==",user_id).stream()
    friends = [match_doc.to_dict() async for match_doc in matches_docs]
    friends_list:List[FriendResponseDTO] = [
        FriendResponseDTO.model_construct(
            user_id=friend["friend_id"],
            username=friend["username"],
            photo_url=friend["photo_url"],
        )
        for friend in friends
    ]
    
    return FriendsResponseDTO.model_construct(
        friends=friends_list
    ).model_dump()

class AcceptInviteRequest(BaseModel):
    invite_id: str
    username: str

class InviteFriendRequest(BaseModel):
    username: str

@router.post("/{user_id}/invites")
async def invite_friend(user_id:str, data:InviteFriendRequest):
    user_friends_docs = (
        db.collection("UserFriends")
        .where("user_id","==",user_id)
        .where("username","==",data.username)
        .limit(1)
        .stream()
    )
    results = [doc async for doc in user_friends_docs]  
    if results:
        raise HTTPException(status_code=409, detail="Amigo ya existe")
    user_doc_ref = db.collection("Users").document(user_id)
    user_doc = await user_doc_ref.get()
    user_friend_doc_ref = db.collection("UserInvites").document()
    await user_friend_doc_ref.set(
        UserInvite.model_construct(
            user_id=user_id,
            username=user_doc["username"],
            invite_username=data.username,
            status="pending",
            created_at=SERVER_TIMESTAMP,
        ).model_dump()
    )


    return {"successfull": True}

@router.post("/{user_id}/invites/{invite_id}")
async def accept_invite(user_id:str, invite_id:str, data:AcceptInviteRequest):
    invite_doc_ref = db.collection("UserInvites").document(invite_id)
    invite_doc = await invite_doc_ref.get()
    if not invite_doc.exists:
        raise HTTPException(status_code=404, detail="Invitacion no encontrada")
    user_stat_doc_ref = db.collection("UserStats").document(data.username)
    user_stat_doc = await user_stat_doc_ref.get()
    if not user_stat_doc.exists:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    # Create UserFriend
    user_friend_doc_ref = db.collection("UserFriends").document()
    await user_friend_doc_ref.set(
        UserFriend.model_construct(
            user_id=user_id,
            friend_id=user_stat_doc["user_id"],
            username=user_stat_doc["username"],
            photo_url=user_stat_doc["photo_url"],
        ).model_dump()
    )
    # Update UserInvite
    await invite_doc_ref.update({
        "status": "accepted",
        "updated_at": SERVER_TIMESTAMP
    })


    return {"successfull": True}

class DeleteFriendRequest(BaseModel):
    username: str

@router.delete("/{user_id}/friends")
async def remove_friend(user_id:str, data:DeleteFriendRequest):
    user_friends_docs = (
        db.collection("UserFriends")    
        .where("user_id","==",user_id)
        .where("username","==",data.username)
        .stream())
    
    async for doc in user_friends_docs:
        await doc.reference.delete()

    return {"successfull": True}

class UserInviteResponseDTO(BaseModel):
    id: str
    username: str
    status: str
    created_at: str

class UserInvitesResponseDTO(BaseModel):
    invites: List[UserInviteResponseDTO]

@router.get("/{user_id}/invites")
async def get_user_invites(user_id:str):
    use_doc_ref = db.collection("Users").document(user_id)
    user_doc = await use_doc_ref.get()
    
    matches_docs = db.collection("UserInvites").where("invite_username","==",user_doc["username"]).where("status","==","pending").stream()
    # invites = [match_doc.to_dict() ]
    invites_list:List[UserInviteResponseDTO] = []
    async for match_doc in matches_docs:
        invite = match_doc.to_dict()
        invites_list.append(UserInviteResponseDTO.model_construct(
            id=match_doc.id,
            username=invite["username"],
            status=invite["status"],
            created_at=invite["created_at"],
        ))
    #     for invite in invites
    # ]
    
    return UserInvitesResponseDTO.model_construct(
        invites=invites_list
    ).model_dump()

class InitUserStatsRequest(BaseModel):
    username: str
    user_id: str
    photo_url: str


@router.post("/initstats")
async def init_user_stats(data:InitUserStatsRequest):
    user_stats_doc_ref = db.collection("UserStats").document(data.username)
    user_stats_doc = await user_stats_doc_ref.get()
    print(f"{user_stats_doc=}")
    if user_stats_doc.exists:
        raise HTTPException(status_code=409, detail=f"Username '{data.username}' ya existe")
    user_stats = UserStats.model_construct(
        user_id=data.user_id,
        username=data.username,
        photo_url=data.photo_url
    )
    
    await user_stats_doc_ref.set(user_stats.model_dump())
    user_ref = db.collection("Users").document(data.user_id)
    await user_ref.update({
        "username": data.username
    })
    return user_stats_doc.to_dict()