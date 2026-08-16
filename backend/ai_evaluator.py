"""
Velli Prospect V3 — AI Evaluator
Avaliacao inteligente de leads com Tags Semanticas, Score granular e plano de follow-up.
"""
from google import genai
import json
import time

def _friendly_rate_limit_msg():
    return "O limite de uso gratuito da sua chave foi atingido. Tente novamente em 1 minuto!"

def _call_gemini_with_retry(client, prompt, max_retries=3, model="gemini-1.5-flash-latest"):
    delays = [5, 10, 20]
    last_err = None
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(
                model=model,
                contents=prompt,
                config={"temperature": 0.2}
            )
        except Exception as e:
            last_err = e
            err_str = str(e).lower()
            if "429" in err_str or "resource_exhausted" in err_str:
                if attempt < max_retries - 1:
                    time.sleep(delays[attempt])
                continue
            raise
    raise Exception(f"Falha apos {max_retries} tentativas: {last_err}")

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

def evaluate_leads_batch(leads, api_key, criteria):
    if not api_key:
        return [{"score": 1, "reason": "Configure sua chave de API.", "tags": [], "decision_maker": "?", "whatsapp_ready": False} for _ in leads]
        
    leads_context = ""
    for i, lead in enumerate(leads):
        leads_context += f"--- LEAD {i} ---\nNome: {lead.get('Nome')}\nLink: {lead.get('Link')}\nBio: {lead.get('Descricao (Bio/Web)')}\nTelefone: {lead.get('Tem Telefone?')}\n\n"
        
    prompt = f"""Atue como Especialista de Vendas. Avalie os leads abaixo usando os Criterios do Usuario.
    
=== CRITERIOS ===
{criteria}

=== LEADS ===
{leads_context}

=== REGRAS DAS TAGS (Escolha de 2 a 4 por lead) ===
{TAGS_DESCRIPTION}

RETORNE EXATAMENTE UM JSON ARRAY. Nao adicione blocos de codigo ou outro texto.
Exemplo:
[
  {{"score": 8, "reason": "Motivo curto", "tags": ["B2B", "Servico Local"], "decision_maker": "Proprietario", "whatsapp_ready": true}},
  {{"score": 3, "reason": "Motivo curto", "tags": ["Alta Concorrencia"], "decision_maker": "Atendente", "whatsapp_ready": false}}
]
"""
    try:
        client = genai.Client(api_key=api_key)
        response = _call_gemini_with_retry(client, prompt)
        
        text = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(text)
        
        # Validacao e correcao
        results = []
        for i in range(len(leads)):
            if i < len(data):
                item = data[i]
                item["score"] = int(item.get("score", 5))
                item["tags"] = [t for t in item.get("tags", []) if t in ALL_TAGS]
                results.append(item)
            else:
                results.append({"score": 1, "reason": "Erro: Lead omitido pela IA.", "tags": ["Avaliacao Incompleta"], "decision_maker": "?", "whatsapp_ready": False})
        return results
    except Exception as e:
        err = str(e)
        if "429" in err or "resource_exhausted" in err.lower():
            err_reason = _friendly_rate_limit_msg()
            err_tag = "Erro de API"
        else:
            err_reason = f"Erro no lote: {err[:50]}"
            err_tag = "Erro"
            
        return [{"score": 1, "reason": err_reason, "tags": [err_tag], "decision_maker": "Desconhecido", "whatsapp_ready": False} for _ in leads]

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

        response = _call_gemini_with_retry(client, prompt, model="gemini-1.5-flash-latest")
        return response.text.strip()

    except Exception as e:
        if "429" in str(e) or "resource_exhausted" in str(e).lower():
            return _friendly_rate_limit_msg()
        return f"Erro no Copilot: {e}"
