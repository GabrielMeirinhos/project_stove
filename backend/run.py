"""Ponto de entrada da aplicação.

Executa o servidor uvicorn que serve a API FastAPI definida em
``app.main:app``. Use::

    python run.py

ou diretamente::

    uvicorn app.main:app --reload
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
