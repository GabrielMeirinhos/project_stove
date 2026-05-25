import React from 'react';
import { cn } from '../../lib/utils';

interface ProgressBarProps {
  value: number;
  color?: 'green' | 'blue' | 'yellow' | 'red' | 'orange';
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({ value, color = 'green', className }) => {
  const colorMap = {
    green: 'bg-green-500',
    blue: 'bg-blue-500',
    yellow: 'bg-yellow-500',
    red: 'bg-red-500',
    orange: 'bg-orange-500',
  };

  return (
    <div className={cn("h-1.5 w-full bg-slate-100 rounded-full overflow-hidden border border-slate-200/50", className)}>
      <div 
        className={cn("h-full transition-all duration-500 ease-out", colorMap[color])} 
        style={{ width: `${value}%` }}
      />
    </div>
  );
};
