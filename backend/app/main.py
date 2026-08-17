from fastapi import FastAPI

app = FastAPI(title="DataWebsite API")

@app.get("/health")
def health_check():
    return {"status": "ok"}