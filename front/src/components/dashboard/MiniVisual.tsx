import React from 'react';
import { Leaf } from 'lucide-react';

export const MiniVisual: React.FC = () => {
  return (
    <div className="glass p-6 rounded-2xl flex items-end justify-around gap-2 h-32 overflow-hidden relative">
      <div className="absolute inset-0 bg-gradient-to-t from-green-500/5 to-transparent pointer-events-none" />
      
      {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((i) => (
        <div 
          key={i} 
          className="flex flex-col items-center gap-1 flex-1 h-full justify-end"
        >
          {/* Bar structure */}
          <div 
            className="w-full bg-slate-100 rounded-t-sm border-x border-t border-slate-200" 
            style={{ height: `${10 + Math.random() * 60}%` }} 
          />
          {/* Plant part */}
          <div className="absolute bottom-6 flex flex-col items-center">
            <div 
              className="w-1 bg-green-500/20 rounded-t-full" 
              style={{ height: `${10 + Math.random() * 20}px` }} 
            />
            <Leaf 
              size={10} 
              className="text-green-600/30" 
              style={{ transform: `rotate(${i % 2 === 0 ? 20 : -20}deg)` }} 
            />
          </div>
        </div>
      ))}
      
      <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-green-500/10 to-transparent" />
    </div>
  );
};
