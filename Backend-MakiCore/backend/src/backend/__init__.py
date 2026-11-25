def main() -> None:
    """Levanta el servidor con `uv run backend` (equivale a uvicorn con recarga)."""
    import uvicorn

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
