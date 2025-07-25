from fastapi import APIRouter
from app.firestore import db


router = APIRouter()


@router.get("/{user_id}/matches")
async def get_matches_by_user(user_id: str):
    matches_docs = db.collection("Matches").stream()
    matches = [match_doc.to_dict() async for match_doc in matches_docs]
    created = [r for r in matches if r["creator_id"] == user_id]
    participating = [r for r in matches if user_id in r.get("players", []) and r["creator_id"] != user_id]
    return {"created": created, "participating": participating}