import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI(title="InsightAI")

cors_origins_raw = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:8080, http://localhost:8081, http://localhost:5173"
)

origins = [origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    logger.warning("STARTUP STEP 1")
    import backend.database.init_db
    logger.warning("STARTUP STEP 2")

    from backend.routers import auth
    logger.warning("AUTH LOADED")
    app.include_router(auth.router, prefix="/auth", tags=["auth"])

    from backend.routers import document
    logger.warning("DOCUMENT LOADED")
    app.include_router(document.router, prefix="/documents")

    from backend.routers import report
    logger.warning("REPORT LOADED")
    app.include_router(report.router, prefix="/reports")

    from backend.routers import chat
    logger.warning("CHAT LOADED")
    app.include_router(chat.router, prefix="/chat")

    from backend.routers import workspace
    logger.warning("WORKSPACE LOADED")
    app.include_router(workspace.router)


@app.get("/")
def root():
    return {"message": "InsightAI is running!"}
