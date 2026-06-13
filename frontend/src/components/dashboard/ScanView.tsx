import React, { useRef, useState } from 'react';
import { Camera, PauseCircle, PlayCircle, Trash2, Loader2, Microscope, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';
import { api } from '../../services/api';
import { PlantAnalysis } from '../../types';

interface ScanViewProps {
  language?: 'pt-BR' | 'en-US';
}

interface CapturedFrame {
  id: string;
  image: string;
  status: 'analyzing' | 'done' | 'error';
  analysis?: PlantAnalysis;
}

function parseClassName(rawClass: string): { plant: string; condition: string; isHealthy: boolean } {
  const parts = rawClass.split('___');
  const plant = (parts[0] ?? rawClass).replace(/_/g, ' ');
  const condition = (parts[1] ?? '').replace(/_/g, ' ');
  const isHealthy = condition.toLowerCase() === 'healthy' || condition.toLowerCase() === 'saudavel';
  return { plant, condition: isHealthy ? 'Saudável' : condition || plant, isHealthy };
}

function ConfidenceBar({ value, isHealthy }: { value: number; isHealthy: boolean }) {
  const pct = Math.round(value * 100);
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${isHealthy ? 'bg-emerald-500' : 'bg-amber-500'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-bold tabular-nums text-slate-700 dark:text-slate-200 w-9 text-right">{pct}%</span>
    </div>
  );
}

const MJPEG_STREAM_URL = import.meta.env.VITE_ESP32_CAM_STREAM_URL ?? '';

export const ScanView: React.FC<ScanViewProps> = ({ language = 'pt-BR' }) => {
  const isEnglish = language === 'en-US';
  const imageRef = useRef<HTMLImageElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [frames, setFrames] = useState<CapturedFrame[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [isLiveOpen, setIsLiveOpen] = useState(false);
  const [streamError, setStreamError] = useState<string | null>(null);

  const selectedFrame = frames.find((f) => f.id === selectedId) ?? frames[0] ?? null;
  const hasStream = Boolean(MJPEG_STREAM_URL);

  const captureAndAnalyze = async () => {
    if (!imageRef.current || !canvasRef.current) return;
    const image = imageRef.current;
    const canvas = canvasRef.current;
    if (!image.complete || !image.naturalWidth) {
      toast.error(isEnglish ? 'Stream not ready' : 'Stream indisponível', {
        description: isEnglish ? 'Wait for the MJPEG feed to load.' : 'Aguarde o carregamento do feed MJPEG.',
      });
      return;
    }

    canvas.width = image.naturalWidth;
    canvas.height = image.naturalHeight;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    try {
      ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
    } catch {
      toast.error(isEnglish ? 'Unable to read stream frame' : 'Não foi possível ler o frame do stream');
      return;
    }

    const imageB64 = canvas.toDataURL('image/jpeg', 0.86);
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
    const newFrame: CapturedFrame = { id, image: imageB64, status: 'analyzing' };

    setFrames((prev) => [newFrame, ...prev].slice(0, 8));
    setSelectedId(id);

    toast.info(isEnglish ? 'Analyzing frame...' : 'Analisando imagem...', { duration: 2000 });

    try {
      const analysis = await api.analyzeImage(imageB64);
      setFrames((prev) => prev.map((f) => (f.id === id ? { ...f, status: 'done', analysis } : f)));
      const { condition, isHealthy } = parseClassName(analysis.top_prediction.class);
      const pct = Math.round(analysis.top_prediction.confidence * 100);

      if (analysis.mock) {
        toast.warning(isEnglish ? 'Model not trained yet' : 'Modelo ainda não treinado', {
          description: isEnglish ? 'Train the model to get real predictions.' : 'Treine o modelo para obter predições reais.',
        });
      } else {
        toast.success(isEnglish ? `Result: ${condition}` : `Resultado: ${condition}`, {
          description: `${pct}% ${isEnglish ? 'confidence' : 'de confiança'} · ${analysis.inference_ms}ms`,
        });
      }

    } catch {
      setFrames((prev) => prev.map((f) => (f.id === id ? { ...f, status: 'error' } : f)));
      toast.error(isEnglish ? 'Analysis failed' : 'Falha na análise');
    }
  };

  return (
    <div className="flex flex-col gap-6 h-full">
      <div className="glass rounded-[28px] p-5 sm:p-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-slate-800 dark:text-slate-100">
            {isEnglish ? 'Plant Camera' : 'Camera da Planta'}
          </h2>
          <p className="text-slate-500 dark:text-slate-300 text-sm mt-1">
            {isEnglish
              ? 'Live MJPEG stream from the ESP32-CAM with optional image capture.'
              : 'Stream MJPEG ao vivo da ESP32-CAM com captura opcional de imagem.'}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest bg-white/70 dark:bg-slate-900/60 border border-slate-100 dark:border-slate-700 text-slate-600 dark:text-slate-300">
            {isLiveOpen && hasStream ? (isEnglish ? 'Live on' : 'Ao vivo') : (isEnglish ? 'Live off' : 'Offline')}
          </span>
          <button
            onClick={() => {
              if (!hasStream) {
                setStreamError(isEnglish ? 'Define VITE_ESP32_CAM_STREAM_URL to enable the stream.' : 'Defina VITE_ESP32_CAM_STREAM_URL para habilitar o stream.');
                toast.error(isEnglish ? 'Missing stream URL' : 'URL do stream ausente');
                return;
              }

              setStreamError(null);
              setIsLiveOpen((current) => !current);
            }}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl border transition-all ${
              isLiveOpen
                ? 'border-red-200 dark:border-red-500/40 bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-300 hover:bg-red-100 dark:hover:bg-red-500/20'
                : 'border-green-200 dark:border-green-500/40 bg-green-50 dark:bg-green-500/10 text-green-600 dark:text-green-300 hover:bg-green-100 dark:hover:bg-green-500/20'
            }`}
          >
            {isLiveOpen ? <PauseCircle size={18} /> : <PlayCircle size={18} />}
            {isLiveOpen ? (isEnglish ? 'Pause live' : 'Pausar live') : (isEnglish ? 'Open live' : 'Abrir live')}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1">
        <div className="lg:col-span-8 flex flex-col gap-4">
          <div className="relative aspect-video glass rounded-[28px] overflow-hidden border border-slate-200 dark:border-slate-700/50 bg-slate-950">
            {isLiveOpen && hasStream ? (
              <img
                ref={imageRef}
                src={MJPEG_STREAM_URL}
                alt={isEnglish ? 'ESP32-CAM live stream' : 'Stream ao vivo da ESP32-CAM'}
                crossOrigin="anonymous"
                className="w-full h-full object-cover"
                onLoad={() => setStreamError(null)}
                onError={() => setStreamError(isEnglish ? 'Could not load the live stream.' : 'Não foi possível carregar o stream.')}
              />
            ) : (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-300 gap-3 bg-slate-900/80 px-6 text-center">
                <Camera size={44} strokeWidth={1.5} />
                <p className="text-sm font-medium">
                  {streamError ?? (isEnglish ? 'Open the live stream to view the camera.' : 'Abra o live stream para ver a câmera.')}
                </p>
              </div>
            )}

            {isLiveOpen && hasStream && (
              <>
                <div className="absolute inset-0 pointer-events-none border border-green-500/30" />
                <div className="absolute inset-0 pointer-events-none bg-[linear-gradient(to_right,transparent_32%,rgba(34,197,94,0.12)_50%,transparent_68%)]" />
                <div className="absolute top-3 left-3 px-2 py-1 rounded-lg bg-black/45 text-white text-[10px] font-bold uppercase tracking-wider">
                  {isEnglish ? 'Live' : 'Ao vivo'}
                </div>
                <div className="absolute top-3 right-3 flex items-center gap-1.5 px-2 py-1 rounded-lg bg-black/45 text-emerald-400 text-[10px] font-bold uppercase tracking-wider">
                  <Microscope size={12} />
                  MJPEG
                </div>
              </>
            )}

            <canvas ref={canvasRef} className="hidden" />
          </div>

          <div className="glass rounded-[24px] p-4 flex items-center justify-between gap-3">
            <div className="text-slate-600 dark:text-slate-300 text-sm font-semibold">
              {isEnglish ? `${frames.length} capture${frames.length !== 1 ? 's' : ''}` : `${frames.length} captura${frames.length !== 1 ? 's' : ''}`}
              {frames.some((f) => f.status === 'analyzing') && (
                <span className="ml-2 text-amber-500 text-xs font-bold">
                  {isEnglish ? '· analyzing...' : '· analisando...'}
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={captureAndAnalyze}
                disabled={!isLiveOpen || !hasStream}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-green-600 hover:bg-green-500 text-white text-sm font-bold disabled:opacity-45 disabled:cursor-not-allowed transition-all"
              >
                <Microscope size={16} />
                {isEnglish ? 'Capture & Analyze' : 'Capturar e Analisar'}
              </button>
              <button
                onClick={() => {
                  setFrames([]);
                  setSelectedId(null);
                }}
                className="p-2 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-300 hover:text-red-500 hover:border-red-300 dark:hover:border-red-500/40 transition-colors"
                title={isEnglish ? 'Clear all' : 'Limpar tudo'}
              >
                <Trash2 size={18} />
              </button>
            </div>
          </div>
        </div>

        <div className="lg:col-span-4 flex flex-col gap-4">
          <div className="glass rounded-[24px] p-4 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-black uppercase tracking-widest text-slate-700 dark:text-slate-200">
                {isEnglish ? 'Captures' : 'Capturas'}
              </h3>
              <span className="text-[10px] font-mono text-slate-400 dark:text-slate-500">max 8</span>
            </div>

            <div className="grid grid-cols-4 gap-2">
              {frames.length === 0 && (
                <div className="col-span-4 h-24 rounded-2xl border-2 border-dashed border-slate-200 dark:border-slate-700 flex items-center justify-center text-xs text-slate-400 dark:text-slate-500 text-center px-3">
                  {isEnglish ? 'No captures yet.' : 'Nenhuma captura ainda.'}
                </div>
              )}

              {frames.map((frame, i) => {
                const isSelected = frame.id === selectedId;
                const parsed = frame.analysis ? parseClassName(frame.analysis.top_prediction.class) : null;
                return (
                  <button
                    key={frame.id}
                    onClick={() => setSelectedId(frame.id)}
                    className={`aspect-square rounded-xl overflow-hidden relative border-2 transition-all ${
                      isSelected
                        ? 'border-green-500 shadow-md shadow-green-500/20'
                        : 'border-transparent hover:border-slate-300 dark:hover:border-slate-600'
                    }`}
                  >
                    <img src={frame.image} alt={`frame ${i + 1}`} className="w-full h-full object-cover" />

                    {frame.status === 'analyzing' && (
                      <div className="absolute inset-0 bg-black/55 flex items-center justify-center">
                        <Loader2 size={16} className="text-white animate-spin" />
                      </div>
                    )}

                    {frame.status === 'error' && (
                      <div className="absolute inset-0 bg-red-900/60 flex items-center justify-center">
                        <AlertTriangle size={14} className="text-red-300" />
                      </div>
                    )}

                    {frame.status === 'done' && parsed && (
                      <div className="absolute bottom-0 left-0 right-0 px-1 py-0.5 bg-gradient-to-t from-black/80 to-transparent">
                        <p className={`text-[8px] font-bold truncate ${parsed.isHealthy ? 'text-emerald-300' : 'text-amber-300'}`}>
                          {parsed.isHealthy ? '✓' : '!'} {parsed.condition}
                        </p>
                      </div>
                    )}

                    <div className="absolute top-0.5 right-0.5 bg-black/55 text-white text-[8px] font-mono px-0.5 rounded">
                      {i + 1}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="glass rounded-[24px] p-4 flex-1 flex flex-col gap-3">
            <h3 className="text-sm font-black uppercase tracking-widest text-slate-700 dark:text-slate-200">
              {isEnglish ? 'AI Result' : 'Resultado IA'}
            </h3>

            {!selectedFrame && (
              <div className="flex-1 flex flex-col items-center justify-center text-center gap-2 py-6">
                <Microscope size={32} strokeWidth={1.5} className="text-slate-300 dark:text-slate-600" />
                <p className="text-xs text-slate-400 dark:text-slate-500">
                  {isEnglish ? 'Capture a frame to get an AI analysis.' : 'Capture um frame para obter a análise da IA.'}
                </p>
              </div>
            )}

            {selectedFrame?.status === 'analyzing' && (
              <div className="flex-1 flex flex-col items-center justify-center gap-3 py-6">
                <Loader2 size={28} className="text-green-500 animate-spin" />
                <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                  {isEnglish ? 'Running model inference...' : 'Executando inferência do modelo...'}
                </p>
              </div>
            )}

            {selectedFrame?.status === 'error' && (
              <div className="flex-1 flex flex-col items-center justify-center gap-2 py-6">
                <AlertTriangle size={28} className="text-red-400" />
                <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                  {isEnglish ? 'Analysis failed. Try again.' : 'Análise falhou. Tente novamente.'}
                </p>
              </div>
            )}

            {selectedFrame?.status === 'done' && selectedFrame.analysis && (() => {
              const analysis = selectedFrame.analysis;
              const { plant, condition, isHealthy } = parseClassName(analysis.top_prediction.class);
              const isMock = analysis.mock;
              return (
                <div className="flex flex-col gap-3">
                  {isMock && (
                    <div className="rounded-xl border border-amber-200 dark:border-amber-500/30 bg-amber-50 dark:bg-amber-500/10 px-3 py-2 text-xs text-amber-700 dark:text-amber-300 font-semibold">
                      {isEnglish ? 'Model not trained — showing placeholder.' : 'Modelo não treinado — exibindo placeholder.'}
                    </div>
                  )}

                  <div className={`rounded-2xl border px-4 py-3 flex items-center gap-3 ${
                    isHealthy
                      ? 'border-emerald-200 dark:border-emerald-500/30 bg-emerald-50 dark:bg-emerald-500/10'
                      : 'border-amber-200 dark:border-amber-500/30 bg-amber-50 dark:bg-amber-500/10'
                  }`}>
                    {isHealthy
                      ? <CheckCircle2 size={22} className="text-emerald-600 dark:text-emerald-400 shrink-0" />
                      : <AlertTriangle size={22} className="text-amber-600 dark:text-amber-400 shrink-0" />
                    }
                    <div className="min-w-0">
                      <p className="text-[10px] uppercase tracking-widest font-bold text-slate-500 dark:text-slate-400">
                        {plant}
                      </p>
                      <p className={`text-base font-black truncate ${
                        isHealthy ? 'text-emerald-700 dark:text-emerald-300' : 'text-amber-700 dark:text-amber-300'
                      }`}>
                        {condition}
                      </p>
                    </div>
                  </div>

                  <div>
                    <p className="text-[10px] uppercase tracking-widest font-bold text-slate-500 dark:text-slate-400 mb-1.5">
                      {isEnglish ? 'Confidence' : 'Confiança'}
                    </p>
                    <ConfidenceBar value={analysis.top_prediction.confidence} isHealthy={isHealthy} />
                  </div>

                  {analysis.top_k.length > 1 && (
                    <div>
                      <p className="text-[10px] uppercase tracking-widest font-bold text-slate-500 dark:text-slate-400 mb-1.5">
                        {isEnglish ? 'Top predictions' : 'Top predições'}
                      </p>
                      <div className="flex flex-col gap-1.5">
                        {analysis.top_k.map((pred, i) => {
                          const p = parseClassName(pred.class);
                          return (
                            <div key={i} className="flex items-center justify-between gap-2 text-xs">
                              <span className="text-slate-600 dark:text-slate-300 truncate">
                                {i + 1}. {p.condition}
                              </span>
                              <span className="tabular-nums font-bold text-slate-700 dark:text-slate-200 shrink-0">
                                {Math.round(pred.confidence * 100)}%
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {!isMock && (
                    <p className="text-[10px] font-mono text-slate-400 dark:text-slate-500 text-right">
                      {isEnglish ? `inference: ${analysis.inference_ms}ms` : `inferência: ${analysis.inference_ms}ms`}
                    </p>
                  )}
                </div>
              );
            })()}
          </div>
        </div>
      </div>
    </div>
  );
};
