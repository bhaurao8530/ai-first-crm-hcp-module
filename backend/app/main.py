import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base, SessionLocal
from . import models
from .routers import hcps, interactions, chat

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI-First CRM - HCP Module", version="1.0.0")

origins = [os.getenv("FRONTEND_ORIGIN", "http://localhost:5173"), "http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hcps.router)
app.include_router(interactions.router)
app.include_router(chat.router)


@app.on_event("startup")
def seed_demo_data():
    """Seeds a couple of demo HCPs so the reviewer can try the app immediately."""
    db = SessionLocal()
    try:
        if db.query(models.HCP).count() == 0:
            demo = [
                models.HCP(name="Dr. Ananya Rao", specialty="Cardiology",
                           hospital="Ruby Hall Clinic, Pune", email="ananya.rao@example.com",
                           phone="9876500001", segment="A"),
                models.HCP(name="Dr. Vikram Shah", specialty="Endocrinology",
                           hospital="Jehangir Hospital, Pune", email="vikram.shah@example.com",
                           phone="9876500002", segment="B"),
                models.HCP(name="Dr. Priya Menon", specialty="Oncology",
                           hospital="KEM Hospital, Mumbai", email="priya.menon@example.com",
                           phone="9876500003", segment="A"),
            ]
            db.add_all(demo)
            db.commit()
    finally:
        db.close()


@app.get("/")
def root():
    return {"status": "ok", "service": "AI-First CRM HCP Module API"}


@app.get("/api/health")
def health():
    return {"status": "healthy"}
