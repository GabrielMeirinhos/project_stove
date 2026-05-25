import React, { useEffect, useRef, useState } from 'react';
import { Search, Bell, Moon, Sun } from 'lucide-react';
import { cn } from '../../lib/utils';

interface HeaderNotification {
  id: string;
  title: string;
  description: string;
  time: string;
  severity: 'info' | 'warning' | 'success';
  unread?: boolean;
}

interface HeaderProps {
  activeTab?: string;
  onTabChange?: (tab: string) => void;
  theme: 'light' | 'dark';
  onToggleTheme: () => void;
  notifications?: HeaderNotification[];
  language: 'pt-BR' | 'en-US';
}

export const Header: React.FC<HeaderProps> = ({ activeTab = 'My Plant', onTabChange, theme, onToggleTheme, notifications = [], language }) => {
  const isEnglish = language === 'en-US';
  const tabs = [
    { value: 'Analytics', label: isEnglish ? 'Analytics' : 'Analises' },
    { value: 'My Plant', label: isEnglish ? 'My Plant' : 'Minha Planta' },
  ];
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const notificationPanelRef = useRef<HTMLDivElement>(null);
  const unreadCount = notifications.filter((item) => item.unread).length;

  useEffect(() => {
    const onPointerDown = (event: MouseEvent) => {
      if (!notificationPanelRef.current) {
        return;
      }

      if (!notificationPanelRef.current.contains(event.target as Node)) {
        setNotificationsOpen(false);
      }
    };

    document.addEventListener('mousedown', onPointerDown);
    return () => {
      document.removeEventListener('mousedown', onPointerDown);
    };
  }, []);

  const severityStyles = {
    info: 'bg-blue-500',
    warning: 'bg-amber-500',
    success: 'bg-green-500',
  } as const;

  return (
    <header className="h-16 flex items-center justify-between gap-8">
      {/* Tabs */}
      <div className="flex bg-white/50 dark:bg-slate-900/60 backdrop-blur-md p-1 rounded-2xl border border-slate-200/50 dark:border-slate-700/60 shadow-sm">
        {tabs.map((tab) => (
          <button
            key={tab.value}
            onClick={() => onTabChange?.(tab.value)}
            className={cn(
              "px-6 py-2 rounded-xl text-sm font-medium transition-all duration-300 flex items-center gap-2",
              activeTab === tab.value
                ? "bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 shadow-sm border border-slate-100 dark:border-slate-700" 
                : "text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-200"
            )}
          >
            {tab.value === 'My Plant' && <div className="w-2 h-2 rounded-full bg-green-500" />}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Search Bar */}
      <div className="flex-1 max-w-md relative group">
        <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none text-slate-400 dark:text-slate-500 group-focus-within:text-green-600 transition-colors">
          <Search size={18} />
        </div>
        <input 
          type="text" 
          placeholder={isEnglish ? 'Search...' : 'Buscar...'}
          className="w-full h-12 pl-12 pr-4 bg-white/50 dark:bg-slate-900/60 backdrop-blur-md border border-slate-200/50 dark:border-slate-700/60 rounded-2xl text-sm text-slate-700 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-green-500/20 focus:border-green-500/50 transition-all shadow-sm"
        />
      </div>

      {/* User Actions */}
      <div className="flex items-center gap-4">
        <button
          onClick={onToggleTheme}
          className="w-12 h-12 flex items-center justify-center rounded-2xl bg-white/50 backdrop-blur-md border border-slate-200/50 text-slate-500 hover:text-slate-700 dark:bg-slate-900/60 dark:border-slate-700/60 dark:text-slate-300 dark:hover:text-white transition-all shadow-sm"
          aria-label={theme === 'dark' ? (isEnglish ? 'Enable light mode' : 'Ativar modo claro') : (isEnglish ? 'Enable dark mode' : 'Ativar modo escuro')}
          title={theme === 'dark' ? (isEnglish ? 'Enable light mode' : 'Ativar modo claro') : (isEnglish ? 'Enable dark mode' : 'Ativar modo escuro')}
        >
          {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
        </button>

        <div className="relative" ref={notificationPanelRef}>
          <button
            onClick={() => setNotificationsOpen((open) => !open)}
            className="w-12 h-12 flex items-center justify-center rounded-2xl bg-white/50 dark:bg-slate-900/60 backdrop-blur-md border border-slate-200/50 dark:border-slate-700/60 text-slate-400 dark:text-slate-300 hover:text-slate-600 dark:hover:text-white transition-all shadow-sm relative"
            aria-label={isEnglish ? 'Open notifications' : 'Abrir notificacoes'}
            title={isEnglish ? 'Notifications' : 'Notificacoes'}
          >
            <Bell size={20} />
            {unreadCount > 0 && (
              <div className="absolute top-2 right-2 min-w-5 h-5 px-1 rounded-full bg-green-500 text-white text-[10px] font-bold flex items-center justify-center border-2 border-white dark:border-slate-900">
                {unreadCount > 9 ? '9+' : unreadCount}
              </div>
            )}
          </button>

          {notificationsOpen && (
            <div className="absolute right-0 mt-3 w-80 max-h-[360px] overflow-y-auto glass rounded-2xl p-3 z-[70]">
              <div className="flex items-center justify-between px-2 py-1">
                <h3 className="text-xs font-black tracking-widest uppercase text-slate-700 dark:text-slate-200">{isEnglish ? 'Notifications' : 'Notificacoes'}</h3>
                <span className="text-[10px] font-bold text-slate-500 dark:text-slate-400">{unreadCount} {isEnglish ? 'unread' : 'nao lidas'}</span>
              </div>

              <div className="mt-2 flex flex-col gap-2">
                {notifications.length === 0 ? (
                  <div className="rounded-xl border border-slate-100 dark:border-slate-700 bg-white/60 dark:bg-slate-900/60 px-3 py-4 text-center text-xs font-medium text-slate-500 dark:text-slate-400">
                    {isEnglish ? 'No notifications right now.' : 'Nenhuma notificacao no momento.'}
                  </div>
                ) : (
                  notifications.map((item) => (
                    <div
                      key={item.id}
                      className="rounded-xl border border-slate-100 dark:border-slate-700 bg-white/70 dark:bg-slate-900/60 p-3"
                    >
                      <div className="flex items-start gap-2">
                        <div className={cn('mt-1 w-2 h-2 rounded-full', severityStyles[item.severity])} />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2">
                            <p className="text-xs font-bold text-slate-800 dark:text-slate-100 truncate">{item.title}</p>
                            <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 whitespace-nowrap">{item.time}</span>
                          </div>
                          <p className="text-[11px] text-slate-600 dark:text-slate-300 mt-1 leading-relaxed">{item.description}</p>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
        
        <div className="w-12 h-12 rounded-2xl overflow-hidden border-2 border-white dark:border-slate-700 shadow-md cursor-pointer hover:scale-105 transition-transform">
          <img 
            src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix" 
            alt={isEnglish ? 'User profile' : 'Perfil do usuario'}
            className="w-full h-full object-cover bg-slate-100 dark:bg-slate-800"
          />
        </div>
      </div>
    </header>
  );
};
