import React from 'react';
import { AlertTriangle, Droplet } from 'lucide-react';
import { Card } from '../ui/Card';
import { cn } from '../../lib/utils';
import { SensorData } from '../../types';

interface AlertItemProps {
  icon: any;
  title: string;
  message: string;
  color: 'red' | 'orange';
}

const AlertItem: React.FC<AlertItemProps> = ({ icon: Icon, title, message, color }) => {
  const colorMap = {
    red: 'bg-red-50 border-red-100 text-red-600 dark:bg-red-500/10 dark:border-red-500/30 dark:text-red-300',
    orange: 'bg-orange-50 border-orange-100 text-orange-600 dark:bg-orange-500/10 dark:border-orange-500/30 dark:text-orange-300',
  };

  return (
    <div className={cn("p-4 rounded-2xl border flex items-start gap-4 hover:bg-white dark:hover:bg-slate-800/40 transition-all duration-300", colorMap[color])}>
      <div className={cn("p-2 rounded-xl bg-white dark:bg-slate-900 shadow-sm border border-slate-100 dark:border-slate-700", color === 'red' ? 'text-red-500 dark:text-red-300' : 'text-orange-500 dark:text-orange-300')}>
        <Icon size={20} />
      </div>
      <div className="flex flex-col gap-1">
        <h4 className="text-sm font-black uppercase tracking-widest">{title}</h4>
        <p className="text-xs font-medium opacity-80">{message}</p>
      </div>
    </div>
  );
};

interface AlertsProps {
  data?: SensorData | null;
  language?: 'pt-BR' | 'en-US';
}

const buildAlerts = (data?: SensorData | null, isEnglish = false) => {
  if (!data) {
    return [];
  }

  const alerts = [] as Array<{
    icon: any;
    title: string;
    message: string;
    color: 'red' | 'orange';
  }>;

  if (data.moisture < 35) {
    alerts.push({
      icon: Droplet,
      title: isEnglish ? 'Low soil moisture' : 'Umidade do solo baixa',
      message: isEnglish ? `Current moisture at ${Math.round(data.moisture)}%.` : `Umidade atual em ${Math.round(data.moisture)}%.`,
      color: 'red',
    });
  } else if (data.moisture > 75) {
    alerts.push({
      icon: Droplet,
      title: isEnglish ? 'High soil moisture' : 'Umidade do solo alta',
      message: isEnglish ? `Current moisture at ${Math.round(data.moisture)}%.` : `Umidade atual em ${Math.round(data.moisture)}%.`,
      color: 'orange',
    });
  }

  if (data.temperature > 30 || data.temperature < 18) {
    alerts.push({
      icon: AlertTriangle,
      title: isEnglish ? 'Temperature out of range' : 'Temperatura fora da faixa',
      message: isEnglish ? `Current temperature at ${data.temperature.toFixed(1)}°C.` : `Temperatura atual em ${data.temperature.toFixed(1)}°C.`,
      color: 'orange',
    });
  }

  if (data.luminosity < 500) {
    alerts.push({
      icon: AlertTriangle,
      title: isEnglish ? 'Low light level' : 'Luminosidade baixa',
      message: isEnglish ? `Current light level at ${Math.round(data.luminosity)} lux.` : `Luminosidade atual em ${Math.round(data.luminosity)} lux.`,
      color: 'orange',
    });
  }

  if (data.health < 70) {
    alerts.push({
      icon: AlertTriangle,
      title: isEnglish ? 'Reduced plant health' : 'Saude da planta reduzida',
      message: isEnglish ? `Current index at ${Math.round(data.health)}%.` : `Indice atual em ${Math.round(data.health)}%.`,
      color: 'red',
    });
  }

  return alerts;
};

export const Alerts: React.FC<AlertsProps> = ({ data, language = 'pt-BR' }) => {
  const isEnglish = language === 'en-US';
  const alerts = buildAlerts(data, isEnglish);

  return (
    <Card title={isEnglish ? 'Alerts' : 'Alertas'} className="flex flex-col gap-3">
      {alerts.length > 0 ? (
        alerts.map((alert, index) => (
          <AlertItem
            key={`${alert.title}-${index}`}
            icon={alert.icon}
            title={alert.title}
            message={alert.message}
            color={alert.color}
          />
        ))
      ) : (
        <div className="rounded-2xl border border-dashed border-slate-200 dark:border-slate-700 p-4 text-sm text-slate-500 dark:text-slate-400">
          {isEnglish ? 'No out-of-range conditions at the moment.' : 'Nenhuma condicao fora da faixa no momento.'}
        </div>
      )}
    </Card>
  );
};
