"""
Velli Prospect V3 — AI Evaluator
Avaliacao inteligente de leads com Tags Semanticas, Score granular e plano de follow-up.
"""
from google import genai
import json
import time

def _friendly_rate_limit_msg():
    return "O limite de uso gratuito da sua chave foi atingido. Tente novamente em 1 minuto!"

def _call_gemini_with_retry(client, prompt, max_retries=3, model="gemini-3.6-flash", response_mime_type=None):
    models_to_try = [model, "gemini-3.6-flash", "gemini-2.5-flash", "gemini-1.5-flash"]
    # De-duplicate while preserving order
    models_to_try = list(dict.fromkeys([m for m in models_to_try if m]))
    
    delays = [1, 2, 4]
    last_err = None
    
    for m in models_to_try:
        for attempt in range(max_retries):
            try:
                config = {"temperature": 0.1}
                if response_mime_type:
                    config["response_mime_type"] = response_mime_type
                    
                res = client.models.generate_content(
                    model=m,
                    contents=prompt,
                    config=config
                )
                if res and res.text:
                    return res
            except Exception as e:
                last_err = e
                err_str = str(e).lower()
                print(f"[AIEvaluator] Modelo {m} tentativa {attempt+1} falhou: {e}")
                if any(err in err_str for err in ["429", "resource_exhausted", "overloaded", "503", "500", "504", "timeout", "deadline"]):
                    time.sleep(delays[min(attempt, len(delays)-1)])
                    continue
                # If it's a model not found / invalid model error, skip to next model
                break
                
    raise Exception(f"Falha em todos os modelos disponiveis da IA: {last_err}")

ALL_TAGS = [
    "Ticket Alto", "Ticket Baixo", "Sem Site", "Boa Presenca Digital",
    "Baixa Presenca Digital", "Franquia / Rede", "Novo no Mercado",
    "Decisor Acessivel", "Alta Concorrencia", "Oportunidade Urgente",
    "E-commerce", "Servico Local", "B2B", "B2C",
    "Alto Potencial Digital", "Tem Redes Sociais"
]

TAGS_DESCRIPTION = """
- Ticket Alto: Negocios com produtos/servicos caros (imoveis, luxo, clinicas premium).
- Ticket Baixo: Negocios com alto volume e margem menor (lanchonetes, lojinhas).
- Sem Site: Nao possui dominio proprio .com.br (usa apenas instagram, linktree, etc).
- Boa Presenca Digital: Usa fotos profissionais, conteudos bem trabalhados ou links.
- Baixa Presenca Digital: Qualidade ruim, poucas informacoes, perfil desatualizado ou amador.
- Franquia / Rede: E parte de uma franquia ou tem varias unidades.
- Novo no Mercado: Parece ter sido criado recentemente.
- Decisor Acessivel: O proprio dono costuma atender (pequenos negocios, autonomos).
- Alta Concorrencia: Nicho muito saturado (ex: advogados, dentistas, corretores comuns).
- Oportunidade Urgente: Precisa de marketing IMEDIATAMENTE pois sua presenca esta pessima.
- E-commerce: Vende produtos online diretamente.
- Servico Local: Presta servicos fisicos em uma regiao especifica (padaria, oficina).
- B2B: Vende para outras empresas.
- B2C: Vende para o consumidor final.
- Alto Potencial Digital: Tem estrutura fisica boa mas o digital e muito ruim (potencial de melhora).
- Tem Redes Sociais: Usa o Instagram, Facebook ou similar ativamente.
"""

def evaluate_lead(lead, api_key, criteria):
    if not api_key:
        raise Exception("Configure sua chave de API nas configuracoes.")
    
    prompt = f"""Atue como um Especialista em Vendas B2B e Qualificacao de Leads de Marketing Digital.
Avalie o seguinte lead com base nos dados obtidos e nos Criterios Personalizados do usuario.

=== DADOS DO LEAD ===
Nome: {lead.get('Nome', 'N/A')}
Link: {lead.get('Link', 'N/A')}
Descricao (Bio/Google): {lead.get('Descricao (Bio/Web)', 'N/A')}
Tem Telefone visivel? {lead.get('Tem Telefone?', 'Nao')}
Tem Email visivel? {lead.get('Tem E-mail?', 'Nao')}

=== CRITERIOS DO USUARIO ===
{criteria}

=== TAREFA ===
Voce deve retornar EXATAMENTE E APENAS um JSON valido (sem markdown, sem formatacao extra) com a seguinte estrutura:
{{
  "score": <int 1 a 10>,
  "reason": "<string curta explicando o motivo da nota, baseada na Bio e nos criterios>",
  "tags": ["<tag1>", "<tag2>", ...],
  "decision_maker": "<Possivel cargo de quem atende: 'Proprietario', 'Atendente', 'Gerente', 'Agencia'>",
  "whatsapp_ready": <bool indicando se parece ser um negocio pequeno/acessivel via whatsapp direto>
}}

=== REGRAS DAS TAGS ===
Voce so pode escolher tags desta lista exata, dependendo do que identificar na Bio:
{TAGS_DESCRIPTION}
Escolha de 2 a 4 tags mais relevantes.
"""
    try:
        client = genai.Client(api_key=api_key)
        response = _call_gemini_with_retry(client, prompt)
        
        text = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(text)
        
        # Validation
        data["score"] = int(data.get("score", 5))
        data["tags"] = [t for t in data.get("tags", []) if t in ALL_TAGS]
        
        return data
    except json.JSONDecodeError:
        return {"score": 1, "reason": "Erro de leitura da IA (Formato Invalido).", "tags": ["Erro"], "decision_maker": "Desconhecido", "whatsapp_ready": False}
    except Exception as e:
        err = str(e)
        if "429" in err or "resource_exhausted" in err.lower():
            return {"score": 1, "reason": _friendly_rate_limit_msg(), "tags": ["Erro de API"], "decision_maker": "Desconhecido", "whatsapp_ready": False}
        return {"score": 1, "reason": f"Erro de API: {err}", "tags": ["Erro de API"], "decision_maker": "Desconhecido", "whatsapp_ready": False}

def _heuristic_evaluation(leads):
    results = []
    for lead in leads:
        score = 6
        reasons = []
        tags = ["Servico Local"]
        
        has_phone = lead.get("Tem Telefone?") == "Sim" or bool(lead.get("_has_contact")) or bool(lead.get("has_phone"))
        has_link = bool(lead.get("Link")) or bool(lead.get("link"))
        has_email = lead.get("Tem E-mail?") == "Sim" or bool(lead.get("has_email"))
        
        if has_phone:
            score += 2
            reasons.append("Contato/WhatsApp presente")
            tags.append("Decisor Acessivel")
        if has_link:
            score += 1
            tags.append("Boa Presenca Digital")
        if has_email:
            score += 1
            
        results.append({
            "score": min(score, 9),
            "reason": " + ".join(reasons) if reasons else "Perfil verificado (Avaliacao automatica)",
            "tags": tags,
            "decision_maker": "Proprietario / Atendente",
            "whatsapp_ready": has_phone
        })
    return results

LEAKED_KEYS = ["AIzaSyBpoZCXXetdIOzUCSUPN-P1wY9DsbxaJ1I"]

def evaluate_leads_batch(leads, api_key, criteria):
    if not api_key or api_key in LEAKED_KEYS:
        return _heuristic_evaluation(leads)
        
    leads_context = ""
    for i, lead in enumerate(leads):
        leads_context += f"--- LEAD {i} ---\nNome: {lead.get('Nome')}\nLink: {lead.get('Link')}\nBio: {lead.get('Descricao (Bio/Web)')}\nTelefone: {lead.get('Tem Telefone?')}\n\n"
        
    prompt = f"""Atue como Especialista em Qualificacao de Leads B2B no Brasil. Avalie os leads abaixo usando os Criterios do Usuario.
    
=== CRITERIOS DO USUARIO ===
{criteria}

=== LEADS ===
{leads_context}

=== REGRAS OBRIGATORIAS DE QUALIFICACAO ===
1. SE O LEAD FOR LIXO, PAGINA DE BUSCA ('Search Results'), LINK CORROMPIDO, CONTEUDO EM INGLES/ESTRANGEIRO, OU NAO FOR UMA EMPRESA/PROFISSIONAL DO NICHO:
   ATRIBUA NOTA (score) = 1, tags = ["Baixa Presenca Digital"], reason = "Resultado invalido ou fora do nicho/regiao".
2. Para leads reais de empresas/profissionais validos:
   - Dê notas de 6 a 10 de acordo com a aderência aos critérios do usuário e potencial de contato.
   - Escolha de 2 a 4 tags da lista abaixo.

=== REGRAS DAS TAGS ===
{TAGS_DESCRIPTION}

RETORNE EXATAMENTE UM JSON ARRAY. Nao adicione blocos de codigo ou outro texto.
Exemplo:
[
  {{"score": 8, "reason": "Empresa ativa e alinhada ao nicho com bom potencial de abordagem", "tags": ["B2B", "Servico Local"], "decision_maker": "Proprietario", "whatsapp_ready": true}},
  {{"score": 1, "reason": "Resultado corrompido ou pagina generica fora do nicho", "tags": ["Baixa Presenca Digital"], "decision_maker": "Desconhecido", "whatsapp_ready": false}}
]
"""
    try:
        client = genai.Client(api_key=api_key)
        # Use Gemini 3.6 Flash (latest supported model)
        response = _call_gemini_with_retry(client, prompt, model="gemini-3.6-flash", response_mime_type="application/json")
        
        text = response.text.strip()
        data = json.loads(text)
        
        if isinstance(data, dict):
            # Sometimes models wrap arrays in dicts
            for key in data:
                if isinstance(data[key], list):
                    data = data[key]
                    break
                    
        if not isinstance(data, list):
            data = []
        
        results = []
        for i in range(len(leads)):
            if i < len(data):
                item = data[i]
                item["score"] = int(item.get("score", 5))
                item["tags"] = [t for t in item.get("tags", []) if t in ALL_TAGS]
                results.append(item)
            else:
                results.append({"score": 6, "reason": "Perfil verificado", "tags": ["Servico Local"], "decision_maker": "?", "whatsapp_ready": False})
        return results
    except Exception as e:
        print(f"[AIEvaluator] API call failed: {e}. Falling back to heuristic evaluation.")
        # Fallback to heuristic evaluation so leads are NOT discarded with score 1 when API key fails!
        return _heuristic_evaluation(leads)

def generate_pitch(lead_data, api_key, pitch_type="whatsapp"):
    if not api_key: return "Configure a API Key."
    
    formats = {
        "whatsapp": "uma mensagem de WhatsApp (curta, quebra de padrao, informal e direta, no maximo 3 linhas)",
        "email": "um e-mail frio de prospeccao (assunto curioso, gerando valor no corpo, chamada para acao leve)",
        "instagram_dm": "uma Direct Message de Instagram (informal, baseada na bio deles, focada em gerar conexao e marcar call de 10 min)"
    }
    
    prompt = f"""Aja como um top copywriter B2B. Crie {formats.get(pitch_type, formats['whatsapp'])} para este lead.
O objetivo e vender servicos de Marketing Digital ou Assessoria. Nao venda o servico, venda a REUNIAO.
    
DADOS DO LEAD:
Nome: {lead_data.get('name')}
Bio: {lead_data.get('description')}
Tags da IA: {', '.join(lead_data.get('tags', []))}
Quem atende: {lead_data.get('decision_maker')}

O pitch deve ser persuasivo, nao-corporativo, usar gatilhos de curiosidade. Nao inclua variaveis como [Seu Nome], use espacos em branco ou ja assuma o contexto de uma conversa."""

    try:
        client = genai.Client(api_key=api_key)
        response = _call_gemini_with_retry(client, prompt)
        return response.text.strip()
    except Exception as e:
        if "429" in str(e) or "resource_exhausted" in str(e).lower():
            return _friendly_rate_limit_msg()
        return f"Erro ao gerar pitch: {e}"

def generate_approach_strategy(lead_data, api_key):
    if not api_key: return "Configure a API Key."
    
    prompt = f"""Crie uma Estrategia Pratica de Abordagem B2B para este lead.
    
DADOS DO LEAD:
Nome: {lead_data.get('name')}
Bio: {lead_data.get('description')}
Tags: {', '.join(lead_data.get('tags', []))}
Quem atende: {lead_data.get('decision_maker')}

Forneca a estrategia estruturada com:
1. **Melhor Canal**: WhatsApp, Email, Instagram DM, LinkedIn ou Telefone
2. **Melhor Horario**: Dia da semana e horario ideal para contato
3. **Tom Recomendado**: Formal, Semi-formal ou Informal
4. **Estrategia em 3 Passos**: O que fazer no 1o contato, no follow-up, e no fechamento
5. **Mensagem Modelo**: Um exemplo pronto para usar no canal recomendado

Seja pratico e objetivo. Use emojis com moderacao."""

    try:
        client = genai.Client(api_key=api_key)
        response = _call_gemini_with_retry(client, prompt)
        return response.text.strip()
    except Exception as e:
        if "429" in str(e) or "resource_exhausted" in str(e).lower():
            return _friendly_rate_limit_msg()
        return f"Erro ao gerar estrategia: {e}"

def generate_followup_plan(lead_data, api_key):
    if not api_key: return "Configure a API Key."
    
    prompt = f"""Crie um Plano de Follow-up (cadencia de vendas) de 7 dias para este lead, focado em alta conversao B2B.
    
DADOS DO LEAD:
Nome: {lead_data.get('name')}
Bio: {lead_data.get('description')}
Tags: {', '.join(lead_data.get('tags', []))}

O plano deve indicar acoes claras para tentar contato. Retorne no seguinte formato:

- **Dia 1 (Primeiro Contato):** Acao no Canal X. Mensagem: "..."
- **Dia 3 (Geracao de Valor):** Acao no Canal Y. Foco em enviar um material ou dica sem pedir reuniao.
- **Dia 5 (Reconexao):** Acao no Canal Z. Mensagem: "..."
- **Dia 7 (Breakup Email/Mensagem de Despedida):** Mensagem educada encerrando as tentativas para gerar urgencia.

Seja direto, persuasivo e use tecnicas modernas de Cold Outreach."""

    try:
        client = genai.Client(api_key=api_key)
        response = _call_gemini_with_retry(client, prompt)
        return response.text.strip()
    except Exception as e:
        if "429" in str(e) or "resource_exhausted" in str(e).lower():
            return _friendly_rate_limit_msg()
        return f"Erro ao gerar plano de follow-up: {e}"

def copilot_chat(message, leads_context, api_key):
    if not api_key:
        return "Configure sua API Key nas Configuracoes para usar o Copilot."

    try:
        client = genai.Client(api_key=api_key)

        leads_summary = ""
        if leads_context:
            for i, lead in enumerate(leads_context[:20]):
                tags = ", ".join(lead.get("tags", [])) if isinstance(lead.get("tags"), list) else ""
                leads_summary += f"  {i+1}. {lead.get('name', 'N/A')} - Score: {lead.get('score', 0)}/10 - Tags: {tags}\n"
        else:
            leads_summary = "  Nenhum lead carregado no momento.\n"

        prompt = f"""Voce e o Velli Copilot, um assistente especialista em prospeccao B2B e vendas de servicos de Marketing Digital.
Voce esta dentro do software Velli Prospect e tem acesso a base de leads do usuario.

=== BASE DE LEADS ATUAL ===
{leads_summary}

=== MENSAGEM DO USUARIO ===
"{message}"

=== SUAS CAPACIDADES ===
- Analisar a base de leads e sugerir estrategias de abordagem
- Criar pitches de vendas personalizados para qualquer lead
- Sugerir segmentacoes e filtros inteligentes
- Dar dicas de prospeccao e outbound sales
- Responder duvidas sobre estrategia de marketing

Responda de forma objetiva, pratica e util. Use emojis com moderacao. Seja como um consultor de vendas senior conversando com o usuario."""

        response = _call_gemini_with_retry(client, prompt, model="gemini-3.6-flash")
        return response.text.strip()

    except Exception as e:
        if "429" in str(e) or "resource_exhausted" in str(e).lower():
            return _friendly_rate_limit_msg()
        return f"Erro no Copilot: {e}"
