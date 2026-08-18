from fastapi import FastAPI
from app.api.datasets import router as datasets_router

app = FastAPI(title="DataWebsite API")
app.include_router(datasets_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}