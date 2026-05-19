"""Camada de serviços — regras de negócio do sistema.

Em particular, esta camada concentra:

* o **cálculo do status** de cada ``sensor_reading`` (seção 6.3 do PDF);
* a **geração automática de alertas** quando uma leitura ultrapassa os
  thresholds da planta vinculada (seção 3.8);
* a **conclusão de eventos de irrigação** (preenchimento de
  ``finished_at`` quando ausente);
* o **vínculo bidirecional** entre ``plant_image`` e ``vision_analysis``.
"""
