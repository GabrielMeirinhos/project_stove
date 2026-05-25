import React from 'react';
import { 
  Leaf, 
  Settings,
  Camera,
  X,
  Home,
  BarChart2,
  LogOut
} from 'lucide-react';
import { cn } from '../../lib/utils';

interface SidebarProps {
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
  activeItem: string;
  setActiveItem: (item: string) => void;
  language: 'pt-BR' | 'en-US';
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, setIsOpen, activeItem, setActiveItem, language }) => {
  const isEnglish = language === 'en-US';
  const menuItems = [
    { icon: Home, value: 'Dashboard', label: isEnglish ? 'Dashboard' : 'Painel' },
    { icon: Leaf, value: 'My Plant', label: isEnglish ? 'My Plant' : 'Minha Planta' },
    { icon: Camera, value: 'Scan 3D', label: isEnglish ? 'Live Camera' : 'Camera ao Vivo' },
    { icon: BarChart2, value: 'Analytics', label: isEnglish ? 'Analytics' : 'Analises' },
    { icon: Settings, value: 'Settings', label: isEnglish ? 'Settings' : 'Configuracoes' },
  ];

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
        "fixed inset-y-0 left-0 w-20 bg-white/40 dark:bg-slate-950/80 backdrop-blur-xl border-r border-slate-200/50 dark:border-slate-700/60 z-50 transition-transform duration-300 lg:relative lg:translate-x-0 flex flex-col items-center py-8",
        isOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        {/* Logo */}
        <div className="mb-12">
          <div className="w-10 h-10 bg-white dark:bg-slate-900 rounded-xl flex items-center justify-center shadow-sm border border-slate-100 dark:border-slate-700">
            <Leaf className="text-green-600 w-6 h-6" fill="currentColor" />
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 flex flex-col gap-6">
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

        {/* Bottom Action */}
        <div className="mt-auto">
          <button className="w-12 h-12 flex items-center justify-center rounded-2xl text-slate-400 dark:text-slate-500 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/15 transition-all group relative">
            <LogOut size={20} />
            <span className="absolute left-16 bg-slate-800 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50">
              {isEnglish ? 'Exit' : 'Sair'}
            </span>
          </button>
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
