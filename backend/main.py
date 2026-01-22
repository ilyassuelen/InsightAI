from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import user, document, report, chat, session, ai
import backend.database.init_db

app = FastAPI(title="InsightAI")

# --- CORS Middleware ---
origins = [
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Router ---
app.include_router(user.router, prefix="/users")
app.include_router(document.router, prefix="/documents")
app.include_router(report.router, prefix="/reports")
app.include_router(chat.router, prefix="/chat")
app.include_router(session.router, prefix="/sessions")
app.include_router(ai.router, prefix="/ai")


@app.get("/")
def root():
    return {"message": "InsightAI is running!"}

