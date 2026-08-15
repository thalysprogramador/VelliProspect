
"use client";

import { useState, useEffect } from "react";
import { Save, Loader2, Eye, EyeOff, CheckCircle2, AlertCircle } from "lucide-react";

export default function Settings() {
  const [apiKey, setApiKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [showKey, setShowKey] = useState(false);
  const [saveStatus, setSaveStatus] = useState<"idle" | "saved" | "error">("idle");

  // Chave padrão como fallback imediato
  const DEFAULT_KEY = "AIzaSyBpoZCXXetdIOzUCSUPN-P1wY9DsbxaJ1I";

  useEffect(() => {
    // Setar a chave padrão imediatamente enquanto busca do servidor
    setApiKey(DEFAULT_KEY);
    
    fetch("https://velli-prospect.onrender.com/api/settings/gemini_api_key")
      .then(r => r.json())
      .then(data => {
        if (data.value) {
          setApiKey(data.value);
        }
        setFetching(false);
      })
      .catch(() => {
        // Mantém a chave padrão se o servidor não responder
        setFetching(false);
      });
  }, []);

  const handleSave = async () => {
    setLoading(true);
    setSaveStatus("idle");
    try {
      const res = await fetch("https://velli-prospect.onrender.com/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key: "gemini_api_key", value: apiKey })
      });
      if (res.ok) {
        setSaveStatus("saved");
        setTimeout(() => setSaveStatus("idle"), 3000);
      } else {
        setSaveStatus("error");
      }
    } catch {
      setSaveStatus("error");
    }
    setLoading(false);
  };

  return (
    <div className="p-10 lg:p-16 max-w-4xl mx-auto">
      <h1 className="text-4xl font-bold mb-4">Configurações</h1>
      <p className="text-gray-400 mb-12">Configure suas chaves de API e preferências do sistema.</p>

      <div className="glass-panel p-8 rounded-3xl grid gap-8">
        <div>
          <label className="block text-sm font-semibold text-gray-300 mb-2">Chave da API Gemini (Google AI Studio)</label>
          <div className="relative">
            <input 
              type={showKey ? "text" : "password"} 
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={fetching ? "Carregando chave..." : "AIzaSy..."} 
              className="w-full bg-black/40 border border-white/10 rounded-2xl px-6 py-4 pr-14 outline-none focus:border-blue-500/50 text-white"
            />
            <button 
              onClick={() => setShowKey(!showKey)} 
              className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white transition-colors"
            >
              {showKey ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
          {fetching && (
            <p className="text-xs text-gray-500 mt-2 flex items-center gap-2">
              <Loader2 className="animate-spin" size={12} /> Buscando chave salva no servidor...
            </p>
          )}
        </div>

        <div className="flex items-center gap-4">
          <button 
            onClick={handleSave} 
            disabled={loading} 
            className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-6 py-4 rounded-2xl font-bold transition-all shadow-[0_0_20px_rgba(0,122,255,0.3)] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? <Loader2 className="animate-spin" /> : <Save size={18} />} Salvar Configurações
          </button>
          
          {saveStatus === "saved" && (
            <span className="flex items-center gap-2 text-green-400 text-sm font-semibold animate-in fade-in duration-300">
              <CheckCircle2 size={16} /> Salvo com sucesso!
            </span>
          )}
          {saveStatus === "error" && (
            <span className="flex items-center gap-2 text-red-400 text-sm font-semibold animate-in fade-in duration-300">
              <AlertCircle size={16} /> Erro ao salvar
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
