import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()


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
    import backend.database.init_db

    from backend.routers import auth, user, document, report, chat, session, ai, workspace

    app.include_router(user.router, prefix="/users")
    app.include_router(document.router, prefix="/documents")
    app.include_router(report.router, prefix="/reports")
    app.include_router(chat.router, prefix="/chat")
    app.include_router(session.router, prefix="/sessions")
    app.include_router(ai.router, prefix="/ai")
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(workspace.router)



@app.get("/")
def root():
    return {"message": "InsightAI is running!"}
