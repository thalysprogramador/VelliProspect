
"use client";

import { Search, Radio, XCircle } from "lucide-react";
import { useProspect } from "@/context/ProspectContext";

export default function Prospect() {
  const {
    niche, setNiche,
    region, setRegion,
    prompt, setPrompt,
    maxResults, setMaxResults,
    minScore, setMinScore,
    sources, setSources,
    status, campaignId,
    handleStart, handleCancel
  } = useProspect();

  const toggleSource = (src: string) => {
    if (sources.includes(src)) {
      setSources(sources.filter(s => s !== src));
    } else {
      setSources([...sources, src]);
    }
  };

  const isBusy = status === "starting" || status === "scraping" || status === "evaluating";

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
              disabled={isBusy}
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
              disabled={isBusy}
              className="w-full bg-black/40 border border-white/10 rounded-2xl px-6 py-4 outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all text-white placeholder:text-gray-600 disabled:opacity-50"
            />
          </div>

          <div className="flex flex-col gap-3 text-left">
            <label className="text-sm font-semibold text-gray-300 ml-2">Fontes de Pesquisa</label>
            <div className="flex flex-wrap gap-3">
              {[
                { id: "maps", label: "Google Maps" },
                { id: "instagram", label: "Instagram" },
                { id: "linkedin", label: "LinkedIn" },
                { id: "facebook", label: "Facebook" }
              ].map(src => (
                <label 
                  key={src.id} 
                  className={`flex items-center gap-2 px-4 py-3 rounded-xl border cursor-pointer transition-all ${
                    sources.includes(src.id) 
                      ? "bg-blue-500/20 border-blue-500/50 text-blue-300" 
                      : "bg-black/40 border-white/10 text-gray-400 hover:bg-white/5"
                  } ${isBusy ? "opacity-50 pointer-events-none" : ""}`}
                >
                  <input 
                    type="checkbox" 
                    className="hidden"
                    checked={sources.includes(src.id)}
                    onChange={() => toggleSource(src.id)}
                    disabled={isBusy}
                  />
                  <span className="text-sm font-medium">{src.label}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-2 text-left">
            <label className="text-sm font-semibold text-gray-300 ml-2">Prompt Customizado (Opcional)</label>
            <textarea 
              placeholder="Ex: Buscar empresas com site ruim, sem foto de capa no maps..."
              value={prompt}
              onChange={e => setPrompt(e.target.value)}
              disabled={isBusy}
              className="w-full bg-black/40 border border-white/10 rounded-2xl px-6 py-4 outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all text-white placeholder:text-gray-600 min-h-[100px] resize-y disabled:opacity-50"
            />
          </div>

          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex flex-col gap-2 text-left w-full md:w-1/2">
              <label className="text-sm font-semibold text-gray-300 ml-2">Meta de Leads (Qtde Exata)</label>
              <input 
                type="number" 
                value={maxResults}
                onChange={e => setMaxResults(Number(e.target.value))}
                disabled={isBusy}
                className="w-full bg-black/40 border border-white/10 rounded-2xl px-6 py-4 outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all text-white disabled:opacity-50"
              />
            </div>
            <div className="flex flex-col gap-2 text-left w-full md:w-1/2">
              <label className="text-sm font-semibold text-gray-300 ml-2">Nota de Corte (0 a 10)</label>
              <input 
                type="number" 
                value={minScore}
                onChange={e => setMinScore(Number(e.target.value))}
                disabled={isBusy}
                className="w-full bg-black/40 border border-white/10 rounded-2xl px-6 py-4 outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all text-white disabled:opacity-50"
                min={0} max={10}
              />
            </div>
          </div>

          {/* Button */}
          {status === "idle" || status === "error" || status === "completed" ? (
            <button 
              onClick={status === "completed" ? handleStart : handleStart}
              className="mt-2 relative w-full overflow-hidden rounded-2xl p-[1px] group"
            >
              <span className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl opacity-70 group-hover:opacity-100 transition-opacity duration-300" />
              <div className="relative flex items-center justify-center gap-3 bg-black px-6 py-4 rounded-2xl text-white font-bold tracking-wide transition-all duration-300 group-hover:bg-opacity-0">
                <Search />
                <span>INICIAR PROSPECÇÃO</span>
              </div>
            </button>
          ) : isBusy ? (
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
