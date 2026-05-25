import React, { useEffect, useRef, useState } from 'react';
import { Camera, PauseCircle, PlayCircle, Image as ImageIcon, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

interface ScanViewProps {
  language?: 'pt-BR' | 'en-US';
}

export const ScanView: React.FC<ScanViewProps> = ({ language = 'pt-BR' }) => {
  const isEnglish = language === 'en-US';
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [capturedImages, setCapturedImages] = useState<string[]>([]);
  const [cameraError, setCameraError] = useState<string | null>(null);

  const stopCamera = () => {
    stream?.getTracks().forEach((track) => track.stop());
    setStream(null);
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  };

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: 1280, height: 720 },
      });
      setCameraError(null);
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
      toast.success(isEnglish ? 'Camera connected' : 'Camera conectada', {
        description: isEnglish ? 'Live plant view started.' : 'Visualizacao ao vivo da planta iniciada.',
      });
    } catch {
      setCameraError(isEnglish ? 'Could not access the camera.' : 'Nao foi possivel acessar a camera.');
      toast.error(isEnglish ? 'Camera access error' : 'Erro ao acessar a camera', {
        description: isEnglish ? 'Check browser camera permission.' : 'Verifique permissao de camera no navegador.',
      });
    }
  };

  const captureFrame = () => {
    if (!videoRef.current || !canvasRef.current) {
      return;
    }

    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video.videoWidth || !video.videoHeight) {
      return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext('2d');

    if (!context) {
      return;
    }

    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const image = canvas.toDataURL('image/jpeg', 0.86);
    setCapturedImages((prev) => [image, ...prev].slice(0, 12));
    toast.success(isEnglish ? 'Photo captured' : 'Foto capturada', {
      description: isEnglish ? 'Frame saved to side panel.' : 'Frame salvo no painel lateral.',
    });
  };

  useEffect(() => {
    void startCamera();
    return () => {
      stopCamera();
    };
  }, []);

  return (
    <div className="flex flex-col gap-6 h-full">
      <div className="glass rounded-[28px] p-5 sm:p-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-slate-800 dark:text-slate-100">{isEnglish ? 'Plant Camera' : 'Camera da Planta'}</h2>
          <p className="text-slate-500 dark:text-slate-300 text-sm mt-1">{isEnglish ? 'Live view to monitor the plant framing in real time.' : 'Visualizacao ao vivo para acompanhar o enquadramento da planta em tempo real.'}</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest bg-white/70 dark:bg-slate-900/60 border border-slate-100 dark:border-slate-700 text-slate-600 dark:text-slate-300">
            {stream ? (isEnglish ? 'Camera on' : 'Camera ativa') : (isEnglish ? 'Camera off' : 'Camera inativa')}
          </span>
          {stream ? (
            <button
              onClick={stopCamera}
              className="flex items-center gap-2 px-4 py-2 rounded-xl border border-red-200 dark:border-red-500/40 bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-300 hover:bg-red-100 dark:hover:bg-red-500/20 transition-all"
            >
              <PauseCircle size={18} />
              {isEnglish ? 'Pause' : 'Pausar'}
            </button>
          ) : (
            <button
              onClick={startCamera}
              className="flex items-center gap-2 px-4 py-2 rounded-xl border border-green-200 dark:border-green-500/40 bg-green-50 dark:bg-green-500/10 text-green-600 dark:text-green-300 hover:bg-green-100 dark:hover:bg-green-500/20 transition-all"
            >
              <PlayCircle size={18} />
              {isEnglish ? 'Start' : 'Iniciar'}
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1">
        <div className="lg:col-span-8 flex flex-col gap-4">
          <div className="relative aspect-video glass rounded-[28px] overflow-hidden border border-slate-200 dark:border-slate-700/50 bg-slate-950">
            <video ref={videoRef} autoPlay playsInline className="w-full h-full object-cover" />

            {stream && (
              <>
                <div className="absolute inset-0 pointer-events-none border border-green-500/30" />
                <div className="absolute inset-0 pointer-events-none bg-[linear-gradient(to_right,transparent_0%,transparent_32%,rgba(34,197,94,0.15)_50%,transparent_68%,transparent_100%)]" />
                <div className="absolute top-3 left-3 px-2 py-1 rounded-lg bg-black/45 text-white text-[10px] font-bold uppercase tracking-wider">
                  {isEnglish ? 'Live' : 'Ao vivo'}
                </div>
              </>
            )}

            {!stream && (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-300 gap-3 bg-slate-900/80 px-6 text-center">
                <Camera size={44} strokeWidth={1.5} />
                <p className="text-sm font-medium">{cameraError ?? (isEnglish ? 'Waiting for camera initialization...' : 'Aguardando inicializacao da camera...')}</p>
              </div>
            )}
            <canvas ref={canvasRef} className="hidden" />
          </div>

          <div className="glass rounded-[24px] p-4 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
              <ImageIcon size={18} />
              <span className="text-sm font-semibold">{isEnglish ? `Recent captures: ${capturedImages.length}` : `Capturas recentes: ${capturedImages.length}`}</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={captureFrame}
                disabled={!stream}
                className="px-4 py-2 rounded-xl bg-green-600 hover:bg-green-500 text-white text-sm font-bold disabled:opacity-45 disabled:cursor-not-allowed transition-all"
              >
                {isEnglish ? 'Capture photo' : 'Capturar foto'}
              </button>
              <button
                onClick={() => setCapturedImages([])}
                className="p-2 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-300 hover:text-red-500 hover:border-red-300 dark:hover:border-red-500/40 transition-colors"
                aria-label={isEnglish ? 'Clear captures' : 'Limpar capturas'}
                title={isEnglish ? 'Clear captures' : 'Limpar capturas'}
              >
                <Trash2 size={18} />
              </button>
            </div>
          </div>
        </div>

        <div className="lg:col-span-4 glass rounded-[24px] p-4 sm:p-5 flex flex-col gap-4 min-h-[420px]">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-black uppercase tracking-widest text-slate-700 dark:text-slate-200">{isEnglish ? 'Local gallery' : 'Galeria local'}</h3>
            <span className="text-[10px] font-mono text-slate-400 dark:text-slate-500">max 12</span>
          </div>

          <div className="grid grid-cols-2 gap-3 overflow-y-auto pr-1">
            {capturedImages.length === 0 && (
              <div className="col-span-2 h-44 rounded-2xl border-2 border-dashed border-slate-200 dark:border-slate-700 flex items-center justify-center text-xs text-slate-500 dark:text-slate-400 text-center px-4">
                {isEnglish ? 'No captures yet. Click Capture photo to save a frame.' : 'Nenhuma captura ainda. Clique em Capturar foto para salvar um frame.'}
              </div>
            )}

            {capturedImages.map((image, index) => (
              <div key={`${image}-${index}`} className="aspect-square rounded-xl overflow-hidden border border-slate-100 dark:border-slate-700 relative">
                <img src={image} alt={`${isEnglish ? 'Capture' : 'Registro'} ${index + 1}`} className="w-full h-full object-cover" />
                <div className="absolute bottom-1 right-1 px-1.5 py-0.5 rounded bg-black/55 text-white text-[9px] font-mono">
                  #{index + 1}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
