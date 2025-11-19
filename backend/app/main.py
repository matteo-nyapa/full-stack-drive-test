from fastapi import FastAPI

from app.routes import files

app = FastAPI(title="Drive Backend", version="0.1.0")


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(files.router)
