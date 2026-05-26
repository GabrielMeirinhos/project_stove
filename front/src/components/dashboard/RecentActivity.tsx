import React from 'react';
import { Clock3, Droplets, Radio, SunMedium, Thermometer } from 'lucide-react';
import { Card } from '../ui/Card';
import { MqttStatus, SensorData } from '../../types';

interface RecentActivityProps {
  data?: SensorData | null;
  mqttStatus?: MqttStatus | null;
  language?: 'pt-BR' | 'en-US';
  historyAverage?: {
    growth: number;
    moisture: number;
    health: number;
  };
}

const formatTime = (value: string | null | undefined, language: 'pt-BR' | 'en-US') => {
  if (!value) {
    return '--:--';
  }

  return new Date(value).toLocaleTimeString(language, { hour: '2-digit', minute: '2-digit' });
};

export const RecentActivity: React.FC<RecentActivityProps> = ({ data, mqttStatus, historyAverage, language = 'pt-BR' }) => {
  const isEnglish = language === 'en-US';

  return (
    <Card
      title={isEnglish ? 'Recent activity' : 'Atividade Recente'}
      subtitle={isEnglish ? 'Based on received readings.' : 'Baseado nas leituras recebidas.'}
      className="bg-white/80 text-slate-800 border border-slate-100 shadow-sm dark:bg-slate-800 dark:text-white dark:border-none dark:shadow-xl"
    >
      <div className="flex flex-col gap-4 mt-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-2xl border border-slate-100 dark:border-slate-700 bg-white/70 dark:bg-slate-900/60 p-4 flex items-center gap-3">
            <div className="p-2 rounded-xl bg-emerald-100 dark:bg-emerald-500/15 text-emerald-600 dark:text-emerald-300">
              <Radio size={16} />
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-widest font-bold text-slate-500 dark:text-slate-400">MQTT</p>
              <p className="text-sm font-black text-slate-800 dark:text-slate-100">{mqttStatus?.connected ? (isEnglish ? 'Connected' : 'Conectado') : (isEnglish ? 'Disconnected' : 'Desconectado')}</p>
            </div>
          </div>
          <div className="rounded-2xl border border-slate-100 dark:border-slate-700 bg-white/70 dark:bg-slate-900/60 p-4 flex items-center gap-3">
            <div className="p-2 rounded-xl bg-blue-100 dark:bg-blue-500/15 text-blue-600 dark:text-blue-300">
              <Clock3 size={16} />
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-widest font-bold text-slate-500 dark:text-slate-400">{isEnglish ? 'Last reading' : 'Ultima leitura'}</p>
              <p className="text-sm font-black text-slate-800 dark:text-slate-100">{formatTime(data?.timestamp, language)}</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-2xl border border-slate-100 dark:border-slate-700 bg-white/70 dark:bg-slate-900/60 p-4 flex items-center gap-3">
            <div className="p-2 rounded-xl bg-cyan-100 dark:bg-cyan-500/15 text-cyan-600 dark:text-cyan-300">
              <Thermometer size={16} />
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-widest font-bold text-slate-500 dark:text-slate-400">{isEnglish ? 'Temperature' : 'Temperatura'}</p>
              <p className="text-sm font-black text-slate-800 dark:text-slate-100">{data ? `${data.temperature.toFixed(1)}°C` : '--'}</p>
            </div>
          </div>
          <div className="rounded-2xl border border-slate-100 dark:border-slate-700 bg-white/70 dark:bg-slate-900/60 p-4 flex items-center gap-3">
            <div className="p-2 rounded-xl bg-sky-100 dark:bg-sky-500/15 text-sky-600 dark:text-sky-300">
              <Droplets size={16} />
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-widest font-bold text-slate-500 dark:text-slate-400">{isEnglish ? 'Moisture' : 'Umidade'}</p>
              <p className="text-sm font-black text-slate-800 dark:text-slate-100">{data ? `${Math.round(data.moisture)}%` : '--'}</p>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-100 dark:border-slate-700 bg-white/70 dark:bg-slate-900/60 p-4 flex items-center gap-3">
          <div className="p-2 rounded-xl bg-amber-100 dark:bg-amber-500/15 text-amber-600 dark:text-amber-300">
            <SunMedium size={16} />
          </div>
          <div className="flex-1">
            <p className="text-[10px] uppercase tracking-widest font-bold text-slate-500 dark:text-slate-400">{isEnglish ? 'History summary' : 'Resumo historico'}</p>
            <p className="text-sm font-black text-slate-800 dark:text-slate-100">
              {historyAverage
                ? isEnglish
                  ? `Growth ${historyAverage.growth}%, moisture ${historyAverage.moisture}%, health ${historyAverage.health}%.`
                  : `Crescimento ${historyAverage.growth}%, umidade ${historyAverage.moisture}%, saude ${historyAverage.health}%.`
                : isEnglish
                  ? 'Waiting for historical data.'
                  : 'Aguardando dados historicos.'}
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
};
