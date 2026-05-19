"""Aplicação backend do Sistema de Monitoramento de Horta Inteligente.

Este pacote implementa, em Python/FastAPI, o backend descrito na
documentação ``documentacao_banco.pdf`` (versão 1.0/2025). A documentação
prevê o uso de Spring Boot (Java); aqui adotamos FastAPI por ser a stack
padrão do ecossistema Python para APIs REST modernas, mas o **schema do
banco**, os **nomes das entidades**, os **relacionamentos** e as **regras
de negócio** seguem fielmente a especificação.

Camadas da aplicação::

    app/
    ├── main.py        # Inicialização da API FastAPI
    ├── config.py      # Configurações (host, porta, versão da API, etc.)
    ├── database.py    # Banco "figurativo" em memória + repositório genérico
    ├── schemas/       # Modelos Pydantic (Create / Update / Response)
    ├── services/      # Regras de negócio (ex: status calculado, alertas)
    └── routers/       # Endpoints REST por entidade
"""

__version__ = "1.0.0"
