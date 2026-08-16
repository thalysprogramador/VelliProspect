"use client";

import { useState, useEffect, useRef } from "react";
import { Sparkles, Send, MessageSquare, Plus, Menu, X } from "lucide-react";

type Message = {
  role: "user" | "assistant";
  text: string;
};

type ChatSession = {
  id: string;
  title: string;
  messages: Message[];
};

export default function Copilot() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false); // For mobile
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load from local storage on mount
  useEffect(() => {
    const saved = localStorage.getItem("vellix_chat_sessions");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (parsed.length > 0) {
          setSessions(parsed);
          setCurrentSessionId(parsed[0].id);
        } else {
          createNewSession();
        }
      } catch (e) {
        createNewSession();
      }
    } else {
      createNewSession();
    }
  }, []);

  // Save to local storage whenever sessions change
  useEffect(() => {
    if (sessions.length > 0) {
      localStorage.setItem("vellix_chat_sessions", JSON.stringify(sessions));
    }
  }, [sessions]);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [sessions, currentSessionId, loading]);

  const createNewSession = () => {
    const newId = Date.now().toString();
    const newSession: ChatSession = {
      id: newId,
      title: "Nova Conversa",
      messages: [{ role: "assistant", text: "Olá! Sou o Vellix, sua IA de prospecção. Como posso ajudar você a fechar mais negócios hoje?" }]
    };
    setSessions(prev => [newSession, ...prev]);
    setCurrentSessionId(newId);
    setIsSidebarOpen(false); // Close mobile sidebar if open
  };

  const currentSession = sessions.find(s => s.id === currentSessionId);
  const messages = currentSession?.messages || [];

  const handleSend = async () => {
    if(!input.trim() || !currentSessionId) return;
    
    const userMsg = input.trim();
    setInput("");
    setLoading(true);

    // Update current session with user message
    setSessions(prev => prev.map(s => {
      if (s.id === currentSessionId) {
        // Update title if it's the first user message
        const newTitle = s.messages.length === 1 ? userMsg.substring(0, 30) + "..." : s.title;
        return { ...s, title: newTitle, messages: [...s.messages, { role: "user", text: userMsg }] };
      }
      return s;
    }));

    try {
      const response = await fetch("https://api.render.com/deploy/srv-d7nvkovavr4c73fthevg", { method: "HEAD" }).catch(()=>null); // Just a dummy to wake render if sleeping, ignore errors
      
      // Get the updated history to send
      const historyToSend = currentSession?.messages || [];
      
      const res = await fetch("https://velli-prospect.onrender.com/api/copilot/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          message: userMsg,
          history: historyToSend
        })
      });

      if (!res.ok) {
        throw new Error("Erro na comunicação com a API");
      }

      const data = await res.json();
      
      setSessions(prev => prev.map(s => {
        if (s.id === currentSessionId) {
          return { ...s, messages: [...s.messages, { role: "assistant", text: data.reply || "Resposta vazia." }] };
        }
        return s;
      }));

    } catch(e: any) {
      setSessions(prev => prev.map(s => {
        if (s.id === currentSessionId) {
          return { ...s, messages: [...s.messages, { role: "assistant", text: "Desculpe, ocorreu um erro ao conectar com o servidor. Tente novamente." }] };
        }
        return s;
      }));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-full bg-black text-white relative">
      
      {/* MOBILE OVERLAY */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/60 z-40 lg:hidden backdrop-blur-sm transition-opacity"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* CHAT HISTORY SIDEBAR */}
      <div className={`
        fixed lg:static inset-y-0 left-0 z-50 w-72 bg-[#0a0a0a] border-r border-white/5 
        transform transition-transform duration-300 ease-in-out flex flex-col
        ${isSidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
      `}>
        <div className="p-4 flex items-center justify-between border-b border-white/5">
          <button 
            onClick={createNewSession}
            className="flex-1 flex items-center gap-2 bg-white/5 hover:bg-white/10 transition-colors p-3 rounded-xl text-sm font-medium"
          >
            <Plus size={16} /> Nova Conversa
          </button>
          <button onClick={() => setIsSidebarOpen(false)} className="lg:hidden p-2 text-gray-400 hover:text-white ml-2">
            <X size={20} />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 px-2">Histórico</div>
          {sessions.map(session => (
            <button
              key={session.id}
              onClick={() => { setCurrentSessionId(session.id); setIsSidebarOpen(false); }}
              className={`w-full text-left flex items-center gap-3 p-3 rounded-xl transition-all ${
                currentSessionId === session.id 
                  ? "bg-purple-500/10 text-purple-400 border border-purple-500/20" 
                  : "text-gray-400 hover:bg-white/5 hover:text-gray-200"
              }`}
            >
              <MessageSquare size={16} className="shrink-0" />
              <span className="truncate text-sm">{session.title}</span>
            </button>
          ))}
        </div>
      </div>

      {/* MAIN CHAT AREA */}
      <div className="flex-1 flex flex-col h-full max-h-screen overflow-hidden relative">
        
        {/* HEADER */}
        <div className="p-4 lg:p-8 flex items-center gap-4 shrink-0 border-b lg:border-none border-white/5 bg-black/50 lg:bg-transparent backdrop-blur-md z-10">
          <button 
            onClick={() => setIsSidebarOpen(true)}
            className="lg:hidden p-2 -ml-2 bg-white/5 rounded-xl text-gray-400 hover:text-white"
          >
            <Menu size={20} />
          </button>
          <div className="p-2.5 bg-purple-500/20 rounded-2xl text-purple-400 shrink-0">
            <Sparkles size={24} />
          </div>
          <div>
            <h1 className="text-xl lg:text-3xl font-bold">VELLIX IA</h1>
            <p className="text-xs lg:text-sm text-gray-400 hidden sm:block">Seu copiloto estratégico para Vendas</p>
          </div>
        </div>

        {/* CHAT MESSAGES */}
        <div className="flex-1 overflow-y-auto p-4 lg:px-16 lg:pb-8">
          <div className="max-w-4xl mx-auto space-y-6">
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[90%] lg:max-w-[80%] p-4 lg:p-5 rounded-3xl text-sm lg:text-base whitespace-pre-wrap ${
                  m.role === "user" 
                    ? "bg-blue-600 text-white rounded-tr-sm shadow-[0_0_15px_rgba(37,99,235,0.2)]" 
                    : "bg-white/5 text-gray-200 border border-white/10 rounded-tl-sm glass-panel"
                }`}>
                  {m.text}
                </div>
              </div>
            ))}
            
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white/5 border border-white/10 p-5 rounded-3xl rounded-tl-sm text-gray-400 flex gap-2 items-center glass-panel">
                  <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" />
                  <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-100" />
                  <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-200" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* INPUT AREA */}
        <div className="p-4 lg:p-8 shrink-0 bg-gradient-to-t from-black via-black to-transparent">
          <div className="max-w-4xl mx-auto relative">
            <input 
              type="text" 
              placeholder="Pergunte sobre abordagens, roteiros de venda..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleSend()}
              className="w-full bg-[#141415] border border-white/10 rounded-2xl pl-5 pr-14 py-4 text-sm lg:text-base outline-none focus:border-purple-500/50 focus:ring-2 focus:ring-purple-500/20 text-white placeholder:text-gray-500 shadow-xl"
            />
            <button 
              onClick={handleSend} 
              disabled={loading || !input.trim()} 
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2.5 bg-purple-600 hover:bg-purple-500 disabled:bg-white/5 disabled:text-gray-500 rounded-xl text-white transition-all"
            >
              <Send size={18} />
            </button>
          </div>
          <div className="text-center mt-3 text-[10px] text-gray-600 hidden lg:block">
            VELLIX IA pode cometer erros. Verifique informações importantes.
          </div>
        </div>

      </div>
    </div>
  );
}
