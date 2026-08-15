
"use client";

import { useState } from "react";
import { Sparkles, Send } from "lucide-react";

export default function Copilot() {
  const [messages, setMessages] = useState([{ role: "assistant", text: "Olá! Sou o Vellix, sua IA de prospecção. Como posso ajudar você a fechar mais negócios hoje?" }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if(!input) return;
    const newMsgs = [...messages, { role: "user", text: input }];
    setMessages(newMsgs);
    setInput("");
    setLoading(true);

    try {
      // In a real implementation this would call a real LLM route on the FastAPI backend
      // But we just simulate the chat flow for the UX
      setTimeout(() => {
        setMessages([...newMsgs, { role: "assistant", text: "Estou analisando sua solicitação com base nos dados do mercado..." }]);
        setLoading(false);
      }, 1000);
    } catch(e) {
      setLoading(false);
    }
  };

  return (
    <div className="p-10 lg:p-16 max-w-4xl mx-auto h-screen flex flex-col">
      <div className="flex items-center gap-4 mb-8">
        <div className="p-3 bg-purple-500/20 rounded-2xl text-purple-400">
          <Sparkles size={28} />
        </div>
        <div>
          <h1 className="text-3xl font-bold">VELLIX IA</h1>
          <p className="text-gray-400">Seu copiloto estratégico para Vendas</p>
        </div>
      </div>

      <div className="flex-1 glass-panel rounded-3xl p-6 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto space-y-6 pr-4">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[80%] p-5 rounded-3xl ${m.role === "user" ? "bg-blue-600 text-white rounded-tr-sm" : "bg-white/5 text-gray-200 border border-white/10 rounded-tl-sm"}`}>
                {m.text}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-white/5 border border-white/10 p-5 rounded-3xl rounded-tl-sm text-gray-400 flex gap-2 items-center">
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" />
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-100" />
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-200" />
              </div>
            </div>
          )}
        </div>

        <div className="mt-6 relative">
          <input 
            type="text" 
            placeholder="Pergunte sobre abordagens, roteiros de venda, ou análise de nicho..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleSend()}
            className="w-full bg-black/50 border border-white/10 rounded-2xl pl-6 pr-16 py-4 outline-none focus:border-purple-500/50 focus:ring-2 focus:ring-purple-500/20 text-white placeholder:text-gray-600"
          />
          <button onClick={handleSend} disabled={loading || !input} className="absolute right-3 top-1/2 -translate-y-1/2 p-2 bg-purple-600 hover:bg-purple-500 disabled:bg-gray-700 rounded-xl text-white transition-colors">
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}

