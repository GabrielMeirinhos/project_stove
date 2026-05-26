# Gaia Monitoring System

Interface experimental de monitoramento para plantas, com visualização procedural, indicadores ambientais, histórico de crescimento e fluxo de escaneamento 3D. O projeto combina React, Vite, Express e componentes visuais para simular um painel de operação da plataforma Gaia.

## Visão geral

O aplicativo atual apresenta:

- um dashboard principal com visual da planta procedural e linha do tempo de crescimento;
- cartões de status com condições de luz, solo, umidade e fertilização;
- gráficos de crescimento e histórico de saúde;
- uma área de alertas e atividade recente;
- uma tela de scan 3D com câmera, captura sequencial de imagens e progresso simulado;

## Tecnologias

- React 19
- TypeScript
- Vite
- Express
- Tailwind CSS
- Recharts
- Framer Motion
- React Three Fiber e Three.js
- Sonner para notificações

## Como executar

### Pré-requisitos

- Node.js 18 ou superior
- npm

### Instalação

1. Instale as dependências.
   ```bash
   npm install
   ```

2. Inicie o ambiente local.
   ```bash
   npm run dev
   ```

O comando `npm run dev` sobe o servidor Express em `http://localhost:3000` e injeta o Vite em modo middleware.

### Outros comandos

```bash
npm run build
npm run preview
npm run lint
npm run clean
```

## Funcionalidades principais

- Dashboard com navegação lateral e alternância entre módulos.
- Visual procedural da planta com controle de dia de crescimento.
- Métricas ambientais e cartões de contexto em tempo real.
- Gráficos de evolução de crescimento e saúde.
- Scan 360° com captura automática de quadros da câmera e simulação de conexão com hardware.

## API local

O arquivo `server.ts` expõe endpoints simulados para apoiar a interface:

- `GET /api/dados` retorna leituras mockadas de sensores.
- `GET /api/modelo-atual?day=1` retorna um estágio de modelo 3D para o dia informado.
- `GET /api/historico` gera uma série histórica de crescimento, umidade e saúde.
- `POST /api/analyze-image` simula a análise de uma imagem da planta.

## Estrutura do projeto

- `src/App.tsx` controla a navegação entre os módulos do painel.
- `src/components/dashboard/` concentra os blocos visuais da experiência principal.
- `src/components/layout/` contém a navegação lateral.
- `src/components/ui/` reúne componentes visuais reutilizáveis.
- `server.ts` inicializa a API mock e o middleware do Vite.

## Observações

- A tela de scan depende de permissão de câmera no navegador.
- Alguns módulos do menu lateral ainda exibem estado de desenvolvimento.
