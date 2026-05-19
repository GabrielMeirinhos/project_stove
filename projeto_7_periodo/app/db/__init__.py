"""Camada de acesso a dados (PostgreSQL via psycopg 3).

* ``connection``     — pool de conexões compartilhado pela aplicação;
* ``repository``     — implementação do repositório que substitui o
  ``InMemoryRepository`` original mantendo a mesma interface;
* ``schema``         — bootstrap idempotente das tabelas a partir de
  ``sql/schema.sql``.
"""