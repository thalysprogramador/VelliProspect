"use client";

import React, { createContext, useContext, useState, useEffect, useRef } from "react";

type ProspectStatus = "idle" | "starting" | "scraping" | "evaluating" | "completed" | "error";

interface ProspectContextProps {
  niche: string;
  setNiche: (val: string) => void;
  region: string;
  setRegion: (val: string) => void;
  prompt: string;
  setPrompt: (val: string) => void;
  maxResults: number;
  setMaxResults: (val: number) => void;
  minScore: number;
  setMinScore: (val: number) => void;
  sources: string[];
  setSources: (val: string[]) => void;
  status: ProspectStatus;
  setStatus: (val: ProspectStatus) => void;
  statusMessage: string;
  setStatusMessage: (val: string) => void;
  campaignId: string | null;
  totalApproved: number;
  totalDiscarded: number;
  totalFound: number;
  progressPercent: number;
  handleStart: () => Promise<void>;
  handleCancel: () => Promise<void>;
  handleReset: () => void;
}

const ProspectContext = createContext<ProspectContextProps | undefined>(undefined);

export function ProspectProvider({ children }: { children: React.ReactNode }) {
  const [niche, setNiche] = useState("");
  const [region, setRegion] = useState("");
  const [prompt, setPrompt] = useState("");
  const [maxResults, setMaxResults] = useState(10);
  const [minScore, setMinScore] = useState(7);
  const [sources, setSources] = useState<string[]>(["maps"]);
  const [status, setStatus] = useState<ProspectStatus>("idle");
  const [statusMessage, setStatusMessage] = useState("");
  const [campaignId, setCampaignId] = useState<string | null>(null);
  const [totalApproved, setTotalApproved] = useState(0);
  const [totalDiscarded, setTotalDiscarded] = useState(0);
  const [totalFound, setTotalFound] = useState(0);
  const [progressPercent, setProgressPercent] = useState(0);
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
            setTotalApproved(data.total_approved || 0);
            setTotalDiscarded(data.total_discarded || 0);
            setTotalFound(data.total_found || 0);
            setProgressPercent(100);
            setStatusMessage(`Prospecção finalizada! ${data.total_approved || 0} leads qualificados encontrados.`);
            if (pollRef.current) clearInterval(pollRef.current);
          } else {
            setStatus("scraping");
            const found = data.total_found || 0;
            const approved = data.total_approved || 0;
            const discarded = data.total_discarded || 0;
            const target = data.max_results || maxResults || 10;
            const percent = Math.min(100, Math.round((approved / target) * 100));
            
            setTotalFound(found);
            setTotalApproved(approved);
            setTotalDiscarded(discarded);
            setProgressPercent(percent);
            
            setStatusMessage(`Analisando... Aprovados: ${approved}/${target} (${percent}%) | Avaliados: ${approved + discarded}/${found}`);
          }
        }
      } catch {
        // Connection error, keep trying
      }
    }, 5000);

    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [campaignId, status]);

  const handleStart = async () => {
    if (!niche || !region || sources.length === 0) {
      setStatus("error");
      setStatusMessage("Preencha o nicho, a região e escolha ao menos uma fonte antes de iniciar.");
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
          source: sources, // now passing array
          block_large_portals: true 
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
    // NÃO limpa mais o niche, region, prompt, sources, maxResults, minScore (Persistência)
  };

  return (
    <ProspectContext.Provider value={{
      niche, setNiche,
      region, setRegion,
      prompt, setPrompt,
      maxResults, setMaxResults,
      minScore, setMinScore,
      sources, setSources,
      status, setStatus,
      statusMessage, setStatusMessage,
      campaignId, setCampaignId,
      totalApproved, totalDiscarded, totalFound, progressPercent,
      handleStart, handleCancel, handleReset
    }}>
      {children}
    </ProspectContext.Provider>
  );
}

export function useProspect() {
  const context = useContext(ProspectContext);
  if (context === undefined) {
    throw new Error("useProspect must be used within a ProspectProvider");
  }
  return context;
}
