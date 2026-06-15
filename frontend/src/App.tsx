import React, { useEffect, useState } from 'react';
import { Header } from './components/dashboard/Header';
import { CurrentStatus } from './components/dashboard/CurrentStatus';
import { GrowthChart } from './components/dashboard/GrowthChart';
import { PlantView } from './components/dashboard/PlantView';
import { Timeline } from './components/dashboard/Timeline';
import { MiniVisual } from './components/dashboard/MiniVisual';
import { Alerts } from './components/dashboard/Alerts';
import { EnvironmentalData } from './components/dashboard/EnvironmentalData';
import { RecentActivity } from './components/dashboard/RecentActivity';
import { ScanView } from './components/dashboard/ScanView';
import Charts from './components/dashboard/Charts';
import Sidebar from './components/layout/Sidebar';
import { LoginScreen } from './components/auth/LoginScreen';
import { Menu } from 'lucide-react';
import { api, AuthUser, AdminOverview, RealtimeSubscription } from './services/api';
import { HistoryData, MqttStatus, PlantStatusPayload, SensorData } from './types';
import { toast } from 'sonner';
import { mapPlantStatusToSensor } from './services/api';

type ThemeMode = 'light' | 'dark';
type AppLanguage = 'pt-BR' | 'en-US';
type HeaderNotificationSeverity = 'info' | 'warning' | 'success';

type HeaderNotification = {
  id: string;
  title: string;
  description: string;
  time: string;
  severity: HeaderNotificationSeverity;
  unread?: boolean;
};

const clampValue = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value));

const generateMockSensor = (step: number): SensorData => {
  const now = new Date();
  const moisture = clampValue(56 + Math.sin(step / 3) * 10 + Math.cos(step / 5) * 4, 30, 82);
  const temperature = clampValue(24 + Math.sin(step / 4) * 2.4 + Math.cos(step / 6) * 1.2, 18, 33);
  const luminosity = clampValue(860 + Math.sin(step / 2.8) * 240, 250, 1400);
  const health = clampValue(84 + Math.sin(step / 6) * 8 + Math.cos(step / 7) * 4, 60, 99);

  return {
    moisture: Number(moisture.toFixed(1)),
    temperature: Number(temperature.toFixed(1)),
    luminosity: Number(luminosity.toFixed(0)),
    health: Number(health.toFixed(1)),
    timestamp: now.toISOString(),
    source: 'mock',
    topic: 'demo/plant/sensors',
    connected: true,
  };
};

const generateMockHistory = (step: number): HistoryData[] => {
  return Array.from({ length: 7 }, (_, index) => {
    const trend = step + index;
    return {
      day: `Dia ${index + 1}`,
      growth: clampValue(32 + index * 7 + Math.sin(trend / 2) * 4, 20, 98),
      moisture: clampValue(50 + Math.cos(trend / 2.4) * 12, 30, 85),
      health: clampValue(75 + index * 2 + Math.sin(trend / 3) * 6, 58, 100),
    };
  }).map((item) => ({
    day: item.day,
    growth: Number(item.growth.toFixed(0)),
    moisture: Number(item.moisture.toFixed(0)),
    health: Number(item.health.toFixed(0)),
  }));
};

export default function App() {
  const getStoredToken = () => {
    if (typeof window === 'undefined') {
      return null;
    }
    return window.localStorage.getItem('gaia-auth-token') || window.sessionStorage.getItem('gaia-auth-token');
  };

  const getStoredUser = (): AuthUser | null => {
    if (typeof window === 'undefined') {
      return null;
    }

    const rawUser = window.localStorage.getItem('gaia-auth-user') || window.sessionStorage.getItem('gaia-auth-user');
    if (!rawUser) {
      return null;
    }

    try {
      return JSON.parse(rawUser) as AuthUser;
    } catch {
      return null;
    }
  };

  const [day, setDay] = useState(20);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeView, setActiveView] = useState('Dashboard');
  const [activeTab, setActiveTab] = useState('My Plant');
  const [authToken, setAuthToken] = useState<string | null>(() => getStoredToken());
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(() => getStoredUser());
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => Boolean(getStoredToken()));
  const [persistAuth, setPersistAuth] = useState<boolean>(() => {
    if (typeof window === 'undefined') {
      return false;
    }

    return Boolean(window.localStorage.getItem('gaia-auth-token'));
  });
  const [language, setLanguage] = useState<AppLanguage>(() => {
    if (typeof window === 'undefined') {
      return 'pt-BR';
    }

    const storedLanguage = window.localStorage.getItem('gaia-language');
    if (storedLanguage === 'pt-BR' || storedLanguage === 'en-US') {
      return storedLanguage;
    }

    return 'pt-BR';
  });
  const [theme, setTheme] = useState<ThemeMode>(() => {
    if (typeof window === 'undefined') {
      return 'light';
    }

    const storedTheme = window.localStorage.getItem('gaia-theme');
    if (storedTheme === 'light' || storedTheme === 'dark') {
      return storedTheme;
    }

    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });
  const [sensorData, setSensorData] = useState<SensorData | null>(null);
  const [mqttStatus, setMqttStatus] = useState<MqttStatus | null>(null);
  const [plantStatus, setPlantStatus] = useState<PlantStatusPayload | null>(null);
  const [plantAlert, setPlantAlert] = useState<string | null>(null);
  const [historyData, setHistoryData] = useState<HistoryData[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [adminUsers, setAdminUsers] = useState<AuthUser[]>([]);
  const [adminOverview, setAdminOverview] = useState<AdminOverview | null>(null);
  const [adminLoading, setAdminLoading] = useState(false);
  const [demoMode, setDemoMode] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    return window.localStorage.getItem('gaia-demo-mode') === 'on';
  });
  const isEnglish = language === 'en-US';

  useEffect(() => {
    try {
      if (isAuthenticated && persistAuth && authToken && currentUser) {
        window.localStorage.setItem('gaia-auth-token', authToken);
        window.localStorage.setItem('gaia-auth-user', JSON.stringify(currentUser));
        window.sessionStorage.removeItem('gaia-auth-token');
        window.sessionStorage.removeItem('gaia-auth-user');
        return;
      }

      if (isAuthenticated && authToken && currentUser) {
        window.sessionStorage.setItem('gaia-auth-token', authToken);
        window.sessionStorage.setItem('gaia-auth-user', JSON.stringify(currentUser));
        window.localStorage.removeItem('gaia-auth-token');
        window.localStorage.removeItem('gaia-auth-user');
        return;
      }

      window.localStorage.removeItem('gaia-auth-token');
      window.localStorage.removeItem('gaia-auth-user');
      window.sessionStorage.removeItem('gaia-auth-token');
      window.sessionStorage.removeItem('gaia-auth-user');
    } catch {
      // ignore
    }
  }, [authToken, currentUser, isAuthenticated, persistAuth]);

  useEffect(() => {
    if (!authToken) {
      return;
    }

    let isMounted = true;
    (async () => {
      try {
        const user = await api.authMe(authToken);
        if (!isMounted) return;
        setCurrentUser(user);
        setIsAuthenticated(true);
      } catch {
        if (!isMounted) return;
        setAuthToken(null);
        setCurrentUser(null);
        setIsAuthenticated(false);
      }
    })();

    return () => {
      isMounted = false;
    };
  }, [authToken]);

  useEffect(() => {
    let isMounted = true;

    if (demoMode || !isAuthenticated) {
      // when demoMode is active we don't subscribe to real stream
      return () => {
        isMounted = false;
      };
    }

    const hydrateInitialState = async () => {
      try {
        const [initialSensors, initialStatus] = await Promise.all([
          api.getSensors(),
          api.getMqttStatus(),
        ]);

        if (!isMounted) return;

        setSensorData(initialSensors);
        setMqttStatus(initialStatus);
      } catch {
        if (isMounted) {
          setSensorData(null);
          setMqttStatus(null);
        }
      }
    };

    // Stream SSE com discriminador de tipo (status vs alerta)
    let liveStream: RealtimeSubscription | null = null;

    const handleStatusUpdate = (payload: PlantStatusPayload) => {
      if (!isMounted) return;
      setPlantStatus(payload);
      setSensorData(mapPlantStatusToSensor(payload));
      setMqttStatus((current) => 
        current 
          ? { ...current, connected: true, lastMessageAt: new Date().toISOString(), subscribedTopic: 'planta/status' }
          : {
              connected: true,
              brokerUrl: 'mqtt://hivemq-cloud',
              subscribedTopic: 'planta/status',
              lastMessageAt: new Date().toISOString(),
            }
      );
    };

    const handleAlertUpdate = (message: string) => {
      if (!isMounted) return;
      setPlantAlert(message);
      toast.error(message, {
        description: isEnglish ? 'Critical plant alert received in real time.' : 'Alerta crítico da planta recebido em tempo real.',
      });
    };

    liveStream = api.subscribeLiveStream(handleStatusUpdate, handleAlertUpdate);

    void hydrateInitialState();

    return () => {
      isMounted = false;
      liveStream?.close();
    };
  }, [demoMode, isAuthenticated, isEnglish]);

  useEffect(() => {
    let isMounted = true;
    const loadHistory = async () => {
      setHistoryLoading(true);
      if (!isAuthenticated) {
        setHistoryLoading(false);
        return;
      }
      try {
        if (demoMode) {
          // demo mode will populate history separately
          return;
        }
        const history = await api.getHistory(authToken ?? undefined);
        if (!isMounted) return;
        setHistoryData(history);
      } catch {
        if (isMounted) setHistoryData([]);
      } finally {
        if (isMounted) setHistoryLoading(false);
      }
    };

    void loadHistory();

    return () => {
      isMounted = false;
    };
  }, [demoMode, isAuthenticated]);

  useEffect(() => {
    // persist demo mode preference
    try {
      window.localStorage.setItem('gaia-demo-mode', demoMode ? 'on' : 'off');
    } catch {
      // ignore
    }
  }, [demoMode]);

  useEffect(() => {
    let tick = 0;
    let intervalId: number | undefined;

    const applyMockData = () => {
      const mockSensor = generateMockSensor(tick);
      const mockHistory = generateMockHistory(tick);

      setSensorData(mockSensor);
      setMqttStatus({
        connected: true,
        brokerUrl: 'mock://gaia-demo',
        subscribedTopic: 'demo/plant/#',
        lastMessageAt: mockSensor.timestamp,
      });
      setHistoryData(mockHistory);
      setHistoryLoading(false);
      tick += 1;
    };

    if (demoMode || !isAuthenticated) {
      applyMockData();
      intervalId = window.setInterval(applyMockData, 5000) as unknown as number;
    } else {
      // when disabling demo, reload real data
      (async () => {
        try {
          const [initialSensors, initialStatus, history] = await Promise.all([
            api.getSensors(),
            api.getMqttStatus(),
            api.getHistory(authToken ?? undefined),
          ]);
          setSensorData(initialSensors);
          setMqttStatus(initialStatus);
          setHistoryData(history);
        } catch {
          setSensorData(null);
          setMqttStatus(null);
          setHistoryData([]);
        }
      })();
    }

    return () => {
      if (intervalId) window.clearInterval(intervalId);
    };
  }, [demoMode, isAuthenticated]);

  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle('dark', theme === 'dark');
    root.style.colorScheme = theme;
    window.localStorage.setItem('gaia-theme', theme);
  }, [theme]);

  useEffect(() => {
    window.localStorage.setItem('gaia-language', language);
  }, [language]);

  const toggleTheme = () => {
    setTheme((currentTheme) => (currentTheme === 'light' ? 'dark' : 'light'));
  };

  useEffect(() => {
    if (currentUser?.role !== 'admin' && ['Settings', 'Users'].includes(activeView)) {
      setActiveView('Dashboard');
    }

    if (activeView === 'Analytics') {
      setActiveTab('Analytics');
      return;
    }

    if (activeView === 'Dashboard' || activeView === 'My Plant') {
      setActiveTab('My Plant');
    }
  }, [activeView]);

  const handleHeaderTabChange = (tab: string) => {
    setActiveTab(tab);
    if (tab === 'Analytics') {
      setActiveView('Analytics');
      return;
    }
    if (tab === 'My Plant') {
      setActiveView('My Plant');
    }
  };

  const handleLogin = async ({ email, password, rememberMe }: { email: string; password: string; rememberMe: boolean }) => {
    const response = await api.authLogin(email, password);

    setAuthToken(response.access_token);
    setCurrentUser(response.user);
    setPersistAuth(rememberMe);
    setIsAuthenticated(true);
    setSidebarOpen(false);
    setActiveView('Dashboard');
    setActiveTab('My Plant');
  };

  const handleLogout = () => {
    setAuthToken(null);
    setCurrentUser(null);
    setAdminUsers([]);
    setAdminOverview(null);
    setPersistAuth(false);
    setIsAuthenticated(false);
    setSidebarOpen(false);
    setActiveView('Dashboard');
    setActiveTab('My Plant');
  };

  useEffect(() => {
    if (!isAuthenticated || currentUser?.role !== 'admin' || !authToken) {
      setAdminUsers([]);
      setAdminOverview(null);
      return;
    }

    let isMounted = true;
    setAdminLoading(true);

    (async () => {
      try {
        const [users, overview] = await Promise.all([
          api.adminUsers(authToken),
          api.adminOverview(authToken),
        ]);

        if (!isMounted) return;
        setAdminUsers(users);
        setAdminOverview(overview);
      } catch {
        if (!isMounted) return;
        setAdminUsers([]);
        setAdminOverview(null);
      } finally {
        if (isMounted) {
          setAdminLoading(false);
        }
      }
    })();

    return () => {
      isMounted = false;
    };
  }, [authToken, currentUser?.role, isAuthenticated]);

  const getViewLabel = (view: string) => {
    if (view === 'Dashboard') return isEnglish ? 'Dashboard' : 'Painel';
    if (view === 'My Plant') return isEnglish ? 'My Plant' : 'Minha Planta';
    if (view === 'Scan 3D') return isEnglish ? 'Live Camera' : 'Camera ao Vivo';
    if (view === 'Analytics') return isEnglish ? 'Analytics' : 'Análises';
    if (view === 'Users') return isEnglish ? 'Users' : 'Usuários';
    if (view === 'Settings') return isEnglish ? 'Settings' : 'Configurações';
    return view;
  };

  const lastUpdatedAt = sensorData?.timestamp
    ? new Date(sensorData.timestamp).toLocaleTimeString(language, { hour: '2-digit', minute: '2-digit' })
    : '--:--';

  const avgGrowth = historyData.length
    ? Math.round(historyData.reduce((sum, item) => sum + item.growth, 0) / historyData.length)
    : 0;
  const avgMoisture = historyData.length
    ? Math.round(historyData.reduce((sum, item) => sum + item.moisture, 0) / historyData.length)
    : 0;
  const avgHealth = historyData.length
    ? Math.round(historyData.reduce((sum, item) => sum + item.health, 0) / historyData.length)
    : 0;

  const getPlantStage = (currentDay: number) => {
    if (currentDay <= 5) return isEnglish ? 'Germination' : 'Germinacao';
    if (currentDay <= 10) return isEnglish ? 'Early development' : 'Desenvolvimento inicial';
    if (currentDay <= 15) return isEnglish ? 'Accelerated growth' : 'Crescimento acelerado';
    return isEnglish ? 'Consolidation stage' : 'Fase de consolidacao';
  };

  const plantStage = getPlantStage(day);
  const isPumpOn = plantStatus?.bomba === 'ligada';
  const notifications: HeaderNotification[] = [
    {
      id: 'mqtt-status',
      title: mqttStatus?.connected ? (isEnglish ? 'MQTT feed active' : 'Feed MQTT ativo') : (isEnglish ? 'MQTT feed disconnected' : 'Feed MQTT desconectado'),
      description: mqttStatus?.connected
        ? isEnglish
          ? `Receiving real-time readings. Last update at ${lastUpdatedAt}.`
          : `Recebendo leituras em tempo real. Ultima atualizacao as ${lastUpdatedAt}.`
        : isEnglish
          ? 'No broker connection. Check network and credentials to resume readings.'
          : 'Sem conexão com o broker. Verifique rede e credenciais para retomar leituras.',
      time: lastUpdatedAt,
      severity: mqttStatus?.connected ? 'success' : 'warning',
      unread: !mqttStatus?.connected,
    },
    {
      id: 'soil-moisture',
      title: isEnglish ? 'Soil moisture' : 'Umidade do solo',
      description: sensorData
        ? isEnglish
          ? `Current moisture at ${Math.round(sensorData.moisture)}%. Recommended range: 45% to 65%.`
          : `Umidade atual em ${Math.round(sensorData.moisture)}%. Faixa recomendada: 45% a 65%.`
        : isEnglish
          ? 'Waiting for soil moisture reading.'
          : 'Aguardando leitura de umidade do solo.',
      time: lastUpdatedAt,
      severity: sensorData && (sensorData.moisture < 35 || sensorData.moisture > 75) ? 'warning' : 'info',
      unread: Boolean(sensorData && (sensorData.moisture < 35 || sensorData.moisture > 75)),
    },
    {
      id: 'plant-health',
      title: isEnglish ? 'Plant health' : 'Saude da planta',
      description: sensorData
        ? isEnglish
          ? `Current index at ${Math.round(sensorData.health)}%. Recent average trend: ${avgHealth}%.`
          : `Indice atual em ${Math.round(sensorData.health)}%. Tendencia media recente: ${avgHealth}%.`
        : isEnglish
          ? 'No health data at the moment.'
          : 'Sem dados de saúde no momento.',
      time: lastUpdatedAt,
          severity: sensorData && sensorData.health < 70 ? 'warning' : 'success',
      unread: Boolean(sensorData && sensorData.health < 70),
    },
  ];

  if (!isAuthenticated) {
    return (
      <LoginScreen
        language={language}
        theme={theme}
        onToggleTheme={toggleTheme}
        onLogin={handleLogin}
      />
    );
  }

  return (
    <div className="flex min-h-screen bg-[#fdfcfb] dark:bg-slate-950 transition-colors duration-500">
      <Sidebar 
        isOpen={sidebarOpen} 
        setIsOpen={setSidebarOpen} 
        activeItem={activeView}
        setActiveItem={setActiveView}
        language={language}
        role={currentUser?.role ?? 'user'}
        onLogout={handleLogout}
      />
      
      <div className="flex-1 flex flex-col p-4 sm:p-6 lg:p-10 gap-8 max-w-[1600px] mx-auto overflow-x-hidden">
        <header className="flex items-center gap-4">
          <button 
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden p-2 glass rounded-xl text-slate-500 hover:text-slate-800 dark:text-slate-300 dark:hover:text-white"
          >
            <Menu size={24} />
          </button>
          <div className="flex-1">
            <Header
              activeTab={activeTab}
              onTabChange={handleHeaderTabChange}
              theme={theme}
              onToggleTheme={toggleTheme}
              notifications={notifications}
              language={language}
            />
          </div>
        </header>
        
        {activeView === 'Dashboard' ? (
          <main className="grid grid-cols-1 lg:grid-cols-12 gap-8 flex-1">
            <div className="lg:col-span-8 flex flex-col gap-8">
              <div className="glass rounded-[32px] p-6">
                <h2 className="text-4xl font-black text-slate-800 dark:text-slate-100 tracking-tight">{isEnglish ? 'Operational Dashboard' : 'Painel Operacional'}</h2>
                <p className="text-slate-500 dark:text-slate-300 text-sm font-medium mt-1">{isEnglish ? 'Fast monitoring for immediate decision-making about plant status.' : 'Monitoramento rapido para decisao imediata sobre o estado da planta.'}</p>

                <div className="mt-4 inline-flex items-center gap-2 rounded-full px-3 py-1 bg-emerald-100 dark:bg-emerald-500/15 border border-emerald-300/70 dark:border-emerald-500/30 text-emerald-700 dark:text-emerald-300 text-[10px] font-bold uppercase tracking-widest">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  {isEnglish ? 'Live mode' : 'Modo ao vivo'}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mt-6">
                  <div className="rounded-2xl border border-slate-100 dark:border-slate-700 bg-white/70 dark:bg-slate-900/60 p-4">
                    <p className="text-[10px] uppercase tracking-widest font-bold text-slate-500 dark:text-slate-400">{isEnglish ? 'MQTT Connection' : 'Conexao MQTT'}</p>
                    <p className="text-xl font-black text-slate-800 dark:text-slate-100 mt-2">
                      {mqttStatus?.connected ? 'Online' : 'Offline'}
                    </p>
                  </div>
                  <div className="rounded-2xl border border-slate-100 dark:border-slate-700 bg-white/70 dark:bg-slate-900/60 p-4">
                    <p className="text-[10px] uppercase tracking-widest font-bold text-slate-500 dark:text-slate-400">{isEnglish ? 'Current Temperature' : 'Temperatura Atual'}</p>
                    <p className="text-xl font-black text-slate-800 dark:text-slate-100 mt-2">
                      {sensorData ? `${sensorData.temperature.toFixed(1)}°C` : '--'}
                    </p>
                  </div>
                  <div className="rounded-2xl border border-slate-100 dark:border-slate-700 bg-white/70 dark:bg-slate-900/60 p-4">
                    <p className="text-[10px] uppercase tracking-widest font-bold text-slate-500 dark:text-slate-400">{isEnglish ? 'Soil Moisture' : 'Umidade do Solo'}</p>
                    <p className="text-xl font-black text-slate-800 dark:text-slate-100 mt-2">
                      {sensorData ? `${Math.round(sensorData.moisture)}%` : '--'}
                    </p>
                  </div>
                  <div className="rounded-2xl border border-slate-100 dark:border-slate-700 bg-white/70 dark:bg-slate-900/60 p-4">
                    <p className="text-[10px] uppercase tracking-widest font-bold text-slate-500 dark:text-slate-400">{isEnglish ? 'Plant Health' : 'Saude da Planta'}</p>
                    <p className="text-xl font-black text-slate-800 dark:text-slate-100 mt-2">
                      {sensorData ? `${Math.round(sensorData.health)}%` : '--'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <CurrentStatus data={sensorData} mqttStatus={mqttStatus} language={language} />
                <Alerts data={sensorData} language={language} />
              </div>

              <div className="glass rounded-[32px] p-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h3 className="text-xl font-black text-slate-800 dark:text-slate-100">{isEnglish ? 'Quick Actions' : 'Acoes Rapidas'}</h3>
                  <p className="text-slate-500 dark:text-slate-300 text-sm mt-1">{isEnglish ? `Last sensor update at ${lastUpdatedAt}. Open live camera for a new visual check.` : `Ultima atualizacao de sensores as ${lastUpdatedAt}. Abra a camera para nova coleta visual.`}</p>
                </div>
                <button
                  onClick={() => setActiveView('Scan 3D')}
                  className="px-5 py-3 rounded-xl bg-green-600 hover:bg-green-500 text-white font-bold text-sm transition-all shadow-lg shadow-green-600/20"
                >
                  {isEnglish ? 'Open Live Camera' : 'Abrir Camera ao Vivo'}
                </button>
              </div>
            </div>

            <div className="lg:col-span-4 flex flex-col gap-8">
              <GrowthChart data={historyData} language={language} />
              <EnvironmentalData data={sensorData} language={language} />
              <RecentActivity
                data={sensorData}
                mqttStatus={mqttStatus}
                language={language}
                historyAverage={historyData.length ? {
                  growth: avgGrowth,
                  moisture: avgMoisture,
                  health: avgHealth,
                } : undefined}
              />
            </div>
          </main>
        ) : activeView === 'My Plant' ? (
          <main className="grid grid-cols-1 lg:grid-cols-12 gap-10 flex-1">
            <div className="lg:col-span-8 flex flex-col gap-10">
              <div className="flex flex-col gap-1">
                <h2 className="text-5xl font-black text-slate-800 dark:text-slate-100 tracking-tight">{isEnglish ? 'Gaia Plant' : 'Planta Gaia'}</h2>
                <p className="text-slate-500 dark:text-slate-300 font-medium text-lg">{isEnglish ? 'Detailed monitoring of plant evolution across each growth phase.' : 'Acompanhamento detalhado da evolucao da planta em cada fase de crescimento.'}</p>
              </div>

              {plantAlert && (
                <div className="glass rounded-[28px] border border-amber-200 dark:border-amber-500/30 bg-amber-50/80 dark:bg-amber-500/10 px-5 py-4 flex items-start justify-between gap-4">
                  <div>
                    <p className="text-[10px] uppercase tracking-widest font-black text-amber-700 dark:text-amber-300">{isEnglish ? 'Critical alert' : 'Alerta crítico'}</p>
                    <p className="text-sm font-semibold text-amber-900 dark:text-amber-100 mt-1">{plantAlert}</p>
                  </div>
                  <button
                    onClick={() => setPlantAlert(null)}
                    className="text-xs font-black uppercase tracking-widest text-amber-700 dark:text-amber-300"
                  >
                    {isEnglish ? 'Dismiss' : 'Fechar'}
                  </button>
                </div>
              )}

              {plantStatus && (
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="rounded-2xl border border-slate-100 dark:border-slate-700 bg-white/70 dark:bg-slate-900/60 p-4">
                    <p className="text-[10px] uppercase tracking-widest font-bold text-slate-500 dark:text-slate-400">{isEnglish ? 'Soil moisture' : 'Umidade do solo'}</p>
                    <p className="text-xl font-black text-slate-800 dark:text-slate-100 mt-2">{Math.round(plantStatus.solo_umi)}%</p>
                  </div>
                  <div className="rounded-2xl border border-slate-100 dark:border-slate-700 bg-white/70 dark:bg-slate-900/60 p-4">
                    <p className="text-[10px] uppercase tracking-widest font-bold text-slate-500 dark:text-slate-400">{isEnglish ? 'Irrigation' : 'Irrigação'}</p>
                    <p className={`text-xl font-black mt-2 ${isPumpOn ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-800 dark:text-slate-100'}`}>
                      {isPumpOn ? (isEnglish ? 'On' : 'Ligada') : (isEnglish ? 'Off' : 'Desligada')}
                    </p>
                  </div>
                  <div className="rounded-2xl border border-slate-100 dark:border-slate-700 bg-white/70 dark:bg-slate-900/60 p-4">
                    <p className="text-[10px] uppercase tracking-widest font-bold text-slate-500 dark:text-slate-400">{isEnglish ? 'Stability' : 'Estabilidade'}</p>
                    <p className={`text-xl font-black mt-2 ${plantStatus.estabilizado ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-300'}`}>
                      {plantStatus.estabilizado ? (isEnglish ? 'Stable' : 'Estável') : (isEnglish ? 'Adjusting' : 'Ajustando')}
                    </p>
                  </div>
                </div>
              )}

              <div className="flex-1 min-h-[500px] relative flex items-center justify-center bg-white/20 dark:bg-slate-900/60 rounded-[60px] border border-white/40 dark:border-slate-700/40 shadow-sm">
                <div className="absolute inset-0 bg-gradient-to-b from-green-500/5 dark:from-green-400/10 to-transparent rounded-[60px] pointer-events-none" />
                <PlantView day={day} />
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <Timeline day={day} setDay={setDay} language={language} />
                <MiniVisual />
              </div>

              <div className="glass rounded-[32px] p-6">
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                  <div>
                    <h3 className="text-xl font-black text-slate-800 dark:text-slate-100">{isEnglish ? 'Plant Diary' : 'Diario da Planta'}</h3>
                    <p className="text-slate-500 dark:text-slate-300 text-sm mt-1">{isEnglish ? `Day ${day}` : `Dia ${day}`} // {plantStage}</p>
                  </div>
                  <span className="text-[10px] uppercase tracking-widest font-bold text-slate-500 dark:text-slate-400">{isEnglish ? `Updated at ${lastUpdatedAt}` : `Atualizado as ${lastUpdatedAt}`}</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-5">
                  <div className="rounded-2xl border border-slate-100 dark:border-slate-700 bg-white/70 dark:bg-slate-900/60 p-4">
                    <p className="text-[10px] uppercase tracking-widest font-bold text-slate-500 dark:text-slate-400">{isEnglish ? 'Weekly Goal' : 'Meta da Semana'}</p>
                    <p className="text-sm font-semibold text-slate-800 dark:text-slate-100 mt-2">{isEnglish ? 'Keep moisture between 45% and 65% to maintain stable development.' : 'Manter umidade entre 45% e 65% para estabilidade no desenvolvimento.'}</p>
                  </div>
                  <div className="rounded-2xl border border-slate-100 dark:border-slate-700 bg-white/70 dark:bg-slate-900/60 p-4">
                    <p className="text-[10px] uppercase tracking-widest font-bold text-slate-500 dark:text-slate-400">{isEnglish ? 'Current Observation' : 'Observacao Atual'}</p>
                    <p className="text-sm font-semibold text-slate-800 dark:text-slate-100 mt-2">
                      {sensorData
                        ? isEnglish
                          ? `Health at ${Math.round(sensorData.health)}% with temperature at ${sensorData.temperature.toFixed(1)}°C.`
                          : `Saude em ${Math.round(sensorData.health)}% com temperatura de ${sensorData.temperature.toFixed(1)}°C.`
                        : isEnglish
                          ? 'No sensor data available at the moment.'
                          : 'Sem dados de sensores no momento.'}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="lg:col-span-4 flex flex-col gap-8">
              <GrowthChart data={historyData} language={language} />
              <CurrentStatus data={sensorData} mqttStatus={mqttStatus} language={language} />
              <RecentActivity
                data={sensorData}
                mqttStatus={mqttStatus}
                language={language}
                historyAverage={historyData.length ? {
                  growth: avgGrowth,
                  moisture: avgMoisture,
                  health: avgHealth,
                } : undefined}
              />
            </div>
          </main>
        ) : activeView === 'Analytics' ? (
          <main className="grid grid-cols-1 lg:grid-cols-12 gap-8 flex-1">
            <div className="lg:col-span-8 flex flex-col gap-8">
              <div className="glass rounded-[32px] p-6">
                <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
                  <div>
                    <h2 className="text-4xl font-black text-slate-800 dark:text-slate-100 tracking-tight">{isEnglish ? 'Plant Analytics' : 'Analises da Planta'}</h2>
                    <p className="text-slate-500 dark:text-slate-300 text-sm font-medium">{isEnglish ? 'Consolidated readings, history and recent plant behavior.' : 'Leituras consolidadas, historico e comportamento recente da planta.'}</p>
                  </div>
                  <span className="text-xs font-bold uppercase tracking-widest text-slate-500 dark:text-slate-400">{isEnglish ? `Updated at ${lastUpdatedAt}` : `Atualizado as ${lastUpdatedAt}`}</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6">
                  <div className="rounded-2xl border border-slate-100 dark:border-slate-700 bg-white/70 dark:bg-slate-900/60 p-4">
                    <p className="text-[10px] uppercase tracking-widest font-bold text-slate-500 dark:text-slate-400">{isEnglish ? 'Average Growth' : 'Crescimento Medio'}</p>
                    <p className="text-2xl font-black text-slate-800 dark:text-slate-100 mt-2">{historyData.length ? `${avgGrowth}%` : '--'}</p>
                  </div>
                  <div className="rounded-2xl border border-slate-100 dark:border-slate-700 bg-white/70 dark:bg-slate-900/60 p-4">
                    <p className="text-[10px] uppercase tracking-widest font-bold text-slate-500 dark:text-slate-400">{isEnglish ? 'Average Moisture' : 'Umidade Media'}</p>
                    <p className="text-2xl font-black text-slate-800 dark:text-slate-100 mt-2">{historyData.length ? `${avgMoisture}%` : '--'}</p>
                  </div>
                  <div className="rounded-2xl border border-slate-100 dark:border-slate-700 bg-white/70 dark:bg-slate-900/60 p-4">
                    <p className="text-[10px] uppercase tracking-widest font-bold text-slate-500 dark:text-slate-400">{isEnglish ? 'Average Health' : 'Saude Media'}</p>
                    <p className="text-2xl font-black text-slate-800 dark:text-slate-100 mt-2">{historyData.length ? `${avgHealth}%` : '--'}</p>
                  </div>
                </div>
              </div>

              <div className="glass rounded-[32px] p-6 min-h-[360px]">
                {historyLoading ? (
                  <div className="h-full min-h-[300px] flex items-center justify-center text-sm font-medium text-slate-500 dark:text-slate-400">
                    {isEnglish ? 'Loading analytics history...' : 'Carregando historico de analises...'}
                  </div>
                ) : historyData.length > 0 ? (
                  <Charts data={historyData} language={language} />
                ) : (
                  <div className="h-full min-h-[300px] flex items-center justify-center text-sm font-medium text-slate-500 dark:text-slate-400">
                    {isEnglish ? 'No historical data available right now.' : 'Nenhum dado historico disponivel no momento.'}
                  </div>
                )}
              </div>

              <EnvironmentalData data={sensorData} language={language} />
            </div>

            <div className="lg:col-span-4 flex flex-col gap-8">
              <CurrentStatus data={sensorData} mqttStatus={mqttStatus} language={language} />
              <GrowthChart data={historyData} language={language} />
              <Alerts data={sensorData} language={language} />
            </div>
          </main>
        ) : activeView === 'Scan 3D' ? (
          <div className="flex-1">
            <ScanView language={language} />
          </div>
        ) : activeView === 'Users' ? (
          <main className="glass rounded-[32px] p-6 flex-1">
            <div className="flex items-center justify-between gap-4 mb-6">
              <div>
                <h2 className="text-3xl font-black text-slate-800 dark:text-slate-100 tracking-tight">{isEnglish ? 'System Users' : 'Usuários do Sistema'}</h2>
                <p className="text-slate-500 dark:text-slate-300 text-sm mt-1">
                  {isEnglish ? 'Admin-only access to users and account metrics.' : 'Acesso exclusivo de admin para usuários e métricas de conta.'}
                </p>
              </div>
              <div className="text-xs uppercase tracking-widest font-bold text-slate-500 dark:text-slate-400">
                {isEnglish ? 'Admin view' : 'Visão admin'}
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
              <div className="rounded-2xl border border-slate-100 dark:border-slate-700 bg-white/70 dark:bg-slate-900/60 p-4">
                <p className="text-[10px] uppercase tracking-widest font-bold text-slate-500 dark:text-slate-400">{isEnglish ? 'Total users' : 'Usuários totais'}</p>
                <p className="text-2xl font-black text-slate-800 dark:text-slate-100 mt-2">{adminOverview?.users_total ?? 0}</p>
              </div>
              <div className="rounded-2xl border border-slate-100 dark:border-slate-700 bg-white/70 dark:bg-slate-900/60 p-4">
                <p className="text-[10px] uppercase tracking-widest font-bold text-slate-500 dark:text-slate-400">{isEnglish ? 'Admins' : 'Admins'}</p>
                <p className="text-2xl font-black text-slate-800 dark:text-slate-100 mt-2">{adminOverview?.admins_total ?? 0}</p>
              </div>
              <div className="rounded-2xl border border-slate-100 dark:border-slate-700 bg-white/70 dark:bg-slate-900/60 p-4">
                <p className="text-[10px] uppercase tracking-widest font-bold text-slate-500 dark:text-slate-400">{isEnglish ? 'Pending invites' : 'Convites pendentes'}</p>
                <p className="text-2xl font-black text-slate-800 dark:text-slate-100 mt-2">{adminOverview?.pending_invites_total ?? 0}</p>
              </div>
              <div className="rounded-2xl border border-slate-100 dark:border-slate-700 bg-white/70 dark:bg-slate-900/60 p-4">
                <p className="text-[10px] uppercase tracking-widest font-bold text-slate-500 dark:text-slate-400">{isEnglish ? 'Pending resets' : 'Resets pendentes'}</p>
                <p className="text-2xl font-black text-slate-800 dark:text-slate-100 mt-2">{adminOverview?.pending_reset_tokens_total ?? 0}</p>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-100 dark:border-slate-700 bg-white/70 dark:bg-slate-900/60 overflow-hidden">
              <div className="grid grid-cols-12 px-4 py-3 bg-slate-50/70 dark:bg-slate-800/50 text-[10px] uppercase tracking-widest font-bold text-slate-500 dark:text-slate-400">
                <div className="col-span-4">{isEnglish ? 'Name' : 'Nome'}</div>
                <div className="col-span-4">Email</div>
                <div className="col-span-2">{isEnglish ? 'Role' : 'Perfil'}</div>
                <div className="col-span-2">Status</div>
              </div>

              {adminLoading ? (
                <div className="px-4 py-6 text-sm text-slate-500 dark:text-slate-300">{isEnglish ? 'Loading users...' : 'Carregando usuários...'}</div>
              ) : adminUsers.length === 0 ? (
                <div className="px-4 py-6 text-sm text-slate-500 dark:text-slate-300">{isEnglish ? 'No users found.' : 'Nenhum usuário encontrado.'}</div>
              ) : (
                adminUsers.map((user) => (
                  <div key={user.id} className="grid grid-cols-12 px-4 py-3 border-t border-slate-100/80 dark:border-slate-700/60 text-sm text-slate-700 dark:text-slate-200">
                    <div className="col-span-4 font-semibold truncate">{user.full_name}</div>
                    <div className="col-span-4 truncate">{user.email}</div>
                    <div className="col-span-2 uppercase text-xs font-bold tracking-wider">{user.role}</div>
                    <div className="col-span-2">{user.is_active ? (isEnglish ? 'Active' : 'Ativo') : (isEnglish ? 'Inactive' : 'Inativo')}</div>
                  </div>
                ))
              )}
            </div>
          </main>
        ) : activeView === 'Settings' ? (
          <main className="grid grid-cols-1 lg:grid-cols-12 gap-8 flex-1">
            <div className="lg:col-span-8 flex flex-col gap-8">
              <div className="glass rounded-[32px] p-6">
                <h2 className="text-4xl font-black text-slate-800 dark:text-slate-100 tracking-tight">{isEnglish ? 'Settings' : 'Configuracoes'}</h2>
                <p className="text-slate-500 dark:text-slate-300 text-sm font-medium mt-1">
                  {isEnglish
                    ? 'Adjust interface preferences and behavior for this dashboard.'
                    : 'Ajuste preferencias de interface e comportamento deste painel.'}
                </p>

                <div className="mt-6 rounded-2xl border border-slate-100 dark:border-slate-700 bg-white/70 dark:bg-slate-900/60 p-5">
                  <h3 className="text-lg font-black text-slate-800 dark:text-slate-100">{isEnglish ? 'Language' : 'Idioma'}</h3>
                  <p className="text-slate-500 dark:text-slate-300 text-sm mt-1">
                    {isEnglish ? 'Choose the interface language.' : 'Escolha o idioma da interface.'}
                  </p>

                  <div className="mt-4 inline-flex p-1 rounded-2xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                    <button
                      onClick={() => setLanguage('pt-BR')}
                      className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all ${language === 'pt-BR' ? 'bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100 shadow-sm' : 'text-slate-500 dark:text-slate-300 hover:text-slate-700 dark:hover:text-white'}`}
                    >
                      {isEnglish ? 'Portuguese (BR)' : 'Português (BR)'}
                    </button>
                    <button
                      onClick={() => setLanguage('en-US')}
                      className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all ${language === 'en-US' ? 'bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100 shadow-sm' : 'text-slate-500 dark:text-slate-300 hover:text-slate-700 dark:hover:text-white'}`}
                    >
                      English (US)
                    </button>
                  </div>
                </div>

                <div className="mt-6 rounded-2xl border border-slate-100 dark:border-slate-700 bg-white/70 dark:bg-slate-900/60 p-5">
                  <h3 className="text-lg font-black text-slate-800 dark:text-slate-100">{isEnglish ? 'Presentation Data' : 'Dados para Apresentacao'}</h3>
                  <p className="text-slate-500 dark:text-slate-300 text-sm mt-1">
                    {isEnglish
                      ? 'Enable realistic mock data to keep charts and statuses animated during your demo.'
                      : 'Ative dados mockados realistas para manter graficos e status animados durante sua apresentacao.'}
                  </p>

                  <div className="mt-4 flex items-center justify-between gap-3 rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/60 px-4 py-3">
                    <div>
                      <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">{isEnglish ? 'Mock mode' : 'Modo mockado'}</p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">{demoMode ? (isEnglish ? 'Using simulated sensor stream.' : 'Usando stream simulado de sensores.') : (isEnglish ? 'Using real API stream.' : 'Usando stream real da API.')}</p>
                    </div>
                    <button
                      onClick={() => setDemoMode((current) => !current)}
                      className={`px-4 py-2 rounded-xl text-sm font-bold transition-all ${demoMode ? 'bg-emerald-600 hover:bg-emerald-500 text-white' : 'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-300 dark:hover:bg-slate-600'}`}
                    >
                      {demoMode ? (isEnglish ? 'On' : 'Ligado') : (isEnglish ? 'Off' : 'Desligado')}
                    </button>
                  </div>
                </div>

              </div>
            </div>

            <div className="lg:col-span-4 flex flex-col gap-8">
              <div className="glass rounded-[28px] p-5">
                <h3 className="text-sm font-black uppercase tracking-widest text-slate-700 dark:text-slate-200">{isEnglish ? 'Current profile' : 'Perfil atual'}</h3>
                <div className="mt-4 space-y-3 text-sm">
                  <div className="flex items-center justify-between text-slate-600 dark:text-slate-300">
                    <span>{isEnglish ? 'Theme' : 'Tema'}</span>
                    <strong className="text-slate-800 dark:text-slate-100">{theme === 'dark' ? (isEnglish ? 'Dark' : 'Escuro') : (isEnglish ? 'Light' : 'Claro')}</strong>
                  </div>
                  <div className="flex items-center justify-between text-slate-600 dark:text-slate-300">
                    <span>{isEnglish ? 'Language' : 'Idioma'}</span>
                    <strong className="text-slate-800 dark:text-slate-100">{language === 'pt-BR' ? 'PT-BR' : 'EN-US'}</strong>
                  </div>
                  <div className="flex items-center justify-between text-slate-600 dark:text-slate-300">
                    <span>MQTT</span>
                    <strong className="text-slate-800 dark:text-slate-100">{mqttStatus?.connected ? (isEnglish ? 'Connected' : 'Conectado') : (isEnglish ? 'Disconnected' : 'Desconectado')}</strong>
                  </div>
                </div>
              </div>
            </div>
          </main>
        ) : (
          <div className="flex-1 flex items-center justify-center glass rounded-[24px]">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-slate-800 dark:text-slate-100 mb-2">{isEnglish ? 'Module' : 'Módulo'} {getViewLabel(activeView)}</h2>
              <p className="text-slate-500 dark:text-slate-300">{isEnglish ? 'This feature is under development.' : 'Esta funcionalidade está em desenvolvimento.'}</p>
            </div>
          </div>
        )}
        
        {/* Footer / Decorative */}
        <footer className="mt-6 text-center">
          <p className="text-[10px] font-mono text-slate-400 dark:text-slate-500 uppercase tracking-[0.4em]">
            Gaia_OS_v1.0 // MQTT: {mqttStatus?.connected ? (isEnglish ? 'Connected' : 'Conectado') : (isEnglish ? 'Disconnected' : 'Desconectado')}
          </p>
        </footer>
      </div>
    </div>
  );
}
