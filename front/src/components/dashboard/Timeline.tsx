import React from 'react';
import { cn } from '../../lib/utils';
import { Card } from '../ui/Card';

interface TimelineProps {
  day: number;
  setDay: (day: number) => void;
}

export const Timeline: React.FC<TimelineProps> = ({ day, setDay }) => {
  const milestones = [1, 5, 10, 15, 20];

  return (
    <Card title="Linha do Tempo" subtitle="Historico de Crescimento" className="flex-1">
      <div className="flex flex-col gap-6 mt-4">
        <div className="flex justify-between items-center px-2">
          {milestones.map((d) => (
            <button
              key={d}
              onClick={() => setDay(d)}
              className={cn(
                "w-10 h-10 rounded-xl text-[10px] font-bold transition-all duration-300 flex items-center justify-center",
                day === d 
                  ? "bg-green-500 text-white shadow-lg shadow-green-500/20 neon-glow-green scale-110" 
                  : "bg-slate-50 text-slate-400 hover:bg-slate-100 hover:text-slate-600 border border-slate-100"
              )}
            >
              D{d}
            </button>
          ))}
        </div>
        
        <div className="px-2">
          <input 
            type="range" 
            min="1" 
            max="20" 
            value={day} 
            onChange={(e) => setDay(parseInt(e.target.value))}
            className="w-full h-2 bg-slate-100 rounded-full appearance-none cursor-pointer accent-green-500"
          />
          <div className="flex justify-between mt-2 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
            <span>Dia 1</span>
            <span>Dia 20</span>
          </div>
        </div>
      </div>
    </Card>
  );
};
