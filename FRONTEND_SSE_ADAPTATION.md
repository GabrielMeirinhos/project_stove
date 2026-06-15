# Adaptação Frontend para SSE com Discriminador de Tipos

## 📋 Resumo das Mudanças

O frontend foi adaptado para se comunicar com o backend real via **SSE simples** (Server-Sent Events), sem inventar WebSocket. O fluxo agora é:

```
ESP32 → MQTT Broker (HiveMQ) → Backend FastAPI → Servidor Node (porta 3000)
                                                           ↓
                                                    /api/live/stream (SSE)
                                                           ↓
                                                      Frontend React
```

---

## 🔧 Mudanças Implementadas

### 1. **`frontend/src/services/api.ts`**

#### ❌ Removido:
- `createWebSocketSubscription()` - Não há WebSocket no backend
- `createMqttSubscription()` - Cliente MQTT no frontend não é necessário
- Imports de `mqtt` library
- Funções auxiliares: `getDefaultWebSocketBaseUrl()`, `buildWebSocketUrl()`, `isMqttTransportConfigured()`, `isBridgeTransportConfigured()`

#### ✅ Adicionado:
```typescript
interface LiveStreamMessage {
  eventType?: 'status' | 'alert';      // Discriminador: qual tipo de mensagem?
  topic?: string;                       // Tópico MQTT original
  data?: unknown;                       // Payload real
  sensor?: SensorData | null;           // Compatibilidade
  status?: MqttStatus;                  // Compatibilidade
}

/**
 * Subscreve ao stream SSE de tempo real para status de planta e alertas.
 * O stream discrimina mensagens por eventType/topic.
 */
subscribeLiveStream(
  onStatus: (payload: PlantStatusPayload) => void,
  onAlert: (message: string) => void,
): RealtimeSubscription
```

**Lógica:**
- Abre EventSource em `/api/live/stream`
- Cada mensagem vem com `eventType: 'status' | 'alert'` ou `topic`
- Se status → chama `onStatus(payload)`
- Se alerta → chama `onAlert(message)`

#### Benefício:
- ✅ Sem WebSocket no frontend
- ✅ Sem cliente MQTT local
- ✅ Discriminação clara: sabe exatamente o que recebeu
- ✅ Compatível com SSE nativo do servidor Node

---

### 2. **`frontend/src/App.tsx`**

#### ❌ Removido:
- Chamadas a `api.subscribePlantStatus()` e `api.subscribePlantAlert()` (funções antigas)
- Tentativa de ativar fallback (`activateFallbackStream()`)
- Variáveis `statusSocket`, `alertSocket`, `fallbackEventSource`

#### ✅ Adicionado:
```typescript
// Único stream SSE, com callbacks separados para status e alerta
let liveStream: RealtimeSubscription | null = null;

const handleStatusUpdate = (payload: PlantStatusPayload) => {
  if (!isMounted) return;
  setPlantStatus(payload);
  setSensorData(mapPlantStatusToSensor(payload));
  setMqttStatus((current) => 
    current 
      ? { ...current, connected: true, lastMessageAt: new Date().toISOString() }
      : { connected: true, brokerUrl: 'mqtt://hivemq-cloud', ... }
  );
};

const handleAlertUpdate = (message: string) => {
  if (!isMounted) return;
  setPlantAlert(message);
  toast.error(message, {...});
};

liveStream = api.subscribeLiveStream(handleStatusUpdate, handleAlertUpdate);
```

**Benefício:**
- ✅ Separação clara entre telemetria (status) e alertas
- ✅ Estados independentes
- ✅ Menos complexidade, menos bugs

---

### 3. **`frontend/server.ts`** (Servidor Node)

#### ✅ Adicionado:
```typescript
// Armazenamento dos payloads MQTT reais (não transformados)
let latestPlantStatus: Record<string, unknown> | null = null;
let latestPlantAlerts: Array<Record<string, unknown>> = [];

/**
 * Broadcast de mensagens discriminadas por tipo.
 * Adiciona campo `eventType` para o frontend distinguir.
 */
const broadcastDiscriminatedEvent = (
  eventType: 'status' | 'alert', 
  topic: string, 
  data: unknown
) => {
  const message = { eventType, topic, data };
  for (const client of sseClients) {
    client.write(`data: ${JSON.stringify(message)}\n\n`);
  }
};
```

#### Roteamento MQTT:
```typescript
mqttClient.on("message", (topic, payload) => {
  
  if (topic === "planta/status") {
    // Telemetria da planta
    latestPlantStatus = JSON.parse(message);
    broadcastDiscriminatedEvent("status", "planta/status", latestPlantStatus);
    return;
  }
  
  if (topic === "planta/alerta") {
    // Alertas da planta
    const parsed = JSON.parse(message);
    if (parsed.alertas) {
      for (const alert of parsed.alertas) {
        broadcastDiscriminatedEvent("alert", "planta/alerta", alert.mensagem);
      }
    }
    return;
  }
  
  // Outros tópicos → sensor/telemetria genérica
  // (compatibilidade com ESP32 legado)
});
```

**Benefício:**
- ✅ SSE agora discrimina `planta/status` de `planta/alerta`
- ✅ Frontend recebe mensagens estruturadas
- ✅ Suporta múltiplos alertas em um único payload MQTT

---

## 📊 Fluxo de Dados Antes vs Depois

### ❌ Antes (Inventado):
```
Frontend
  ├─ WebSocket (inventado, não existe)
  │   └─ Tenta planta/status
  ├─ WebSocket (inventado, não existe)
  │   └─ Tenta planta/alerta
  ├─ MQTT direto no browser (mqtt.js)
  └─ Fallback: EventSource
```

### ✅ Depois (Real):
```
Frontend
  └─ EventSource: /api/live/stream
      ├─ Recebe: { eventType: 'status', topic: 'planta/status', data: {...} }
      ├─ Recebe: { eventType: 'alert', topic: 'planta/alerta', data: '...' }
      └─ Sem ambiguidade, sem fallbacks complexos
```

---

## 🎯 Contratos de Dados

### Mensagem de Status (do backend)
```json
{
  "eventType": "status",
  "topic": "planta/status",
  "data": {
    "planta": "Planta A",
    "ar_temp": 24.5,
    "ar_umi": 65,
    "solo_umi": 55,
    "luz_bruta": 1200,
    "luz_pct": 85,
    "bomba": "ligada",
    "estabilizado": true,
    "ts": 1718450000000
  }
}
```

### Mensagem de Alerta (do backend)
```json
{
  "eventType": "alert",
  "topic": "planta/alerta",
  "data": "Umidade do solo abaixo de 30%"
}
```

---

## ✅ Checklist: Tudo Funcionando?

- ✅ Sem WebSocket no backend (arquitetura real)
- ✅ SSE simples em `/api/live/stream`
- ✅ Discriminador claro: `eventType` 
- ✅ Status e alertas separados
- ✅ Sem imports de MQTT no frontend
- ✅ Sem fallbacks complexos
- ✅ Layout visual preservado
- ✅ REST calls mantidas (auth, história, etc)
- ✅ Compatível com servidor Node existente
- ✅ Sem mudanças necessárias no backend FastAPI

---

## 🚀 Como Testar

1. **Inicie o servidor Node:**
   ```bash
   cd frontend && npm run dev
   ```

2. **Faça login** (se necessário)

3. **Verifique DevTools → Network → EventStream:**
   - Deve ver mensagens SSE com formato:
   ```
   data: {"eventType":"status","topic":"planta/status","data":{...}}
   ```

4. **Publique mensagens MQTT** (via MQTT.fx ou similar):
   - `planta/status` → status aparece no dashboard
   - `planta/alerta` → toast de alerta aparece

5. **Sem erros no console do browser**

---

## 📝 Notas Importantes

- O servidor Node **continua conectado ao broker MQTT** (necessário para receber telemetria)
- O **frontend não conecta diretamente ao MQTT** (removemos mqtt.js)
- O discriminador `eventType` é adicionado **no servidor Node**, não vem do backend FastAPI
- Se o backend FastAPI implementar webhooks ou callbacks para SSE no futuro, pode remover essa camada do Node
- Layout visual mantém 100% de compatibilidade

---

## 🔗 Relação com Backend FastAPI

O backend FastAPI em `/api/v1`:
- ✅ Continua recebendo MQTT via cliente no `main.py`
- ✅ Persiste em `sensor_reading` e `planta_alerta`
- ✅ Expõe endpoints REST normalmente
- ✅ **Não precisa de mudanças para o frontend funcionar**

O backend Node (porta 3000):
- ✅ Age como **proxy/adapter** do stream MQTT
- ✅ Discrimina mensagens por tópico
- ✅ Emite SSE para o frontend
- ✅ Chamadas REST proxy para FastAPI

