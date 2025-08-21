# app/main.py
from fastapi import FastAPI
from app.routers.content import make_content_router

app = FastAPI(title="edu-grants API")

for name in ["grants", "courses", "scholarships", "nonprofits"]:
    app.include_router(make_content_router(name))

@app.get("/")
def root():
    return {"message": "Hello from edu-grants"}

from app.routers.v2_grants import router as v2_grants_router
app.include_router(v2_grants_router)
