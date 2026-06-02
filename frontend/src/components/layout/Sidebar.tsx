import React from 'react';
import { 
  Leaf, 
  Settings,
  Camera,
  X,
  Home,
  BarChart2,
  LogOut,
  Users
} from 'lucide-react';
import { cn } from '../../lib/utils';

interface SidebarProps {
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
  activeItem: string;
  setActiveItem: (item: string) => void;
  language: 'pt-BR' | 'en-US';
  role: 'admin' | 'user';
  onLogout: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, setIsOpen, activeItem, setActiveItem, language, role, onLogout }) => {
  const isEnglish = language === 'en-US';
  const baseMenuItems = [
    { icon: Home, value: 'Dashboard', label: isEnglish ? 'Dashboard' : 'Painel' },
    { icon: Leaf, value: 'My Plant', label: isEnglish ? 'My Plant' : 'Minha Planta' },
    { icon: Camera, value: 'Scan 3D', label: isEnglish ? 'Live Camera' : 'Camera ao Vivo' },
    { icon: BarChart2, value: 'Analytics', label: isEnglish ? 'Analytics' : 'Análises' },
  ];
  const adminMenuItems = [
    { icon: Users, value: 'Users', label: isEnglish ? 'Users' : 'Usuários' },
    { icon: Settings, value: 'Settings', label: isEnglish ? 'Settings' : 'Configurações' },
  ];
  const menuItems = role === 'admin' ? [...baseMenuItems, ...adminMenuItems] : baseMenuItems;

  const handleItemClick = (value: string) => {
    setActiveItem(value);
    if (window.innerWidth < 1024) {
      setIsOpen(false);
    }
  };

  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/20 dark:bg-black/55 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      <aside className={cn(
        "fixed inset-y-0 left-0 w-20 h-screen bg-white/40 dark:bg-slate-950/80 backdrop-blur-xl border-r border-slate-200/50 dark:border-slate-700/60 z-50 transition-transform duration-300 lg:sticky lg:top-0 lg:translate-x-0 lg:self-start flex flex-col items-center justify-between py-6",
        isOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="flex flex-col items-center">
          {/* Logo */}
          <div className="mb-10">
            <div className="w-10 h-10 bg-white dark:bg-slate-900 rounded-xl flex items-center justify-center shadow-sm border border-slate-100 dark:border-slate-700">
              <Leaf className="text-green-600 w-6 h-6" fill="currentColor" />
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex flex-col gap-5">
            {menuItems.map((item) => (
              <button
                key={item.value}
                onClick={() => handleItemClick(item.value)}
                className={cn(
                  "w-12 h-12 flex items-center justify-center rounded-2xl transition-all duration-300 group relative",
                  activeItem === item.value
                    ? "bg-white dark:bg-slate-800 text-green-600 shadow-sm border border-slate-100 dark:border-slate-700"
                    : "text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-100 hover:bg-white/50 dark:hover:bg-slate-800/80"
                )}
                title={item.label}
              >
                <item.icon className={cn("w-5 h-5 transition-colors", activeItem === item.value ? "text-green-600" : "text-slate-400 dark:text-slate-500 group-hover:text-slate-600 dark:group-hover:text-slate-100")} />

                {/* Tooltip for slim sidebar */}
                <span className="absolute left-16 bg-slate-800 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50">
                  {item.label}
                </span>
              </button>
            ))}
          </nav>
        </div>

        {/* Bottom Action */}
        <div className="group flex flex-col items-center gap-2">
          <button
            onClick={onLogout}
            className="w-12 h-12 flex items-center justify-center rounded-xl bg-gradient-to-br from-[#f3f8f4] to-[#e6efe8] dark:from-slate-800 dark:to-slate-900 text-[#4b5b53] dark:text-slate-200 border border-[#acb4b1]/20 dark:border-slate-700/60 transition-all duration-300 shadow-[0_8px_24px_rgba(45,52,50,0.12)] hover:from-red-500 hover:to-red-600 hover:text-white hover:border-red-400/60 hover:shadow-[0_14px_34px_rgba(239,68,68,0.32)] hover:-translate-y-0.5"
            title={isEnglish ? 'Sign out' : 'Sair da conta'}
            aria-label={isEnglish ? 'Sign out' : 'Sair da conta'}
          >
            <LogOut size={18} />
          </button>
          <span className="text-[10px] uppercase tracking-widest font-bold text-[#4b5b53] dark:text-slate-300 transition-colors duration-300 group-hover:text-red-600 dark:group-hover:text-red-300">
            {isEnglish ? 'Exit' : 'Sair'}
          </span>
        </div>

        {/* Mobile Close Button */}
        <button 
          onClick={() => setIsOpen(false)} 
          className="absolute top-4 right-[-40px] lg:hidden bg-white dark:bg-slate-900 p-2 rounded-r-xl border-y border-r border-slate-200 dark:border-slate-700 text-slate-400 dark:text-slate-300"
        >
          <X size={20} />
        </button>
      </aside>
    </>
  );
};

export default Sidebar;
