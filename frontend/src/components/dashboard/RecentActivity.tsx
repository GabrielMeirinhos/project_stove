import React from 'react';
import { Play, Trash2 } from 'lucide-react';
import { Card } from '../ui/Card';

export const RecentActivity: React.FC = () => {
  return (
    <Card
      title="Plantas Monitoradas"
      subtitle="Guias e boas praticas."
      className="bg-white/80 text-slate-800 border border-slate-100 shadow-sm dark:bg-slate-800 dark:text-white dark:border-none dark:shadow-xl"
    >
      <div className="flex flex-col gap-6 mt-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-full bg-slate-100 dark:bg-white/10 flex items-center justify-center">
              <Play size={16} className="text-green-600 dark:text-white fill-current" />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-white/10 flex items-center justify-center hover:bg-slate-200 dark:hover:bg-white/20 transition-colors cursor-pointer text-slate-500 dark:text-slate-200">
              <Trash2 size={14} />
            </div>
          </div>
        </div>

        {/* Waveform Visualizer */}
        <div className="h-16 flex items-end gap-1 px-2">
          {[...Array(30)].map((_, i) => {
            const height = Math.random() * 80 + 20;
            return (
              <div 
                key={i} 
                className="flex-1 bg-green-400/60 rounded-full transition-all duration-500"
                style={{ height: `${height}%` }}
              />
            );
          })}
        </div>

        <div className="flex items-center justify-between text-[10px] font-bold text-slate-400 dark:text-white/40 uppercase tracking-widest">
          <div className="flex items-center gap-2">
            <span className="text-slate-700 dark:text-white/80">1x</span>
          </div>
          <span>05:34</span>
        </div>
      </div>
    </Card>
  );
};
