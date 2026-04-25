import streamlit as st
import pandas as pd
from scraper import scrape_leads
from ai_evaluator import evaluate_lead
import time

# --- Setup Página ---
st.set_page_config(page_title="VELLI PROSPECT V2", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# --- CSS Customizado ---
st.markdown("""
<style>
    .velli-title {
        background: -webkit-linear-gradient(45deg, #FF4B4B, #FF904B);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        font-weight: 900;
        font-size: 3.5rem !important;
        margin-bottom: 0px;
    }
    .velli-subtitle {
        text-align: center;
        color: #A0AEC0;
        font-size: 1.2rem;
        margin-bottom: 30px;
    }
    .metric-card {
        background-color: #1E2127;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- Cabeçalho Visual ---
st.markdown('<h1 class="velli-title">⚡ VELLI PROSPECT V2</h1>', unsafe_allow_html=True)
st.markdown('<p class="velli-subtitle">O software definitivo de mineração B2B com Inteligência Artificial</p>', unsafe_allow_html=True)

# --- Sidebar / Cofre de Chaves ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3651/3651239.png", width=80)
    st.header("⚙️ Motor de IA")
    api_key = st.text_input("Cole aqui sua Gemini API Key", type="password", help="Chave gratuita do AI Studio.")
    st.info("O Velli Prospect usa a inteligência do Google para ler a bio de cada empresa e entregar apenas as melhores.")

    st.markdown("---")
    st.markdown("🟢 **Status:** V2 Online e Otimizado")

# --- Interface Principal em Abas ---
tab_busca, tab_resultados = st.tabs(["🎯 Configurar Nova Prospecção", "📊 Painel de Leads"])

with tab_busca:
    with st.container(border=True):
        st.subheader("1. Onde e Quem buscar?")
        col1, col2, col3 = st.columns(3)
        with col1:
            niche = st.text_input("Qual o Nicho? (ex: Escritório de Contabilidade)", "Estética")
        with col2:
            region = st.text_input("Qual a Região? (ex: Belo Horizonte)", "São Paulo")
        with col3:
            source = st.selectbox("Qual a Fonte?", ["Instagram", "Google Mapas/Sites (Geral)"])

    with st.container(border=True):
        st.subheader("2. Filtros de Inteligência (A Cirurgia)")
        colA, colB = st.columns([2, 1])
        
        with colA:
            criteria = st.text_area("Descreva o lead dos sonhos para a IA:", height=130, 
                                  value="Procure empresas que parecem pequenas ou não têm site profissional. Exclua qualquer clínica que pareça gigantesca ou rede de franquias.")
        with colB:
            st.markdown("**Regulagem da Peneira:**")
            min_score = st.slider("Nota Mínima exigida para Aprovar (0 a 10)", 1, 10, 7)
            require_contact = st.checkbox("Exigir Telefone Ou Email na Bio?", value=False, help="Se marcado, ignora perfis que não tenham deixado contato visível.")
            block_portals = st.checkbox("Bloquear grandes portais (G1, etc)", value=True)
            max_results = st.number_input("Tamanho da Varredura na internet", min_value=10, max_value=100, value=25)

    if st.button("🚀 EXECUTAR VARREDURA MÁGICA", use_container_width=True, type="primary"):
        if not niche or not region or not api_key:
            st.error("⚠️ Atenção: Preecha o Nicho, Região e a sua Chave Gemini API (no menu lateral) antes de continuar.")
        else:
            with st.spinner(f"🔍 Vasculhando a internet em '{region}' atrás de '{niche}'... Pode demorar alguns segundos."):
                raw_leads = scrape_leads(niche, region, source, max_results=max_results, block_portals=block_portals)
            
            if not raw_leads:
                st.warning("Nenhum dado bruto encontrado. O Google/DuckDuckGo pode ter limitado a busca. Mude os termos ou aguarde.")
            else:
                st.success(f"🌐 Extraímos {len(raw_leads)} perfis na internet! A IA vai analisar agora:")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                approved_leads = []
                discarded_count = 0
                
                for i, lead in enumerate(raw_leads):
                    status_text.text(f"⏳ A IA está lendo o perfil: {lead['Nome'][:30]}...")
                    
                    # Filtro Rápido (Contato)
                    if require_contact and not lead['_has_contact']:
                        discarded_count += 1
                        progress_bar.progress((i + 1) / len(raw_leads))
                        continue
                    
                    # Filtro de Inteligência (Gemini)
                    justificativa, nota = evaluate_lead(lead, api_key, criteria)
                    
                    if int(nota) >= min_score:
                        lead['Nota Velli (0-10)'] = f"⭐ {nota}"
                        lead['Veredito da IA'] = justificativa
                        # Puxa pro início da tabela
                        approved_leads.append(lead)
                    else:
                        discarded_count += 1
                        
                    progress_bar.progress((i + 1) / len(raw_leads))
                    time.sleep(3) # Pausa pra API grátis
                
                status_text.text("✅ Análise da Inteligência Artificial Finalizada!")
                time.sleep(1)
                
                # Salvar no session state
                st.session_state['last_results'] = approved_leads
                st.session_state['total_found'] = len(raw_leads)
                st.session_state['discarded'] = discarded_count

with tab_resultados:
    st.subheader("📊 Painel Analítico dos Leads")
    
    if 'last_results' in st.session_state:
        # Métricas no Topo
        m1, m2, m3 = st.columns(3)
        m1.metric("🌐 Perfis Lidos", st.session_state['total_found'])
        m2.metric("🏆 Leads Aprovados (Ouro)", len(st.session_state['last_results']))
        m3.metric("🗑️ Lixo Descartado (Reprovado)", st.session_state['discarded'])
        
        if st.session_state['last_results']:
            st.markdown("---")
            # Tabela Gourmet
            df = pd.DataFrame(st.session_state['last_results'])
            
            # Removemos a flag interna pra ficar bonitinho
            if '_has_contact' in df.columns:
                df = df.drop(columns=['_has_contact'])
                
            st.dataframe(df, use_container_width=True, height=400)
            
            st.markdown("<br>", unsafe_allow_html=True)
            # Botão de Download Enfatizado
            csv = df.to_csv(index=False).encode('utf-8')
            col_d1, col_d2, col_d3 = st.columns([1,2,1])
            with col_d2:
                st.download_button(
                    label="📥 BAIXAR LISTA DE LEADS (PLANILHA EXCEL/CSV)",
                    data=csv,
                    file_name=f'Velli_Leads_Premium.csv',
                    mime='text/csv',
                    use_container_width=True,
                    type="primary"
                )
        else:
            st.info("Nenhum lead sobreviveu aos seus critérios rigorosos. Tente diminuir a 'Nota Mínima' ou desmarcar a exigência de contato.")
    else:
        st.info("Faça uma busca na aba 'Configurar Nova Prospecção' para os resultados preencherem este painel.")
