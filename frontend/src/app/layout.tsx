
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import { ProspectProvider } from "@/context/ProspectContext";
import GlobalToast from "@/components/GlobalToast";

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
        <ProspectProvider>
          <Sidebar />
          <main className="flex-1 min-w-0 max-h-screen overflow-y-auto pb-20 md:pb-0">
            {children}
          </main>
          <GlobalToast />
        </ProspectProvider>
      </body>
    </html>
  );
}

