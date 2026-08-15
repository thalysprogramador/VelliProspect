
"use client";

import { useEffect, useState } from "react";
import { Download, Trash2, ChevronLeft, ExternalLink, Calendar } from "lucide-react";
import * as XLSX from "xlsx"; // Will install this shortly

export default function Campaigns() {
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [selectedCid, setSelectedCid] = useState<string | null>(null);
  const [leads, setLeads] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("https://velli-prospect.onrender.com/api/campaigns")
      .then(r => r.json())
      .then(data => { setCampaigns(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const loadLeads = async (cid: string) => {
    setSelectedCid(cid);
    setLoading(true);
    try {
      const r = await fetch(`https://velli-prospect.onrender.com/api/campaigns/${cid}/leads`);
      const data = await r.json();
      setLeads(data);
    } catch {}
    setLoading(false);
  };

  const handleExport = () => {
    if(!leads.length) return;
    const formatted = leads.map(l => ({
      "Nome da Empresa": l.name || "",
      "Nota (1 a 10)": l.score || "",
      "Status": l.status || "approved",
      "Telefone?": l.has_phone ? "Sim" : "Nao",
      "Email?": l.has_email ? "Sim" : "Nao",
      "Quem Atende": l.decision_maker || "",
      "Tags de Perfil": (l.tags || []).join(", "),
      "Analise da IA": l.reason || "",
      "Link de Contato": l.link || "",
      "Data de Captura": l.created_at || "",
      "Bio Original": l.description || ""
    }));
    const ws = XLSX.utils.json_to_sheet(formatted);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Leads");
    XLSX.writeFile(wb, "Leads_Velli.xlsx");
  };

  if (selectedCid) {
    const camp = campaigns.find(c => c.id === selectedCid);
    return (
      <div className="p-10 lg:p-16 max-w-7xl mx-auto animate-in fade-in zoom-in-95 duration-500">
        <div className="flex items-center justify-between mb-12">
          <div className="flex items-center gap-6">
            <button onClick={() => setSelectedCid(null)} className="p-3 bg-white/5 hover:bg-white/10 rounded-full transition-colors">
              <ChevronLeft size={24} />
            </button>
            <h1 className="text-4xl font-bold">{camp?.name}</h1>
          </div>
          <button onClick={handleExport} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-2xl font-bold transition-all shadow-[0_0_20px_rgba(0,122,255,0.3)]">
            <Download size={18} /> Exportar Excel
          </button>
        </div>

        <div className="grid gap-6">
          {loading ? (
            <div className="text-center py-20 text-gray-500">Carregando leads...</div>
          ) : leads.map(l => (
            <div key={l.id} className="glass-panel p-6 rounded-3xl flex gap-6 items-start hover:border-white/20 transition-all">
              <div className={`flex items-center justify-center w-12 h-12 rounded-full font-bold text-xl ${l.score >= 8 ? "bg-green-500/20 text-green-400" : l.score >= 5 ? "bg-yellow-500/20 text-yellow-400" : "bg-red-500/20 text-red-400"}`}>
                {l.score}
              </div>
              <div className="flex-1">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-xl font-bold flex items-center gap-3">
                      {l.name}
                      {l.link && <a href={l.link} target="_blank" rel="noreferrer" className="text-blue-400 hover:text-blue-300"><ExternalLink size={16} /></a>}
                    </h3>
                    <p className="text-gray-400 text-sm mt-1 mb-3">{l.description}</p>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2 mb-4">
                  {(l.tags || []).map((t: string) => <span key={t} className="bg-white/5 text-gray-300 px-3 py-1 text-xs font-semibold rounded-full">{t}</span>)}
                </div>
                <p className="text-sm italic text-gray-500">&quot;{l.reason}&quot;</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-10 lg:p-16 max-w-7xl mx-auto">
      <h1 className="text-4xl font-bold mb-4">Campanhas</h1>
      <p className="text-gray-400 mb-12">Gerencie e exporte seus leads estruturados com IA.</p>
      
      {loading ? (
        <div className="text-center py-20 text-gray-500">Carregando campanhas...</div>
      ) : (
        <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-6">
          {campaigns.map(c => (
            <div key={c.id} onClick={() => loadLeads(c.id)} className="glass-panel p-8 rounded-3xl cursor-pointer hover:-translate-y-1 hover:shadow-[0_10px_30px_rgba(0,0,0,0.5)] hover:border-white/20 transition-all group relative">
              <div className="flex justify-between items-start mb-6">
                <h3 className="text-xl font-bold group-hover:text-blue-400 transition-colors">{c.name}</h3>
                <span className={`text-xs font-bold px-3 py-1 rounded-full ${c.status === "completed" ? "bg-green-500/20 text-green-400" : "bg-yellow-500/20 text-yellow-400"}`}>
                  {c.status === "completed" ? "Concluída" : "Em Andamento"}
                </span>
              </div>
              <p className="text-gray-400 text-sm mb-6">{c.niche} • {c.region} • {c.source}</p>
              <div className="flex items-center justify-between border-t border-white/10 pt-6">
                <div className="flex items-center gap-2 text-gray-500 text-sm">
                  <Calendar size={14} /> {c.created_at?.split("T")[0]}
                </div>
                <div className="text-green-400 font-semibold text-sm">
                  {c.total_approved} leads
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

