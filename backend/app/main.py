from fastapi import FastAPI

app = FastAPI(title="Sheria RAG")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
