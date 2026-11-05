from fastapi import FastAPI
from app.routers.v2_grants import router as v2_grants_router

app = FastAPI(title="Edu/Grants API")

app.include_router(v2_grants_router)


@app.get("/")
def root():
    return {"message": "Hello from edu-grants"}