# Documentação dos Endpoints — Sistema de Monitoramento de Horta Inteligente

Backend em **FastAPI** que expõe uma API REST para o sistema de horta inteligente
(ESP32 + sensores + câmera + bomba de irrigação), persistindo dados em
**PostgreSQL (Neon)**.

- **Título:** Sistema de Monitoramento de Horta Inteligente
- **Versão:** 1.0.0
- **Prefixo global:** `/api/v1`
- **Documentação interativa (Swagger UI):** `/docs`
- **OpenAPI JSON:** `/openapi.json`

Todos os caminhos abaixo são **relativos ao prefixo** `/api/v1` (exceto o
health-check, que vive na raiz).

---

## Sumário

1. [Health-check](#1-health-check)
2. [Plantas (`/plants`)](#2-plantas-plants)
3. [Dispositivos (`/devices`)](#3-dispositivos-devices)
4. [Leituras de sensores (`/sensor-readings`)](#4-leituras-de-sensores-sensor-readings)
5. [Eventos de irrigação (`/irrigation-events`)](#5-eventos-de-irrigação-irrigation-events)
6. [Imagens (`/images`)](#6-imagens-images)
7. [Análises de visão computacional (`/vision-analyses`)](#7-análises-de-visão-computacional-vision-analyses)
8. [Eventos do sistema (`/system-events`)](#8-eventos-do-sistema-system-events)
9. [Alertas (`/alerts`)](#9-alertas-alerts)

---

## 1. Health-check

| Método | Caminho | Descrição |
|--------|---------|-----------|
| `GET`  | `/`     | Verifica se o serviço está no ar. Retorna `service`, `version`, `status` e link para `/docs`. |

**Uso:** sondagem de liveness por orquestradores (Docker, Kubernetes) ou apenas
para conferir manualmente que o backend subiu.

---

## 2. Plantas (`/plants`)

Cadastro das espécies de planta que o sistema é capaz de monitorar — cada
planta carrega as **faixas ideais** (umidade do solo, temperatura, luz etc.)
usadas depois para classificar leituras de sensores e gerar alertas.

| Método  | Caminho                  | Descrição |
|---------|--------------------------|-----------|
| `POST`  | `/plants`                | Cadastra uma nova espécie de planta. |
| `GET`   | `/plants`                | Lista plantas cadastradas. Aceita paginação via `limit` (1–500, padrão 100) e `offset`. |
| `GET`   | `/plants/{plant_id}`     | Busca uma planta pelo `UUID`. Retorna `404` se não existir. |
| `PATCH` | `/plants/{plant_id}`     | Atualização parcial dos dados da planta. |
| `DELETE`| `/plants/{plant_id}`     | Remove a planta. Retorna `404` se não existir. |

---

## 3. Dispositivos (`/devices`)

Cadastro e monitoramento dos **ESP32** instalados na horta. Cada device está
tipicamente vinculado a uma planta e envia leituras de sensores via MQTT/HTTP.

| Método  | Caminho                                | Descrição |
|---------|----------------------------------------|-----------|
| `POST`  | `/devices`                             | Cadastra um novo ESP32. |
| `GET`   | `/devices`                             | Lista dispositivos. Filtros opcionais: `plant_id` e `only_active` (apenas ativos). |
| `GET`   | `/devices/by-mac/{mac_address}`        | Busca dispositivo pelo MAC address — útil para o próprio ESP32 se "auto-identificar" no primeiro boot. |
| `GET`   | `/devices/{device_id}`                 | Busca dispositivo por `UUID`. |
| `PATCH` | `/devices/{device_id}`                 | Atualiza dados do dispositivo (apelido, planta vinculada, status, etc.). |
| `POST`  | `/devices/{device_id}/heartbeat`       | Registra heartbeat MQTT — atualiza o campo `last_seen_at` para indicar que o ESP32 está online. |
| `DELETE`| `/devices/{device_id}`                 | Remove dispositivo. |

---

## 4. Leituras de sensores (`/sensor-readings`)

Coleta histórica das medições enviadas pelos ESP32 (umidade do solo,
temperatura, luminosidade, etc.). É o **principal canal de ingestão** de dados
sensoriais.

| Método | Caminho                          | Descrição |
|--------|----------------------------------|-----------|
| `POST` | `/sensor-readings`               | Registra uma nova leitura. O backend **calcula o status** (ok / warning / critical) comparando o valor com a faixa ideal da planta vinculada e **gera registros automáticos em `alert`** caso a leitura esteja fora da faixa. Endpoint normalmente consumido pelo serviço Spring Boot (ou, em uma evolução futura, pelo próprio ESP32). |
| `GET`  | `/sensor-readings`               | Consulta histórica com filtros: `device_id`, `status` (ok / warning / critical), `start`, `end`, e paginação (`limit` 1–1000, `offset`). |
| `GET`  | `/sensor-readings/{reading_id}`  | Busca uma leitura específica por `UUID`. |

**Thresholds** (definidos em `app/config.py`):
- `WARNING_DEVIATION = 0.0`
- `CRITICAL_DEVIATION = 5.0`

---

## 5. Eventos de irrigação (`/irrigation-events`)

Histórico dos acionamentos da bomba de irrigação — quem disparou, quando
começou e quando terminou.

| Método  | Caminho                                | Descrição |
|---------|----------------------------------------|-----------|
| `POST`  | `/irrigation-events`                   | Registra o **início** de um acionamento da bomba. |
| `GET`   | `/irrigation-events`                   | Lista eventos. Filtros: `device_id`, `limit` (1–500), `offset`. |
| `GET`   | `/irrigation-events/{event_id}`        | Busca um evento por `UUID`. |
| `PATCH` | `/irrigation-events/{event_id}`        | Atualiza/**finaliza** o evento — tipicamente usado para preencher `finished_at` quando a bomba é desligada. |

---

## 6. Imagens (`/images`)

Registro das imagens capturadas pela câmera para inspeção visual da planta.
Armazena metadados (caminho/URL, timestamp, device). O conteúdo binário fica
em armazenamento externo.

| Método  | Caminho                       | Descrição |
|---------|-------------------------------|-----------|
| `POST`  | `/images`                     | Registra uma imagem recém-capturada (cria o metadado no banco). |
| `GET`   | `/images`                     | Lista imagens. Filtros: `device_id`, `limit` (1–500, padrão 50), `offset`. |
| `GET`   | `/images/{image_id}`          | Busca uma imagem por `UUID`. |
| `PATCH` | `/images/{image_id}`          | Atualiza metadados da imagem. |

---

## 7. Análises de visão computacional (`/vision-analyses`)

Resultados da inferência de visão computacional sobre uma imagem capturada
(ex.: detecção de pragas, classificação de saúde da planta).

| Método | Caminho                                       | Descrição |
|--------|-----------------------------------------------|-----------|
| `POST` | `/vision-analyses`                            | Registra uma nova análise (output do modelo de CV). |
| `GET`  | `/vision-analyses`                            | Lista análises. Paginação: `limit` (1–500, padrão 50), `offset`. |
| `GET`  | `/vision-analyses/{analysis_id}`              | Busca análise por `UUID`. |
| `GET`  | `/vision-analyses/by-image/{image_id}`        | Recupera a análise associada a uma imagem específica. |

---

## 8. Eventos do sistema (`/system-events`)

Log de **auditoria operacional** — falhas de leitura, desconexões, reinícios
de dispositivos, ações administrativas, etc. Suporta o fluxo de
"reconhecimento" pelo operador.

| Método | Caminho                                       | Descrição |
|--------|-----------------------------------------------|-----------|
| `POST` | `/system-events`                              | Registra um evento de auditoria. |
| `GET`  | `/system-events`                              | Lista eventos. Filtros: `device_id`, `only_unacknowledged` (apenas pendentes), `limit` (1–1000), `offset`. |
| `GET`  | `/system-events/{event_id}`                   | Busca evento por `UUID`. |
| `POST` | `/system-events/{event_id}/acknowledge`       | Marca o evento como **reconhecido** pelo operador (workflow de ack). |

---

## 9. Alertas (`/alerts`)

Alertas gerados quando uma leitura ficou fora da faixa ideal (criados
**automaticamente** pelo endpoint `POST /sensor-readings`) ou criados
manualmente pelo painel. Possui fluxo de resolução.

| Método | Caminho                            | Descrição |
|--------|------------------------------------|-----------|
| `POST` | `/alerts`                          | Cria alerta manualmente. Para alertas automáticos use `POST /sensor-readings`. |
| `GET`  | `/alerts`                          | Lista alertas. Filtros: `device_id`, `only_active` (apenas não resolvidos), `limit` (1–1000), `offset`. |
| `GET`  | `/alerts/{alert_id}`               | Busca alerta por `UUID`. |
| `POST` | `/alerts/{alert_id}/resolve`       | Marca o alerta como **resolvido** (preenche `resolved_at`). |

---

## Observações gerais

- **Identificadores:** todas as entidades usam `UUID` como chave primária.
- **Códigos HTTP:**
  - `201 Created` — sucesso em `POST` de criação.
  - `200 OK` — sucesso em `GET`, `PATCH`, `DELETE` e ações.
  - `404 Not Found` — recurso inexistente.
  - `422 Unprocessable Entity` — payload inválido (validação Pydantic).
- **CORS:** liberado para qualquer origem (`*`) — para produção, restringir à
  origem real do dashboard Angular.
- **Ciclo de vida:** no startup o pool de conexões PostgreSQL é aberto e o
  schema é garantido (`ensure_schema`); no shutdown o pool é fechado.
