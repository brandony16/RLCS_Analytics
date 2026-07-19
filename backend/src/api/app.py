from fastapi import FastAPI

app = FastAPI(title="Rocket League Analytics API")

@app.get("/")
def read_root():
    return {"status": "healthy", "message": "Backend is running!"}