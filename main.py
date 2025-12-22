from fastapi import FastAPI
from backend.routers import user, document, report, chat, session

app = FastAPI(title="InsightAI")

app.include_router(user.router, prefix="/users")
app.include_router(document.router, prefix="/documents")
app.include_router(report.router, prefix="/reports")
app.include_router(chat.router, prefix="/chat")
app.include_router(session.router, prefix="/sessions")


@app.get("/")
def root():
    return {"message": "InsightAI is running!"}
