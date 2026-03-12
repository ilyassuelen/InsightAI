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

    from backend.routers import auth, user, document, report, chat, session, ai, workspace
    logger.warning("STARTUP STEP 3")

    app.include_router(user.router, prefix="/users")
    logger.warning("STARTUP STEP 4")
    app.include_router(document.router, prefix="/documents")
    logger.warning("STARTUP STEP 5")
    app.include_router(report.router, prefix="/reports")
    logger.warning("STARTUP STEP 6")
    app.include_router(chat.router, prefix="/chat")
    logger.warning("STARTUP STEP 7")
    app.include_router(session.router, prefix="/sessions")
    logger.warning("STARTUP STEP 8")
    app.include_router(ai.router, prefix="/ai")
    logger.warning("STARTUP STEP 9")
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    logger.warning("STARTUP STEP 10")
    app.include_router(workspace.router)
    logger.warning("STARTUP STEP 11")



@app.get("/")
def root():
    return {"message": "InsightAI is running!"}
