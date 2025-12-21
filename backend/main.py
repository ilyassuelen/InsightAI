from fastapi import FastAPI

app = FastAPI(title="InsightAI")

@app.get("/")
def root():
    return {"message": "InsightAI is running!"}