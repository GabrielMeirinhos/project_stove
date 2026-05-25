import React from 'react';
import { LucideIcon } from 'lucide-react';
import { cn } from '../../lib/utils';

interface StatCardProps {
  icon: LucideIcon;
  label: string;
  value: string | number;
  unit: string;
  color: 'green' | 'blue' | 'orange' | 'yellow' | 'red';
  progress?: number;
}

const StatCard: React.FC<StatCardProps> = ({ icon: Icon, label, value, unit, color, progress }) => {
  const colorMap = {
    green: 'text-green-400 bg-green-500/10 border-green-500/20 shadow-green-500/10',
    blue: 'text-blue-400 bg-blue-500/10 border-blue-500/20 shadow-blue-500/10',
    orange: 'text-orange-400 bg-orange-500/10 border-orange-500/20 shadow-orange-500/10',
    yellow: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20 shadow-yellow-500/10',
    red: 'text-red-400 bg-red-500/10 border-red-500/20 shadow-red-500/10',
  };

  const barColorMap = {
    green: 'bg-green-500',
    blue: 'bg-blue-500',
    orange: 'bg-orange-500',
    yellow: 'bg-yellow-500',
    red: 'bg-red-500',
  };

  return (
    <div className="glass glass-hover p-3 sm:p-4 rounded-2xl flex flex-col justify-between h-full group">
      <div className="flex items-center gap-2 sm:gap-3 mb-2 sm:mb-3">
        <div className={cn("w-8 h-8 sm:w-10 sm:h-10 rounded-lg sm:rounded-xl flex items-center justify-center border transition-transform duration-300 group-hover:scale-110", colorMap[color])}>
          <Icon size={16} className="sm:w-5 sm:h-5" />
        </div>
        <span className="text-[9px] sm:text-[10px] font-bold uppercase tracking-widest text-slate-500">{label}</span>
      </div>
      
      <div className="flex items-baseline gap-1">
        <span className="text-xl sm:text-2xl font-black text-slate-800 dark:text-white tracking-tight">{value}</span>
        <span className="text-[10px] sm:text-xs font-medium text-slate-500 dark:text-slate-400">{unit}</span>
      </div>

      {progress !== undefined && (
        <div className="mt-3 space-y-1.5">
          <div className="h-1 w-full bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
            <div 
              className={cn("h-full transition-all duration-1000", barColorMap[color])} 
              style={{ width: `${progress}%` }} 
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default StatCard;
