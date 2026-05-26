import React from 'react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts';
import { Card } from '../ui/Card';
import { HistoryData } from '../../types';

interface GrowthChartProps {
  data: HistoryData[];
  language?: 'pt-BR' | 'en-US';
}

export const GrowthChart: React.FC<GrowthChartProps> = ({ data, language = 'pt-BR' }) => {
  const isEnglish = language === 'en-US';
  const chartData = data.map((item) => ({
    name: item.day,
    value: item.growth,
  }));

  const subtitle = chartData.length > 0 ? (isEnglish ? 'Based on received history.' : 'Baseado no historico recebido.') : (isEnglish ? 'Waiting for growth history.' : 'Aguardando historico de crescimento.');

  return (
    <Card title={isEnglish ? 'Growth analysis' : 'Analise de Crescimento'} subtitle={subtitle} className="overflow-hidden">
      <div className="h-48 w-full mt-4 relative bg-gradient-to-b from-green-100/50 to-white dark:from-slate-900/80 dark:to-slate-900 rounded-3xl p-4 border border-slate-100 dark:border-slate-700/50">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="colorGrowth" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#22c55e" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#94a3b8" opacity={0.25} />
            <XAxis 
              dataKey="name" 
              axisLine={false} 
              tickLine={false} 
              tick={{ fontSize: 10, fill: '#94a3b8', fontWeight: 600 }}
              dy={10}
            />
            <YAxis hide />
            <Tooltip 
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  return (
                    <div className="bg-white dark:bg-slate-900 text-slate-800 dark:text-white px-3 py-1.5 rounded-full text-[10px] font-bold shadow-xl border border-slate-200 dark:border-slate-800 flex items-center gap-1">
                      <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
                      {payload[0].value}%
                    </div>
                  );
                }
                return null;
              }}
            />
            <Area 
              type="monotone" 
              dataKey="value" 
              stroke="#22c55e" 
              strokeWidth={3}
              fillOpacity={1} 
              fill="url(#colorGrowth)" 
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};
