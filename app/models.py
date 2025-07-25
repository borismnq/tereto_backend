from pydantic import BaseModel
from typing import List, Optional

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
    mode: str  # 5vs5, 6vs6...
    place: str
    date: str  # ISO format
    time: str
    duration: int
    status: str = "open"
    bet: Optional[str] = None
    players: List[Player] = []
    confirmed_players: List[Player] = []
    notas: Optional[str] = None