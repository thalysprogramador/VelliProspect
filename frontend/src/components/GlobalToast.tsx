"use client";

import { useProspect } from "@/context/ProspectContext";
import { CheckCircle2, Loader2, XCircle } from "lucide-react";
import { usePathname } from "next/navigation";

export default function GlobalToast() {
  const { status, statusMessage } = useProspect();
  const pathname = usePathname();

  // Se já estamos na página inicial, o painel central já mostra o status.
  // Só mostramos o toast global se estivermos fora da página inicial,
  // ou se quiser manter em todo lugar, podemos mostrar sempre.
  if (pathname === "/" && status !== "completed") return null;

  if (status === "idle") return null;

  const isCompleted = status === "completed";
  const isError = status === "error";

  return (
    <div className={`fixed bottom-24 md:bottom-10 right-4 md:right-10 z-50 animate-in slide-in-from-bottom-5 fade-in duration-500`}>
      <div className={`flex items-center gap-3 p-4 rounded-2xl border shadow-2xl backdrop-blur-md ${
        isCompleted ? "bg-green-500/20 border-green-500/30 text-green-100" :
        isError ? "bg-red-500/20 border-red-500/30 text-red-100" :
        "bg-blue-500/20 border-blue-500/30 text-blue-100"
      }`}>
        {!isCompleted && !isError && <Loader2 className="animate-spin text-blue-400" size={20} />}
        {isCompleted && <CheckCircle2 className="text-green-400" size={20} />}
        {isError && <XCircle className="text-red-400" size={20} />}
        <div>
          <p className="text-sm font-bold">{isCompleted ? "Prospecção Concluída!" : isError ? "Erro" : "Prospecção em Andamento"}</p>
          <p className="text-xs opacity-80 max-w-[200px] truncate">{statusMessage}</p>
        </div>
      </div>
    </div>
  );
}
