from __future__ import annotations

import os

from dotenv import load_dotenv
import uvicorn


def _load_env() -> None:
    load_dotenv(".env.local")
    load_dotenv(".env")


def main() -> None:
    _load_env()
    host = os.getenv("UVICORN_HOST", "0.0.0.0")
    port = int(os.getenv("UVICORN_PORT", "8000"))
    uvicorn.run("app.api:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
