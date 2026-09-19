from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="CarHunter API", version="0.1.0")
app.include_router(router)

@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
