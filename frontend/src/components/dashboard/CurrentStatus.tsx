import React from 'react';
import { Droplets, Sun, Waves, Leaf } from 'lucide-react';
import { Card } from '../ui/Card';
import { cn } from '../../lib/utils';
import { MqttStatus, SensorData } from '../../types';

interface StatusItemProps {
  icon: any;
  label: string;
  value: string;
  color: string;
}

interface CurrentStatusProps {
  data?: SensorData | null;
  mqttStatus?: MqttStatus | null;
}

const StatusItem: React.FC<StatusItemProps> = ({ icon: Icon, label, value, color }) => {
  return (
    <div className="flex flex-col gap-3 p-4 rounded-2xl bg-white/50 backdrop-blur-sm border border-slate-100 hover:bg-white transition-all duration-300 shadow-sm group">
      <div className="flex items-center gap-3">
        <div className={cn("p-2 rounded-xl bg-white shadow-sm border border-slate-100 transition-transform group-hover:scale-110", color)}>
          <Icon size={18} />
        </div>
        <span className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest leading-none">{label}</span>
      </div>
      <span className="text-sm font-black text-slate-800 dark:text-slate-100">{value}</span>
    </div>
  );
};

const getLightCondition = (luminosity: number) => {
  if (luminosity < 500) return 'Baixa';
  if (luminosity < 1000) return 'Equilibrada';
  return 'Alta';
};

const getSoilCondition = (moisture: number) => {
  if (moisture < 35) return 'Seco';
  if (moisture < 65) return 'Saudavel';
  return 'Umido';
};

export const CurrentStatus: React.FC<CurrentStatusProps> = ({ data, mqttStatus }) => {
  const hasData = Boolean(data);

  return (
    <Card
      title="Detalhes da Planta"
      subtitle={mqttStatus?.connected ? 'Feed MQTT ao vivo.' : 'Aguardando dados MQTT.'}
    >
      <div className="mb-4 flex items-center justify-between rounded-2xl border border-slate-100 dark:border-slate-700 bg-white/70 dark:bg-slate-900/60 px-4 py-3 text-[10px] font-bold uppercase tracking-widest text-slate-500 dark:text-slate-400">
        <span>Status do Feed</span>
        <span className={cn(mqttStatus?.connected ? 'text-green-600' : 'text-amber-500')}>
          {mqttStatus?.connected ? 'Conectado' : 'Desconectado'}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <StatusItem 
          icon={Sun} 
          label="Condicao de Luz" 
          value={hasData && data ? getLightCondition(data.luminosity) : '--'} 
          color="text-amber-500"
        />
        <StatusItem 
          icon={Droplets} 
          label="Saude do Solo" 
          value={hasData && data ? getSoilCondition(data.moisture) : '--'} 
          color="text-blue-500"
        />
        <StatusItem 
          icon={Waves} 
          label="Temperatura" 
          value={hasData && data ? `${data.temperature.toFixed(1)}°C` : '--'} 
          color="text-cyan-500"
        />
        <StatusItem 
          icon={Leaf} 
          label="Saude da Planta" 
          value={hasData && data ? `${Math.round(data.health)}%` : '--'} 
          color="text-green-500"
        />
      </div>
    </Card>
  );
};
