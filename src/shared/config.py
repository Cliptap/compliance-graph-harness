import os

# Configuración básica de base de datos relacional ligera (AD-005)
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./catalog.db")

# Configuración de orígenes permitidos para CORS
CORS_ORIGINS: list[str] = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "*",
]
