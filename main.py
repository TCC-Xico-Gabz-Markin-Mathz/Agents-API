from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import contextRoutes

app = FastAPI()

app.include_router(contextRoutes.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello World"}