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
          const found = data.total_found || 0;
          const approved = data.total_approved || 0;
          const discarded = data.total_discarded || 0;
          const target = data.max_results || maxResults || 10;
          
          // Always update counters in real-time
          setTotalFound(found);
          setTotalApproved(approved);
          setTotalDiscarded(discarded);
          
          if (data.status === "completed") {
            // Show final evaluating state briefly before completing
            setStatus("evaluating");
            setProgressPercent(95);
            setStatusMessage(`Finalizando análise... ${approved} leads qualificados de ${found} encontrados.`);
            
            // After 1.5s, show completed
            setTimeout(() => {
              setStatus("completed");
              setProgressPercent(100);
              setStatusMessage(`Prospecção finalizada! ${approved} leads qualificados encontrados.`);
            }, 1500);
            if (pollRef.current) clearInterval(pollRef.current);
          } else if (data.status === "error") {
            setStatus("error");
            setStatusMessage(data.status_message || "Ocorreu um erro durante a prospecção.");
            setProgressPercent(0);
            if (pollRef.current) clearInterval(pollRef.current);
          } else {
            // Campaign still running - show distinct phases
            const evaluated = approved + discarded;
            
            if (found === 0) {
              // Phase 1: Searching
              setStatus("scraping");
              setProgressPercent(5);
              setStatusMessage("🔍 Buscando empresas na região informada...");
            } else if (evaluated < found) {
              // Phase 2: Evaluating with AI
              setStatus("evaluating");
              const evalPercent = Math.min(90, Math.round((evaluated / found) * 90) + 10);
              setProgressPercent(evalPercent);
              setStatusMessage(`🤖 Analisando com IA... Aprovados: ${approved}/${target} | Avaliados: ${evaluated}/${found}`);
            } else {
              // Phase 3: All evaluated, waiting for completion
              setStatus("evaluating");
              const percentValue = Math.min(95, Math.round((approved / target) * 95));
              setProgressPercent(isNaN(percentValue) ? 90 : percentValue);
              setStatusMessage(`✅ Aprovados: ${approved}/${target} | Descartados: ${discarded} | Concluindo...`);
            }
          }
        }
      } catch {
        // Connection error, keep trying
      }
    }, 1500);

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
    setTotalFound(0);
    setTotalApproved(0);
    setTotalDiscarded(0);
    setProgressPercent(0);
    
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 90000); // 90 seconds (Render cold start can take 60s)
      
      const res = await fetch("https://velli-prospect.onrender.com/api/campaigns", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({ 
          niche, region, criteria: prompt, 
          max_results: maxResults, min_score: minScore, 
          source: sources,
          block_large_portals: true 
        })
      });
      clearTimeout(timeoutId);
      
      if (res.ok) {
        const data = await res.json();
        const cid = data.campaign?.id ? String(data.campaign.id) : null;
        setCampaignId(cid);
        
        if (data.status === "completed" && cid) {
          setStatus("completed");
          setTotalFound(data.campaign?.total_found || 0);
          setTotalApproved(data.campaign?.total_approved || 0);
          setTotalDiscarded(data.campaign?.total_discarded || 0);
          setProgressPercent(100);
          setStatusMessage(data.campaign?.status_message || "Prospecção concluída com sucesso!");
        } else {
          setStatus("scraping");
          setStatusMessage("Fazendo varredura... buscando empresas na região informada...");
        }
      } else {
        setStatus("error");
        setStatusMessage("Erro ao iniciar campanha: " + res.statusText);
      }
    } catch (e: any) {
      setStatus("error");
      if (e.name === "AbortError") {
        setStatusMessage("O seu navegador ou antivírus bloqueou a conexão. Desative o AdBlock e tente novamente.");
      } else {
        setStatusMessage("Erro de conexão com servidor. Verifique sua internet ou AdBlock.");
      }
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
