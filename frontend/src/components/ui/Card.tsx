import React from 'react';
import { cn } from '../../lib/utils';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
}

export const Card: React.FC<CardProps> = ({ children, className, title, subtitle }) => {
  return (
    <div className={cn("glass rounded-[32px] p-6 flex flex-col", className)}>
      {(title || subtitle) && (
        <div className="flex flex-col gap-0.5 mb-4">
          {title && (
            <h3 className="text-lg font-black text-slate-800 dark:text-slate-100 tracking-tight">
              {title}
            </h3>
          )}
          {subtitle && (
            <p className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest">
              {subtitle}
            </p>
          )}
        </div>
      )}
      {children}
    </div>
  );
};
