from fastapi import FastAPI
from src.api.routes import replays

app = FastAPI(title="Rocket League Analytics API")

app.include_router(replays.router)


@app.get("/")
def read_root():
    return {"status": "healthy", "message": "Backend is running!"}
