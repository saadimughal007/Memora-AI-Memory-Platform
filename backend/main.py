from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database.db import initialize_database
from backend.api.routes import router

app = FastAPI(title="Memora AI Memory API",version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:8501","http://127.0.0.1:8501"],
                   allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

@app.on_event("startup")
def startup():
    initialize_database()

app.include_router(router,prefix="/api")

@app.get("/health")
def health():
    return {"status":"ok","service":"memora"}
