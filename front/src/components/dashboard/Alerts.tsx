import React from 'react';
import { AlertTriangle, Droplet } from 'lucide-react';
import { Card } from '../ui/Card';
import { cn } from '../../lib/utils';

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

export const Alerts: React.FC = () => {
  return (
    <Card title="Alertas" className="flex flex-col gap-3">
      <AlertItem 
        icon={Droplet} 
        title="Nivel de Agua Baixo" 
        message="Reabasteca o tanque em breve!" 
        color="red" 
      />
      <AlertItem 
        icon={AlertTriangle} 
        title="Deficiencia de Nutrientes" 
        message="Verifique os nutrientes do solo!" 
        color="orange" 
      />
    </Card>
  );
};
