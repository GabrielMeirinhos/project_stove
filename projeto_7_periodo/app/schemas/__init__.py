"""Modelos Pydantic (schemas) — um módulo por entidade do banco.

Cada entidade exporta três modelos:

* ``XxxCreate``  — payload de entrada para criação;
* ``XxxUpdate``  — payload de entrada para atualização parcial;
* ``XxxResponse`` (ou ``Xxx``) — representação completa, com ``id`` e
  timestamps gerados pelo backend.

Os tipos seguem **fielmente** a seção 3 do PDF (incluindo a coluna
``status`` calculada em ``sensor_reading``, que é gerada pelo serviço e
não pelo cliente).
"""
