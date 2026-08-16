
"use client";

import { useState, useEffect, useRef } from "react";
import { Search, Loader2, CheckCircle2, XCircle, Radio } from "lucide-react";

type ProspectStatus = "idle" | "starting" | "scraping" | "evaluating" | "completed" | "error";

export default function Prospect() {
  const [niche, setNiche] = useState("");
  const [region, setRegion] = useState("");
  const [prompt, setPrompt] = useState("");
  const [maxResults, setMaxResults] = useState(50);
  const [minScore, setMinScore] = useState(7);
  const [source, setSource] = useState("maps");
  const [status, setStatus] = useState<ProspectStatus>("idle");
  const [statusMessage, setStatusMessage] = useState("");
  const [campaignId, setCampaignId] = useState<string | null>(null);
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  // Poll campaign status while active
  useEffect(() => {
    if (!campaignId || status === "completed" || status === "error" || status === "idle") {
      if (pollRef.current) clearInterval(pollRef.current);
      return;
    }

    pollRef.current = setInterval(async () => {
      try {
        const r = await fetch(`https://velli-prospect.onrender.com/api/campaigns/${campaignId}`);
        if (r.ok) {
          const data = await r.json();
          if (data.status === "completed") {
            setStatus("completed");
            setStatusMessage(`Prospecção finalizada! ${data.total_approved || 0} leads qualificados encontrados.`);
            if (pollRef.current) clearInterval(pollRef.current);
          } else {
            setStatus("scraping");
            const found = data.total_found || 0;
            const approved = data.total_approved || 0;
            setStatusMessage(`Fazendo varredura... ${found} encontrados, ${approved} aprovados pela IA`);
          }
        }
      } catch {
        // Connection error, keep trying
      }
    }, 5000);

    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [campaignId, status]);

  const handleStart = async () => {
    if (!niche || !region) {
      setStatus("error");
      setStatusMessage("Preencha o nicho e a região antes de iniciar.");
      return;
    }
    
    setStatus("starting");
    setStatusMessage("Conectando ao servidor de prospecção...");
    
    try {
      const res = await fetch("https://velli-prospect.onrender.com/api/campaigns", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          niche, region, criteria: prompt, 
          max_results: maxResults, min_score: minScore, 
          source, block_large_portals: true 
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        setCampaignId(data.campaign?.id || null);
        setStatus("scraping");
        setStatusMessage("Fazendo varredura... buscando empresas na região informada...");
      } else {
        setStatus("error");
        setStatusMessage("Erro ao iniciar a prospecção. Tente novamente.");
      }
    } catch {
      setStatus("error");
      setStatusMessage("Falha na conexão com o servidor. Verifique sua internet.");
    }
  };

  const handleCancel = async () => {
    if (!campaignId) return;
    try {
      await fetch(`https://velli-prospect.onrender.com/api/campaigns/${campaignId}/cancel`, { method: "POST" });
    } catch {}
    setStatus("idle");
    setStatusMessage("");
    setCampaignId(null);
  };

  const handleReset = () => {
    setStatus("idle");
    setStatusMessage("");
    setCampaignId(null);
    setNiche("");
    setRegion("");
    setPrompt("");
  };

  const statusColors: Record<ProspectStatus, string> = {
    idle: "",
    starting: "text-yellow-400",
    scraping: "text-blue-400",
    evaluating: "text-purple-400",
    completed: "text-green-400",
    error: "text-red-400",
  };

  return (
    <div className="min-h-screen p-4 md:p-10 lg:p-20 flex flex-col items-center justify-center relative overflow-hidden">
      {/* Background blobs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-600/20 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-600/20 rounded-full blur-[120px] pointer-events-none" />
      
      <div className="w-full max-w-4xl flex flex-col items-center text-center z-10 space-y-4 md:space-y-6">
        <img src="/logo_velli_white.png" alt="Velli Marketing" className="h-16 md:h-20 mb-2 object-contain" />
        <h1 className="text-4xl md:text-5xl lg:text-7xl font-extrabold tracking-tight bg-gradient-to-br from-white to-gray-500 bg-clip-text text-transparent">
          Velli Prospect
        </h1>
        <p className="text-lg md:text-xl text-gray-400 font-medium max-w-2xl px-4">
          Transformando negócios comuns em marcas extraordinárias.
        </p>

        <div className="w-full max-w-2xl mt-8 md:mt-12 glass-panel p-6 md:p-8 rounded-3xl flex flex-col gap-6 relative group">
          <div className="absolute inset-0 rounded-3xl bg-gradient-to-b from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
          
          <div className="flex flex-col gap-2 text-left">
            <label className="text-sm font-semibold text-gray-300 ml-2">Qual o nicho alvo?</label>
            <input 
              type="text" 
              placeholder="Ex: Advogados, Clínicas de Estética"
              value={niche}
              onChange={e => setNiche(e.target.value)}
              disabled={status === "scraping" || status === "starting"}
              className="w-full bg-black/40 border border-white/10 rounded-2xl px-6 py-4 outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all text-white placeholder:text-gray-600 disabled:opacity-50"
            />
          </div>

          <div className="flex flex-col gap-2 text-left">
            <label className="text-sm font-semibold text-gray-300 ml-2">Qual a região?</label>
            <input 
              type="text" 
              placeholder="Ex: São Paulo, Brasilia"
              value={region}
              onChange={e => setRegion(e.target.value)}
              disabled={status === "scraping" || status === "starting"}
              className="w-full bg-black/40 border border-white/10 rounded-2xl px-6 py-4 outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all text-white placeholder:text-gray-600 disabled:opacity-50"
            />
          </div>

          <div className="flex flex-col gap-2 text-left">
            <label className="text-sm font-semibold text-gray-300 ml-2">Onde procurar?</label>
            <select 
              value={source}
              onChange={e => setSource(e.target.value)}
              disabled={status === "scraping" || status === "starting"}
              className="w-full bg-black/40 border border-white/10 rounded-2xl px-6 py-4 outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all text-white disabled:opacity-50"
            >
              <option value="maps">Google Maps (Recomendado para Negócios Locais)</option>
              <option value="instagram">Instagram</option>
              <option value="linkedin">LinkedIn</option>
              <option value="maps_insta">Google Maps + Instagram</option>
            </select>
          </div>

          <div className="flex flex-col gap-2 text-left">
            <label className="text-sm font-semibold text-gray-300 ml-2">Prompt Customizado (Opcional)</label>
            <textarea 
              placeholder="Ex: Buscar empresas com site ruim, sem foto de capa no maps..."
              value={prompt}
              onChange={e => setPrompt(e.target.value)}
              disabled={status === "scraping" || status === "starting"}
              className="w-full bg-black/40 border border-white/10 rounded-2xl px-6 py-4 outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all text-white placeholder:text-gray-600 min-h-[100px] resize-y disabled:opacity-50"
            />
          </div>

          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex flex-col gap-2 text-left w-full md:w-1/2">
              <label className="text-sm font-semibold text-gray-300 ml-2">Máximo de Resultados</label>
              <input 
                type="number" 
                value={maxResults}
                onChange={e => setMaxResults(Number(e.target.value))}
                disabled={status === "scraping" || status === "starting"}
                className="w-full bg-black/40 border border-white/10 rounded-2xl px-6 py-4 outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all text-white disabled:opacity-50"
              />
            </div>
            <div className="flex flex-col gap-2 text-left w-full md:w-1/2">
              <label className="text-sm font-semibold text-gray-300 ml-2">Nota de Corte (0 a 10)</label>
              <input 
                type="number" 
                value={minScore}
                onChange={e => setMinScore(Number(e.target.value))}
                disabled={status === "scraping" || status === "starting"}
                className="w-full bg-black/40 border border-white/10 rounded-2xl px-6 py-4 outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all text-white disabled:opacity-50"
                min={0} max={10}
              />
            </div>
          </div>

          {/* Status Panel - shows during and after prospection */}
          {status !== "idle" && (
            <div className={`flex items-center gap-3 p-4 rounded-2xl border ${
              status === "completed" ? "bg-green-500/10 border-green-500/30" :
              status === "error" ? "bg-red-500/10 border-red-500/30" :
              "bg-blue-500/10 border-blue-500/30"
            } animate-in fade-in duration-500`}>
              {(status === "starting" || status === "scraping" || status === "evaluating") && (
                <Loader2 className="animate-spin text-blue-400 flex-shrink-0" size={20} />
              )}
              {status === "completed" && <CheckCircle2 className="text-green-400 flex-shrink-0" size={20} />}
              {status === "error" && <XCircle className="text-red-400 flex-shrink-0" size={20} />}
              <div className="flex-1">
                <p className={`text-sm font-semibold ${statusColors[status]}`}>{statusMessage}</p>
                {status === "scraping" && (
                  <p className="text-xs text-gray-500 mt-1">Acompanhe em tempo real na aba Campanhas</p>
                )}
              </div>
              {(status === "completed" || status === "error") && (
                <button 
                  onClick={handleReset}
                  className="text-xs font-semibold text-gray-400 hover:text-white border border-white/10 px-3 py-1.5 rounded-xl transition-all hover:bg-white/5"
                >
                  Nova Prospecção
                </button>
              )}
            </div>
          )}

          {/* Button */}
          {status === "idle" || status === "error" ? (
            <button 
              onClick={handleStart}
              className="mt-2 relative w-full overflow-hidden rounded-2xl p-[1px] group"
            >
              <span className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl opacity-70 group-hover:opacity-100 transition-opacity duration-300" />
              <div className="relative flex items-center justify-center gap-3 bg-black px-6 py-4 rounded-2xl text-white font-bold tracking-wide transition-all duration-300 group-hover:bg-opacity-0">
                <Search />
                <span>INICIAR PROSPECÇÃO</span>
              </div>
            </button>
          ) : status === "scraping" || status === "starting" || status === "evaluating" ? (
            <div className="mt-2 flex flex-col md:flex-row gap-3">
              <div className="w-full rounded-2xl bg-white/5 border border-white/10 px-6 py-4 flex items-center justify-center gap-3">
                <Radio className="text-blue-400 animate-pulse" size={20} />
                <span className="text-sm font-bold text-blue-400 uppercase tracking-wider">Prospecção em Andamento...</span>
              </div>
              <button 
                onClick={handleCancel}
                className="w-full md:w-auto rounded-2xl bg-red-500/10 border border-red-500/30 px-6 py-4 flex items-center justify-center gap-2 hover:bg-red-500/20 transition-colors text-red-400"
              >
                <XCircle size={20} />
                <span className="text-sm font-bold uppercase tracking-wider">Cancelar</span>
              </button>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
