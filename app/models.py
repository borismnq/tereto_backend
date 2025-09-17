from pydantic import BaseModel
from typing import List, Optional

class User(BaseModel):
    id: str
    created_at: str
    email: str
    name: str
    username: str
    photo_url: str


class Player(BaseModel):
    user_id: str
    name: str
    position: Optional[str] = None
    confirmed: bool = False
    status: str = "active"
    team: str = "home"


class Match(BaseModel):
    id: Optional[str] = None
    creator_id: str
    creator_name: str
    mode: str  # 5vs5, 6vs6...
    place: str
    date: str  # ISO format
    time: str
    duration: int
    status: str = "open"
    bet: Optional[str] = None
    players: List[Player] = []
    # confirmed_players: List[Player] = []
    notas: Optional[str] = None
    creator_position: Optional[str] = None

class UserStats(BaseModel):
    user_id: str
    username: str
    photo_url: str
    pref_position: str = ""
    matches_played: int = 0
    rank: int = 0
    wins: int = 0
    loses: int = 0
    draws: int = 0
    stars: str = 0
class UserFriend(BaseModel):
    user_id: str
    friend_id: str
    username: str
    photo_url: str

class UserInvite(BaseModel):
    user_id: str
    username: str
    invite_username: str
    status: str
    created_at: str