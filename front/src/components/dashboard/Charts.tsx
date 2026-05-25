import React, { useState } from 'react';
import { 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';
import { HistoryData } from '../../types';
import { cn } from '../../lib/utils';
import { toast } from 'sonner';

interface ChartsProps {
  data: HistoryData[];
}

const Charts: React.FC<ChartsProps> = ({ data }) => {
  const [activeTab, setActiveTab] = useState<'growth' | 'health'>('growth');

  const handleTabChange = (tab: 'growth' | 'health') => {
    setActiveTab(tab);
    toast.info(`Visualizando: ${tab === 'growth' ? 'Crescimento' : 'Saúde'}`, {
      duration: 1500,
    });
  };

  return (
    <div className="glass p-4 sm:p-5 rounded-2xl h-full flex flex-col min-h-[300px]">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div className="flex gap-1 bg-slate-100/70 dark:bg-white/5 p-1 rounded-lg w-full sm:w-auto">
          <button 
            onClick={() => handleTabChange('growth')}
            className={cn(
              "flex-1 sm:flex-none px-3 py-2 rounded-md text-[10px] font-bold uppercase tracking-wider transition-all",
              activeTab === 'growth' ? "bg-green-500 text-white shadow-lg shadow-green-500/20" : "text-slate-500 dark:text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
            )}
          >
            Crescimento
          </button>
          <button 
            onClick={() => handleTabChange('health')}
            className={cn(
              "flex-1 sm:flex-none px-3 py-2 rounded-md text-[10px] font-bold uppercase tracking-wider transition-all",
              activeTab === 'health' ? "bg-blue-500 text-white shadow-lg shadow-blue-500/20" : "text-slate-500 dark:text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
            )}
          >
            Saúde
          </button>
        </div>
        <div className="text-[9px] sm:text-[10px] font-mono text-slate-500 dark:text-slate-400 uppercase tracking-widest">DADOS_HISTORICOS</div>
      </div>

      <div className="flex-1 min-h-[180px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="colorChart" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={activeTab === 'growth' ? "#22c55e" : "#3b82f6"} stopOpacity={0.3}/>
                <stop offset="95%" stopColor={activeTab === 'growth' ? "#22c55e" : "#3b82f6"} stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
            <XAxis 
              dataKey="day" 
              stroke="#475569" 
              fontSize={10} 
              tickLine={false} 
              axisLine={false} 
              dy={10}
            />
            <YAxis 
              stroke="#475569" 
              fontSize={10} 
              tickLine={false} 
              axisLine={false} 
              dx={-10}
            />
            <Tooltip 
              contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', fontSize: '12px' }}
              itemStyle={{ color: activeTab === 'growth' ? '#22c55e' : '#3b82f6' }}
            />
            <Area 
              type="monotone" 
              dataKey={activeTab === 'growth' ? "growth" : "health"} 
              stroke={activeTab === 'growth' ? "#22c55e" : "#3b82f6"} 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorChart)" 
              animationDuration={1000}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default Charts;
