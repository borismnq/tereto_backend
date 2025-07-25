from fastapi import FastAPI
from app.routes import matches
from app.routes import users
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Permitir origenes
origins = [
    "http://localhost:5173",  # Tu frontend en desarrollo
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,           # O ["*"] para permitir todo (no recomendado en producción)
    allow_credentials=True,
    allow_methods=["*"],             # Permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],             # Permite todos los headers
)

app.include_router(matches.router, prefix="/matches", tags=["Retos"])
app.include_router(users.router, prefix="/users", tags=["Usuarios"])