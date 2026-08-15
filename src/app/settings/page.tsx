
"use client";

import { Save } from "lucide-react";

export default function Settings() {
  return (
    <div className="p-10 lg:p-16 max-w-4xl mx-auto">
      <h1 className="text-4xl font-bold mb-4">Configurações</h1>
      <p className="text-gray-400 mb-12">Configure suas chaves de API e preferências do sistema.</p>

      <div className="glass-panel p-8 rounded-3xl grid gap-8">
        <div>
          <label className="block text-sm font-semibold text-gray-300 mb-2">Chave da API Gemini (Google AI Studio)</label>
          <input 
            type="password" 
            placeholder="AIzaSy..." 
            className="w-full bg-black/40 border border-white/10 rounded-2xl px-6 py-4 outline-none focus:border-blue-500/50 text-white"
          />
        </div>
        
        <div>
          <label className="block text-sm font-semibold text-gray-300 mb-2">Prompt do Avaliador de Leads</label>
          <textarea 
            rows={4}
            className="w-full bg-black/40 border border-white/10 rounded-2xl px-6 py-4 outline-none focus:border-blue-500/50 text-white"
            placeholder="Você é um especialista em qualificação..."
          />
        </div>

        <button className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-6 py-4 rounded-2xl font-bold transition-all shadow-[0_0_20px_rgba(0,122,255,0.3)]">
          <Save size={18} /> Salvar Configurações
        </button>
      </div>
    </div>
  );
}

