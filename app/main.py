from fastapi import FastAPI
# (оставь тут свои ИМЕЮЩИЕСЯ импорты роутеров, если были)
from app.routers.v2_grants import router as v2_grants_router  # ← наш новый

app = FastAPI(title="Edu/Grants API")

# (оставь тут свои ИМЕЮЩИЕСЯ app.include_router(...) если были)
app.include_router(v2_grants_router)  # ← подключаем v2

@app.get("/")
def root():
    return {"message": "Hello from edu-grants"}

from app.routers.v2_grants import router as v2_grants_router
app.include_router(v2_grants_router)

