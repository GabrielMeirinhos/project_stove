# Guia de Integração ESP32 — GAIA

Este documento descreve **tudo o que o firmware do ESP32 precisa fazer**
para se integrar ao backend GAIA: conectar no broker MQTT (HiveMQ Cloud),
publicar telemetria/heartbeat e receber comandos da bomba de irrigação.

O backend já está pronto e validado end-to-end — basta o firmware seguir
o contrato abaixo.

---

## 1. Pré-requisito: cadastrar o dispositivo no backend

Antes do ESP32 começar a publicar, ele precisa existir no banco. Cada
mensagem é gravada com o `device_id` (UUID) embutido no tópico, e o
backend valida que esse UUID existe.

**Como cadastrar (uma vez só, por ESP32):**

`POST http://<backend>/api/v1/devices`

```json
{
  "plant_id": "<uuid-da-planta-vinculada>",
  "name": "ESP32-Horta-01",
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "firmware_version": "1.0.0",
  "location_description": "Estufa principal — bancada A",
  "is_active": true
}
```

A resposta traz o `id` (UUID) — **esse é o `device_id` que o ESP32 vai
usar nos tópicos MQTT**. Anote/grave em EEPROM/NVS.

Alternativa em runtime: o ESP32 pode chamar
`GET /api/v1/devices/by-mac/{mac_address}` no boot para descobrir o
próprio `id` sem precisar gravá-lo no firmware.

---

## 2. Credenciais do broker (HiveMQ Cloud)

| Campo | Valor |
|-------|-------|
| Host | `bdffc9a5bf6e4bf28591393206fc27e0.s1.eu.hivemq.cloud` |
| Porta | `8883` (MQTT sobre TLS — **obrigatório**) |
| Usuário | `gaia-esp32` |
| Senha | *(combinar com o time — não versionar no firmware)* |
| Protocolo | MQTT 3.1.1 |
| TLS | Sim (HiveMQ Cloud só aceita conexões criptografadas) |

> ⚠️ **A porta 1883 (sem TLS) não funciona.** O HiveMQ Cloud exige TLS
> em todas as conexões.

---

## 3. Contrato de tópicos

Tudo é namespaceado por `gaia/{device_id}/...`. Substitua `{device_id}`
pelo UUID retornado no passo 1.

### 3.1 ESP32 → Backend

#### `gaia/{device_id}/telemetry` — leituras dos sensores

**Direção:** ESP32 publica. Backend assina (já está implementado).
**QoS:** 1 (entrega garantida ao menos uma vez)
**Frequência sugerida:** a cada 30 segundos
**Payload:** JSON UTF-8

```json
{
  "temperature_celsius": 24.7,
  "humidity_percent": 62.3,
  "soil_moisture_percent": 48.1,
  "light_lux": 850.0
}
```

**Regras:**
- Todos os campos são **opcionais** — mande apenas os sensores que estiverem disponíveis.
- `humidity_percent` e `soil_moisture_percent` devem estar entre `0` e `100`.
- `temperature_celsius` em graus Celsius (ponto, não vírgula).
- `light_lux` em lux (sempre ≥ 0).
- Pode incluir `"recorded_at": "2026-05-22T14:30:00Z"` se você quiser
  fixar o timestamp da coleta; se omitir, o backend usa o instante de
  recepção.

**O que o backend faz ao receber:**
1. Valida o JSON
2. Compara cada métrica com a faixa ideal da planta vinculada
3. Calcula o `status` agregado (`normal` / `warning` / `critical`)
4. Grava a leitura no PostgreSQL
5. Para cada métrica fora da faixa, gera um `alert` automaticamente
6. Atualiza o `last_seen_at` do device

#### `gaia/{device_id}/heartbeat` — sinal de vida

**Direção:** ESP32 publica. Backend assina.
**QoS:** 0 (perda eventual é ok)
**Frequência sugerida:** a cada 60 segundos
**Payload:** qualquer JSON — o backend ignora o conteúdo

```json
{ "ts": 1716412800, "uptime_s": 3600 }
```

Atualiza o `last_seen_at` do device. Usado pelo dashboard para mostrar
"online/offline".

### 3.2 Backend → ESP32

#### `gaia/{device_id}/cmd/pump` — comando de irrigação

**Direção:** Backend publica. ESP32 deve **assinar** no momento da
conexão (`subscribe`).
**QoS:** 1
**Payload:**

```json
{ "action": "on", "duration_seconds": 15 }
```

**Comportamento esperado do ESP32:**
- `action: "on"` → liga a bomba pelo tempo indicado em `duration_seconds`
- `action: "off"` → desliga imediatamente
- Sempre faça uma checagem de segurança: limite máximo de duração
  (ex: 60s) e cooldown entre acionamentos.

---

## 4. Exemplo de firmware (Arduino / PlatformIO)

Bibliotecas necessárias:
- `WiFi.h` (built-in)
- `WiFiClientSecure.h` (built-in)
- [`PubSubClient`](https://github.com/knolleary/pubsubclient) (Nick O'Leary)
- [`ArduinoJson`](https://arduinojson.org/)

```cpp
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// --- WiFi ---
const char* WIFI_SSID = "sua-rede";
const char* WIFI_PASS = "sua-senha-wifi";

// --- HiveMQ Cloud ---
const char* MQTT_HOST = "bdffc9a5bf6e4bf28591393206fc27e0.s1.eu.hivemq.cloud";
const int   MQTT_PORT = 8883;
const char* MQTT_USER = "gaia-esp32";
const char* MQTT_PASS = "<combinar-com-o-time>";

// --- Identidade deste device ---
// Pegue o UUID retornado em POST /api/v1/devices e cole aqui
const char* DEVICE_ID = "0746da27-6942-44d2-bb49-626079f5ccda";

// Tópicos derivados
String topicTelemetry = String("gaia/") + DEVICE_ID + "/telemetry";
String topicHeartbeat = String("gaia/") + DEVICE_ID + "/heartbeat";
String topicPumpCmd   = String("gaia/") + DEVICE_ID + "/cmd/pump";

WiFiClientSecure net;
PubSubClient mqtt(net);

void onMqttMessage(char* topic, byte* payload, unsigned int len) {
  // Comando da bomba
  if (String(topic) == topicPumpCmd) {
    StaticJsonDocument<128> doc;
    if (deserializeJson(doc, payload, len)) return;
    const char* action = doc["action"] | "off";
    float duration = doc["duration_seconds"] | 0.0f;
    if (strcmp(action, "on") == 0 && duration > 0 && duration <= 60) {
      // TODO: ligar GPIO da bomba pelo tempo informado
      Serial.printf("Bomba ON por %.1fs\n", duration);
    } else {
      // TODO: desligar GPIO da bomba
      Serial.println("Bomba OFF");
    }
  }
}

void mqttReconnect() {
  while (!mqtt.connected()) {
    String clientId = String("gaia-esp32-") + String((uint32_t)ESP.getEfuseMac(), HEX);
    if (mqtt.connect(clientId.c_str(), MQTT_USER, MQTT_PASS)) {
      mqtt.subscribe(topicPumpCmd.c_str(), 1);
      Serial.println("MQTT conectado");
    } else {
      Serial.printf("MQTT erro rc=%d — retry em 3s\n", mqtt.state());
      delay(3000);
    }
  }
}

void setup() {
  Serial.begin(115200);

  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.println("WiFi ok");

  // Em produção, embarque o root CA do Let's Encrypt em vez de setInsecure()
  net.setInsecure();

  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(onMqttMessage);
}

unsigned long lastTelemetry = 0;
unsigned long lastHeartbeat = 0;

void loop() {
  if (!mqtt.connected()) mqttReconnect();
  mqtt.loop();

  unsigned long now = millis();

  // Telemetria a cada 30s
  if (now - lastTelemetry > 30000) {
    lastTelemetry = now;
    StaticJsonDocument<256> doc;
    doc["temperature_celsius"]   = lerDHT22Temperatura();    // sua leitura
    doc["humidity_percent"]      = lerDHT22Umidade();        // sua leitura
    doc["soil_moisture_percent"] = lerSensorSolo();          // sua leitura
    doc["light_lux"]             = lerLDR();                 // sua leitura

    char buf[256];
    size_t n = serializeJson(doc, buf);
    mqtt.publish(topicTelemetry.c_str(), (uint8_t*)buf, n, false);
  }

  // Heartbeat a cada 60s
  if (now - lastHeartbeat > 60000) {
    lastHeartbeat = now;
    char buf[64];
    snprintf(buf, sizeof(buf), "{\"uptime_s\":%lu}", now / 1000);
    mqtt.publish(topicHeartbeat.c_str(), buf, false);
  }
}
```

---

## 5. Como testar antes de plugar no GAIA real

### a) Testar a conexão MQTT sem sensores
Suba o ESP32 com o firmware acima e publique um payload "dummy" fixo.
Veja se aparece no:

- **Web Client do HiveMQ Cloud** → console do HiveMQ → "Web Client" →
  inscreva-se em `gaia/#`. Se a publicação aparecer ali, o TLS e a
  autenticação estão ok.

- **API REST do backend** → `GET /api/v1/sensor-readings?device_id=...`
  deve listar as leituras gravadas.

### b) Testar a recepção do comando de bomba
Pelo Web Client do HiveMQ, publique manualmente em
`gaia/<seu-device-id>/cmd/pump`:
```json
{ "action": "on", "duration_seconds": 5 }
```
O ESP32 deve reagir (acender LED, ligar relé, log no serial).

---

## 6. Checklist antes de declarar pronto

- [ ] Dispositivo cadastrado via `POST /devices` e `device_id` anotado
- [ ] WiFi reconectando sozinho após queda
- [ ] MQTT reconectando sozinho após queda (com backoff)
- [ ] TLS funcionando na porta 8883
- [ ] Publica em `gaia/{id}/telemetry` a cada 30s em JSON válido
- [ ] Publica em `gaia/{id}/heartbeat` a cada 60s
- [ ] Assina `gaia/{id}/cmd/pump` e aciona a bomba ao receber `"action":"on"`
- [ ] Limite de segurança: duração máxima da bomba (ex: 60s)
- [ ] Sem credenciais hard-coded no repositório (use `secrets.h` no `.gitignore`)

---

## 7. Troubleshooting

| Sintoma | Provável causa |
|---------|----------------|
| `MQTT_CONNECT_BAD_CREDENTIALS` (rc=4 ou 5) | Usuário/senha incorretos, ou permissões insuficientes no HiveMQ |
| `MQTT_CONNECT_FAILED` (rc=-2) | TLS não habilitado, ou root CA não validado — em dev use `setInsecure()` |
| Backend não grava nada | `device_id` no tópico não existe na tabela `device`. Cadastre primeiro via REST. |
| `device_id ... não existe` no log do backend | UUID errado no tópico — confira que está usando o UUID do banco, não o MAC |
| Leitura cai como `400 Bad Request` | JSON inválido (vírgula como decimal, campo fora do range 0-100, etc.) |
| Nenhum alerta gerado | A planta vinculada tem a faixa configurada? Confira em `GET /plants/{plant_id}` |

---

## 8. Convenções importantes

- **Use ponto como separador decimal** no JSON (`24.7`, não `24,7`)
- **Timestamps em UTC ISO-8601** (`2026-05-22T14:30:00Z`) se for enviá-los
- **MAC address** sempre no formato `AA:BB:CC:DD:EE:FF` (maiúsculas, dois-pontos)
- **Identifique-se com `client_id` único** (use o `efuseMac` do ESP32 para gerar)

---

## Contato

Backend já está rodando e validado com o mock (`scripts/mock_esp32.py`).
Para qualquer dúvida sobre payload, status calculado ou alertas, use o
mock como referência funcional.
