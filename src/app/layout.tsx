
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Velli Prospect | Premium",
  description: "Sistema avançado de prospecção e IA",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body className={`${inter.className} flex min-h-screen bg-[#0a0a0a] text-white selection:bg-blue-500/30 overflow-x-hidden`}>
        <Sidebar />
        <main className="flex-1 min-w-0 max-h-screen overflow-y-auto">
          {children}
        </main>
      </body>
    </html>
  );
}

