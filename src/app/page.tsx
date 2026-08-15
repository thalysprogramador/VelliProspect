
"use client";

import { useState } from "react";
import { Search, Loader2 } from "lucide-react";

export default function Prospect() {
  const [niche, setNiche] = useState("");
  const [region, setRegion] = useState("");
  const [prompt, setPrompt] = useState("");
  const [maxResults, setMaxResults] = useState(50);
  const [minScore, setMinScore] = useState(7);
  const [loading, setLoading] = useState(false);

  const handleStart = async () => {
    if(!niche || !region) return alert("Preencha nicho e regiao");
    setLoading(true);
    try {
      const res = await fetch("https://velli-prospect.onrender.com/api/campaigns", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ niche, region, criteria: prompt, max_results: maxResults, min_score: minScore, source: "maps", block_large_portals: true })
      });
      if(res.ok) {
        alert("Prospeccao iniciada! A IA esta buscando em segundo plano. Va para Campanhas para acompanhar.");
        setNiche(""); setRegion(""); setPrompt("");
      } else {
        alert("Erro ao iniciar.");
      }
    } catch(e) {
      alert("Falha na conexao com o servidor.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-10 lg:p-20 flex flex-col items-center justify-center relative overflow-hidden">
      {/* Background blobs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-600/20 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-600/20 rounded-full blur-[120px] pointer-events-none" />
      
      <div className="w-full max-w-4xl flex flex-col items-center text-center z-10 space-y-6">
        <img src="/logo_full.png" alt="Velli Marketing" className="h-20 mb-2 object-contain" />
        <h1 className="text-5xl lg:text-7xl font-extrabold tracking-tight bg-gradient-to-br from-white to-gray-500 bg-clip-text text-transparent">
          Velli Prospect
        </h1>
        <p className="text-xl text-gray-400 font-medium max-w-2xl">
          Transformando negócios comuns em marcas extraordinárias.
        </p>

        <div className="w-full max-w-2xl mt-12 glass-panel p-8 rounded-3xl flex flex-col gap-6 relative group">
          <div className="absolute inset-0 rounded-3xl bg-gradient-to-b from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
          
          <div className="flex flex-col gap-2 text-left">
            <label className="text-sm font-semibold text-gray-300 ml-2">Qual o nicho alvo?</label>
            <input 
              type="text" 
              placeholder="Ex: Advogados, Clínicas de Estética"
              value={niche}
              onChange={e => setNiche(e.target.value)}
              className="w-full bg-black/40 border border-white/10 rounded-2xl px-6 py-4 outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all text-white placeholder:text-gray-600"
            />
          </div>

          <div className="flex flex-col gap-2 text-left">
            <label className="text-sm font-semibold text-gray-300 ml-2">Qual a região?</label>
            <input 
              type="text" 
              placeholder="Ex: São Paulo, Brasilia"
              value={region}
              onChange={e => setRegion(e.target.value)}
              className="w-full bg-black/40 border border-white/10 rounded-2xl px-6 py-4 outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all text-white placeholder:text-gray-600"
            />
          </div>

          <div className="flex flex-col gap-2 text-left">
            <label className="text-sm font-semibold text-gray-300 ml-2">Prompt Customizado (Opcional)</label>
            <textarea 
              placeholder="Ex: Buscar empresas com site ruim, sem foto de capa no maps..."
              value={prompt}
              onChange={e => setPrompt(e.target.value)}
              className="w-full bg-black/40 border border-white/10 rounded-2xl px-6 py-4 outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all text-white placeholder:text-gray-600 min-h-[100px] resize-y"
            />
          </div>

          <div className="flex gap-4">
            <div className="flex flex-col gap-2 text-left w-1/2">
              <label className="text-sm font-semibold text-gray-300 ml-2">Máximo de Resultados</label>
              <input 
                type="number" 
                value={maxResults}
                onChange={e => setMaxResults(Number(e.target.value))}
                className="w-full bg-black/40 border border-white/10 rounded-2xl px-6 py-4 outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all text-white"
              />
            </div>
            <div className="flex flex-col gap-2 text-left w-1/2">
              <label className="text-sm font-semibold text-gray-300 ml-2">Nota de Corte (0 a 10)</label>
              <input 
                type="number" 
                value={minScore}
                onChange={e => setMinScore(Number(e.target.value))}
                className="w-full bg-black/40 border border-white/10 rounded-2xl px-6 py-4 outline-none focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all text-white"
                min={0} max={10}
              />
            </div>
          </div>

          <button 
            onClick={handleStart}
            disabled={loading}
            className="mt-4 relative w-full overflow-hidden rounded-2xl p-[1px] group disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl opacity-70 group-hover:opacity-100 transition-opacity duration-300" />
            <div className="relative flex items-center justify-center gap-3 bg-black px-6 py-4 rounded-2xl text-white font-bold tracking-wide transition-all duration-300 group-hover:bg-opacity-0">
              {loading ? <Loader2 className="animate-spin" /> : <Search />}
              <span>{loading ? "INICIANDO VARREDURA..." : "INICIAR PROSPECÇÃO"}</span>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}

