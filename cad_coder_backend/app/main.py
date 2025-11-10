from fastapi import FastAPI
from app.routers import generate, history, health

app = FastAPI(title="CAD-Coder Backend", version="1.0")

# Include all routers
app.include_router(generate.router)
app.include_router(history.router)
app.include_router(health.router)

@app.get("/")
async def root():
    return {"message": "CAD-Coder Backend is running"}
