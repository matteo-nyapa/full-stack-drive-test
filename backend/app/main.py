from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import files, auth, folders # 👈 añade auth

app = FastAPI(title="Drive Backend", version="0.1.0")

origins = [
    "http://localhost",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(folders.router)# 👈 nuevo
app.include_router(files.router)
