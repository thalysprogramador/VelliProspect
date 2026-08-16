"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Rocket, Folder, Sparkles, Settings } from "lucide-react";

export default function Sidebar() {
  const pathname = usePathname();

  const links = [
    { href: "/", label: "Prospectar", icon: Rocket },
    { href: "/campaigns", label: "Campanhas", icon: Folder },
    { href: "/copilot", label: "VELLIX IA", icon: Sparkles },
    { href: "/settings", label: "Config", icon: Settings },
  ];

  return (
    <aside className="fixed bottom-0 left-0 w-full h-20 bg-[#0a0a0a]/95 backdrop-blur-xl border-t border-white/5 z-50 flex flex-row items-center justify-around px-4 md:sticky md:top-0 md:w-24 md:min-h-screen md:flex-col md:py-8 glass-panel md:border-r md:border-t-0 md:justify-start">
      <div className="hidden md:block mb-12">
        <img src="/logo_icon.png?v=4_force_refresh" alt="Velli Prospect" className="w-14 h-14 rounded-xl object-contain bg-black" />
      </div>
      <nav className="flex flex-row md:flex-col gap-2 md:gap-6 w-full md:w-auto justify-around flex-1 md:flex-none">
        {links.map((link) => {
          const isActive = pathname === link.href || (link.href !== "/" && pathname.startsWith(link.href));
          const Icon = link.icon;
          return (
            <Link 
              key={link.href} 
              href={link.href}
              className={`flex flex-col items-center gap-1.5 px-3 md:px-2 py-3 rounded-2xl transition-all duration-300 ${
                isActive 
                  ? "bg-white/10 text-white shadow-[0_0_15px_rgba(255,255,255,0.1)]" 
                  : "text-gray-500 hover:text-white hover:bg-white/5"
              }`}
            >
              <Icon size={22} className={isActive ? "text-blue-500" : ""} strokeWidth={isActive ? 2.5 : 2} />
              <span className="text-[10px] font-semibold tracking-wide uppercase hidden sm:block md:block">{link.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
