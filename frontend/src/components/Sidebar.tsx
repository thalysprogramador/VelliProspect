
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
    <aside className="w-24 min-h-screen flex flex-col items-center py-8 glass-panel sticky top-0 border-r border-white/5 z-50">
      <div className="mb-12">
        <img src="/logo_icon.png" alt="Velli Prospect" className="w-14 h-14 rounded-xl object-cover" />
      </div>
      <nav className="flex flex-col gap-6 flex-1">
        {links.map((link) => {
          const isActive = pathname === link.href || (link.href !== "/" && pathname.startsWith(link.href));
          const Icon = link.icon;
          return (
            <Link 
              key={link.href} 
              href={link.href}
              className={`flex flex-col items-center gap-1.5 px-2 py-3 rounded-2xl transition-all duration-300 ${
                isActive 
                  ? "bg-white/10 text-white shadow-[0_0_15px_rgba(255,255,255,0.1)]" 
                  : "text-gray-500 hover:text-white hover:bg-white/5"
              }`}
            >
              <Icon size={22} className={isActive ? "text-blue-500" : ""} strokeWidth={isActive ? 2.5 : 2} />
              <span className="text-[10px] font-semibold tracking-wide uppercase">{link.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
