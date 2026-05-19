"""Repositório PostgreSQL com a mesma interface do ``InMemoryRepository``.

O objetivo é trocar a camada de persistência **sem alterar serviços nem
routers**. As operações ``add``/``get``/``update``/``delete``/``exists``
viram SQL puro (``INSERT``/``SELECT``/``UPDATE``/``DELETE``); operações
que recebem callables Python (``list(where=...)``, ``find_one``,
``count``) executam um ``SELECT *`` e filtram em memória — solução
adequada para o volume acadêmico do projeto e que mantém os serviços
intactos.

Quando o sistema crescer, basta reescrever ``list``/``find_one``/``count``
para aceitar um filtro estruturado (ex: dict ``coluna -> valor``) e
traduzir para ``WHERE`` nativo, aproveitando os índices da seção 5 do PDF.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar
from uuid import UUID

from psycopg import sql

from app.db.connection import get_pool

T = TypeVar("T", bound=Dict[str, Any])


class PostgresRepository(Generic[T]):
    """Repositório genérico apontando para uma tabela do schema.

    Parameters
    ----------
    table_name:
        Nome físico da tabela no PostgreSQL.
    """

    def __init__(self, table_name: str) -> None:
        self.table_name = table_name
        self._table = sql.Identifier(table_name)

    # ------------------------------------------------------------------
    # CRUD básico
    # ------------------------------------------------------------------
    def add(self, record: T) -> T:
        """Insere ``record`` e devolve a linha completa após o INSERT."""
        cols = list(record.keys())
        stmt = sql.SQL("INSERT INTO {tbl} ({cols}) VALUES ({vals}) RETURNING *").format(
            tbl=self._table,
            cols=sql.SQL(", ").join(sql.Identifier(c) for c in cols),
            vals=sql.SQL(", ").join(sql.Placeholder() for _ in cols),
        )
        with get_pool().connection() as conn, conn.cursor() as cur:
            cur.execute(stmt, [record[c] for c in cols])
            row = cur.fetchone()
            assert row is not None
            return row  # type: ignore[return-value]

    def get(self, record_id: UUID) -> Optional[T]:
        stmt = sql.SQL("SELECT * FROM {tbl} WHERE id = %s").format(tbl=self._table)
        with get_pool().connection() as conn, conn.cursor() as cur:
            cur.execute(stmt, [record_id])
            return cur.fetchone()  # type: ignore[return-value]

    def list(
        self,
        *,
        where: Optional[Callable[[T], bool]] = None,
        order_by: Optional[str] = None,
        descending: bool = False,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[T]:
        """Lê todos os registros e aplica filtro/ordenação/paginação em
        memória, exatamente como o repositório original. Suficiente para
        a escala acadêmica deste projeto."""
        stmt = sql.SQL("SELECT * FROM {tbl}").format(tbl=self._table)
        with get_pool().connection() as conn, conn.cursor() as cur:
            cur.execute(stmt)
            rows: List[T] = list(cur.fetchall())  # type: ignore[arg-type]

        if where is not None:
            rows = [r for r in rows if where(r)]
        if order_by is not None:
            rows.sort(
                key=lambda r: (r.get(order_by) is None, r.get(order_by)),
                reverse=descending,
            )
        if offset:
            rows = rows[offset:]
        if limit is not None:
            rows = rows[:limit]
        return rows

    def update(self, record_id: UUID, changes: Dict[str, Any]) -> Optional[T]:
        """Aplica apenas os campos não-nulos de ``changes`` e retorna a
        linha atualizada (ou ``None`` se o id não existir)."""
        effective = {k: v for k, v in changes.items() if v is not None}
        if not effective:
            return self.get(record_id)

        assignments = sql.SQL(", ").join(
            sql.SQL("{col} = {val}").format(
                col=sql.Identifier(k), val=sql.Placeholder()
            )
            for k in effective.keys()
        )
        stmt = sql.SQL(
            "UPDATE {tbl} SET {assignments} WHERE id = %s RETURNING *"
        ).format(tbl=self._table, assignments=assignments)

        with get_pool().connection() as conn, conn.cursor() as cur:
            cur.execute(stmt, [*effective.values(), record_id])
            return cur.fetchone()  # type: ignore[return-value]

    def delete(self, record_id: UUID) -> bool:
        stmt = sql.SQL("DELETE FROM {tbl} WHERE id = %s").format(tbl=self._table)
        with get_pool().connection() as conn, conn.cursor() as cur:
            cur.execute(stmt, [record_id])
            return cur.rowcount > 0

    def exists(self, record_id: UUID) -> bool:
        stmt = sql.SQL("SELECT 1 FROM {tbl} WHERE id = %s").format(tbl=self._table)
        with get_pool().connection() as conn, conn.cursor() as cur:
            cur.execute(stmt, [record_id])
            return cur.fetchone() is not None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def find_one(self, predicate: Callable[[T], bool]) -> Optional[T]:
        rows = self.list(where=predicate, limit=1)
        return rows[0] if rows else None

    def count(self, where: Optional[Callable[[T], bool]] = None) -> int:
        if where is None:
            stmt = sql.SQL("SELECT COUNT(*) AS c FROM {tbl}").format(tbl=self._table)
            with get_pool().connection() as conn, conn.cursor() as cur:
                cur.execute(stmt)
                row = cur.fetchone()
                return int(row["c"]) if row else 0  # type: ignore[index]
        return len(self.list(where=where))