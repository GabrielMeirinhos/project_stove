import React from 'react';
import {
  LineChart,
  Line,
  ResponsiveContainer,
  YAxis
} from 'recharts';
import { Card } from '../ui/Card';
import { TrendingDown, TrendingUp } from 'lucide-react';
import { SensorData } from '../../types';

interface MiniChartProps {
  title: string;
  value: string;
  data: any[];
  color: string;
  icon: any;
}

interface EnvironmentalDataProps {
  data?: SensorData | null;
  language?: 'pt-BR' | 'en-US';
}

const MiniChart: React.FC<MiniChartProps> = ({ title, value, data, color, icon: Icon }) => {
  return (
    <div className="flex flex-col gap-3 p-4 rounded-2xl bg-slate-50/50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700 hover:bg-white dark:hover:bg-slate-800 transition-all duration-300">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest">{title}</span>
        <div className="flex items-center gap-2">
          <Icon size={14} className={color === '#3b82f6' ? 'text-blue-600' : 'text-red-600'} />
          <span className="text-lg font-black text-slate-800 dark:text-slate-100">{value}</span>
        </div>
      </div>
      <div className="h-16 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <YAxis hide domain={['dataMin - 5', 'dataMax + 5']} />
            <Line
              type="monotone"
              dataKey="value"
              stroke={color}
              strokeWidth={2}
              dot={false}
              animationDuration={1000}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

const buildTrend = (baseValue: number, spread: number) => {
  return [
    { time: '10:00', value: Math.max(0, baseValue - spread) },
    { time: '11:00', value: baseValue - spread / 2 },
    { time: '12:00', value: baseValue },
    { time: '13:00', value: baseValue + spread / 2 },
    { time: '14:00', value: baseValue + spread },
  ];
};

export const EnvironmentalData: React.FC<EnvironmentalDataProps> = ({ data, language = 'pt-BR' }) => {
  const isEnglish = language === 'en-US';
  const hasData = Boolean(data);
  const moistureSeries = hasData && data ? buildTrend(data.moisture, 6) : [];
  const temperatureSeries = hasData && data ? buildTrend(data.temperature, 2) : [];

  return (
    <Card title={isEnglish ? 'Environmental data' : 'Dados Ambientais'} subtitle={isEnglish ? 'Live sensor summary.' : 'Resumo ao vivo dos sensores.'} className="flex flex-col gap-4">
      <MiniChart
        title={isEnglish ? 'Moisture levels' : 'Niveis de Umidade'}
        value={hasData && data ? `${Math.round(data.moisture)}%` : '--'}
        data={moistureSeries}
        color="#3b82f6"
        icon={TrendingDown}
      />
      <MiniChart
        title={isEnglish ? 'Temperature' : 'Temperatura'}
        value={hasData && data ? `${data.temperature.toFixed(1)}°C` : '--'}
        data={temperatureSeries}
        color="#ef4444"
        icon={TrendingUp}
      />
    </Card>
  );
};
