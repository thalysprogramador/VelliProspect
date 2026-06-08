"""
Velli Prospect V3 — AI Evaluator (Revisado)
Avaliacao inteligente de leads com Tags Semanticas expandidas, Score granular e retry automatico.
"""
from google import genai
import json
import time


# ── Retry Logic ──────────────────────────────────────────────────
def _call_gemini_with_retry(client, prompt, max_retries=3):
    """Chama o Gemini com retry automatico para erros 429."""
    for attempt in range(max_retries + 1):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            return response
        except Exception as e:
            error_msg = str(e)
            if ("429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg) and attempt < max_retries:
                wait_time = 5 * (2 ** attempt)  # 5s, 10s, 20s
                print(f"Rate limit atingido, aguardando {wait_time}s... (tentativa {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
            raise


def _friendly_rate_limit_msg():
    """Retorna mensagem amigavel para erro de rate limit."""
    return (
        "\u26a0\ufe0f **Limite de velocidade atingido!** \U0001f605\n\n"
        "O plano gratuito do Google permite ate 15 interacoes por minuto "
        "e voce atingiu esse limite.\n\n"
        "**Aguarde cerca de 40 a 60 segundos** e tente novamente!"
    )


# ── Tags de Segmentacao ──────────────────────────────────────────
ALL_TAGS = [
    "Ticket Alto", "Ticket Baixo",
    "Sem Site", "Boa Presenca Digital", "Baixa Presenca Digital",
    "Franquia / Rede", "Novo no Mercado",
    "Decisor Acessivel", "Alta Concorrencia", "Oportunidade Urgente",
    "E-commerce", "Servico Local", "B2B", "B2C",
    "Alto Potencial Digital", "Tem Redes Sociais",
]

TAGS_DESCRIPTION = """
Tags permitidas (use SOMENTE estas):
   - "Ticket Alto" - Negocio com ticket medio alto
   - "Ticket Baixo" - Micro-empreendedor ou operacao simples
   - "Sem Site" - Nao aparenta ter site profissional
   - "Boa Presenca Digital" - Ja tem presenca online razoavel
   - "Baixa Presenca Digital" - Presenca digital fraca ou inexistente
   - "Franquia / Rede" - Aparenta ser franquia ou rede grande
   - "Novo no Mercado" - Negocio recente
   - "Decisor Acessivel" - O decisor parece acessivel para contato direto
   - "Alta Concorrencia" - Nicho com muita competicao local
   - "Oportunidade Urgente" - Demonstra necessidade urgente de marketing
   - "E-commerce" - Possui loja online ou vende pela internet
   - "Servico Local" - Negocio de servico local (clinica, escritorio, etc)
   - "B2B" - Vende para outras empresas
   - "B2C" - Vende diretamente para consumidor final
   - "Alto Potencial Digital" - Se beneficiaria muito de marketing digital
   - "Tem Redes Sociais" - Possui perfis ativos em redes sociais
"""


def evaluate_lead(lead, api_key, criteria):
    """Avalia um lead usando Gemini e retorna um dicionario rico."""
    if not api_key:
        return {
            "score": 0,
            "reason": "Chave de API nao configurada.",
            "tags": [],
            "decision_maker": "Desconhecido",
            "whatsapp_ready": False
        }

    try:
        client = genai.Client(api_key=api_key)

        prompt = f"""Voce e um analista senior de prospeccao B2B em Marketing Digital.
Analise esta empresa/perfil encontrado na internet e avalie o potencial de COMPRA de servicos de marketing.

=== INSTRUCAO PERSONALIZADA DO USUARIO ===
"{criteria}"

=== DADOS DO PROSPECT ===
- Nome: {lead.get('Nome', 'N/A')}
- Descricao / Bio / Snippet: {lead.get('Descricao (Bio/Web)', lead.get('Descrição (Bio/Web)', 'N/A'))}
- Link: {lead.get('Link', 'N/A')}
- Tem telefone visivel: {'Sim' if lead.get('_has_contact') else 'Nao'}

=== SUA ANALISE DEVE CONTER ===

1. **score** (inteiro 0-10): Nota de potencial de compra.
   - 0-3: Lead frio, sem potencial
   - 4-6: Lead morno, tem potencial mas com ressalvas
   - 7-8: Lead quente, bom prospect
   - 9-10: Lead incandescente, prospect ideal

2. **reason** (string, maximo 2 frases): Justificativa objetiva e curta.

3. **tags** (lista de strings): Classifique o prospect com 2 a 5 tags.
{TAGS_DESCRIPTION}

4. **decision_maker** (string): Chute educado sobre quem e o decisor (ex: "Proprietario", "Gerente", "Socio", "Diretor de Marketing", "Desconhecido")

5. **whatsapp_ready** (boolean): true se ha indicio de telefone/WhatsApp nos dados

=== FORMATO DE RESPOSTA ===
Retorne APENAS um JSON valido, sem markdown, sem explicacao extra:
{{"score": 8, "reason": "...", "tags": ["...", "..."], "decision_maker": "...", "whatsapp_ready": true}}
"""

        response = _call_gemini_with_retry(client, prompt)
        text = response.text.strip()

        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        result = json.loads(text.strip())

        return {
            "score": int(result.get("score", 0)),
            "reason": str(result.get("reason", "Sem justificativa")),
            "tags": list(result.get("tags", [])),
            "decision_maker": str(result.get("decision_maker", "Desconhecido")),
            "whatsapp_ready": bool(result.get("whatsapp_ready", False))
        }

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            return {
                "score": 0,
                "reason": _friendly_rate_limit_msg(),
                "tags": ["Erro de API"],
                "decision_maker": "Desconhecido",
                "whatsapp_ready": False
            }
        return {
            "score": 0,
            "reason": f"Erro na IA: {str(e)[:100]}",
            "tags": ["Erro"],
            "decision_maker": "Desconhecido",
            "whatsapp_ready": False
        }


def evaluate_leads_batch(leads, api_key, criteria):
    """Avalia uma lista inteira de leads de uma so vez (Batching)."""
    if not api_key:
        return [{
            "score": 0,
            "reason": "Chave de API nao configurada.",
            "tags": [],
            "decision_maker": "Desconhecido",
            "whatsapp_ready": False
        } for _ in leads]

    try:
        client = genai.Client(api_key=api_key)

        leads_json_str = json.dumps([{
            "id": i,
            "Nome": l.get('Nome'),
            "Descricao": l.get('Descricao (Bio/Web)', l.get('Descrição (Bio/Web)', '')),
            "Link": l.get('Link'),
            "_has_contact": l.get('_has_contact')
        } for i, l in enumerate(leads)], ensure_ascii=False)

        prompt = f"""Voce e um super-computador de IA analisando potenciais clientes B2B. AVALIE ESTES LEADS EM LOTE.
=== CRITERIOS DE COMPRA ===
"{criteria}"

=== DADOS DOS PROSPECTS (JSON DE ENTRADA) ===
{leads_json_str}

=== INSTRUCOES ===
Retorne APENAS um Array JSON. Cada objeto deve seguir este modelo EXATO:
{{
  "id": <id original do lead da entrada>,
  "score": <nota 0-10 baseada no potencial>,
  "reason": "<justificativa muito curta e objetiva: 1 frase so>",
  "tags": ["<tag1>", "<tag2>"],
  "decision_maker": "<provavel decisor>",
  "whatsapp_ready": <true se _has_contact for true, senao false>
}}
{TAGS_DESCRIPTION}
IMPORTANTE: NAO escreva mais NADA alem do array JSON (iniciando com [ e fechando com ]).
"""

        response = _call_gemini_with_retry(client, prompt)
        text = response.text.strip()

        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        results_array = json.loads(text.strip())
        evaluations = {r.get("id"): r for r in results_array}

        final_results = []
        for i in range(len(leads)):
            result = evaluations.get(i, {})
            final_results.append({
                "score": int(result.get("score", 0)),
                "reason": str(result.get("reason", "Inconclusivo")),
                "tags": list(result.get("tags", ["Avaliacao Incompleta"])),
                "decision_maker": str(result.get("decision_maker", "Desconhecido")),
                "whatsapp_ready": bool(result.get("whatsapp_ready", False))
            })

        return final_results
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            return [{
                "score": 0,
                "reason": _friendly_rate_limit_msg(),
                "tags": ["Erro de API"],
                "decision_maker": "Desconhecido",
                "whatsapp_ready": False
            } for _ in leads]
        print("Erro de batch via Gemini API:", e)
        return [{
            "score": 0,
            "reason": f"Erro na super-avaliacao: {str(e)[:50]}",
            "tags": ["Erro de API"],
            "decision_maker": "Desconhecido",
            "whatsapp_ready": False
        } for _ in leads]


def generate_pitch(lead_data, api_key, pitch_type="whatsapp"):
    """Gera um pitch personalizado para abordar o lead."""
    if not api_key:
        return "Configure sua API Key primeiro."

    try:
        client = genai.Client(api_key=api_key)

        channel_instructions = {
            "whatsapp": "WhatsApp (mensagem curta, informal mas profissional, com emoji)",
            "email": "E-mail frio (assunto + corpo, formal mas empatico)",
            "instagram_dm": "DM do Instagram (muito curta, informal, com emoji)"
        }

        channel = channel_instructions.get(pitch_type, channel_instructions["whatsapp"])

        prompt = f"""Voce e um copywriter de vendas B2B especializado em abordagem fria.
Crie uma mensagem de primeiro contato para o canal: {channel}

=== DADOS DO PROSPECT ===
- Nome da empresa: {lead_data.get('name', 'N/A')}
- Descricao: {lead_data.get('description', 'N/A')}
- Decisor provavel: {lead_data.get('decision_maker', 'Proprietario')}
- Tags do perfil: {', '.join(lead_data.get('tags', []))}
- Score Velli: {lead_data.get('score', 'N/A')}/10

=== REGRAS ===
- NAO mencione que voce e IA
- NAO use cliches como "venho por meio desta"
- Seja direto, humano e mostre que pesquisou sobre o negocio
- Maximo 3 paragrafos curtos
- Finalize com uma pergunta que incentive resposta

Retorne APENAS o texto da mensagem, sem aspas, sem explicacao."""

        response = _call_gemini_with_retry(client, prompt)
        return response.text.strip()

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            return _friendly_rate_limit_msg()
        return f"Erro ao gerar pitch: {e}"


def generate_approach_strategy(lead_data, api_key):
    """Gera uma estrategia completa de abordagem para um lead."""
    if not api_key:
        return "Configure sua API Key primeiro."

    try:
        client = genai.Client(api_key=api_key)

        prompt = f"""Voce e um consultor senior de vendas B2B e outbound marketing.
Crie uma ESTRATEGIA COMPLETA de abordagem para este prospect.

=== DADOS DO PROSPECT ===
- Nome: {lead_data.get('name', 'N/A')}
- Descricao: {lead_data.get('description', 'N/A')}
- Decisor: {lead_data.get('decision_maker', 'Proprietario')}
- Tags: {', '.join(lead_data.get('tags', []))}
- Score: {lead_data.get('score', 'N/A')}/10
- WhatsApp disponivel: {'Sim' if lead_data.get('whatsapp_ready') else 'Nao'}

=== ENTREGUE ===
1. **Melhor Canal**: WhatsApp, Email, Instagram DM, LinkedIn ou Telefone
2. **Melhor Horario**: Dia da semana e horario ideal para contato
3. **Tom Recomendado**: Formal, Semi-formal ou Informal
4. **Estrategia em 3 Passos**: O que fazer no 1o contato, no follow-up, e no fechamento
5. **Mensagem Modelo**: Um exemplo pronto para usar no canal recomendado

Seja pratico e objetivo. Use emojis com moderacao."""

        response = _call_gemini_with_retry(client, prompt)
        return response.text.strip()

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            return _friendly_rate_limit_msg()
        return f"Erro ao gerar estrategia: {e}"


def copilot_chat(message, leads_context, api_key):
    """Assistente Copilot que entende os leads e ajuda o usuario."""
    if not api_key:
        return "Configure sua API Key nas Configuracoes para usar o Copilot."

    try:
        client = genai.Client(api_key=api_key)

        leads_summary = ""
        if leads_context:
            for i, lead in enumerate(leads_context[:20]):
                tags = ", ".join(lead.get("tags", [])) if isinstance(lead.get("tags"), list) else ""
                leads_summary += f"  {i+1}. {lead.get('name', 'N/A')} \u2014 Score: {lead.get('score', 0)}/10 \u2014 Tags: {tags}\n"
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

        response = _call_gemini_with_retry(client, prompt)
        return response.text.strip()

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            return _friendly_rate_limit_msg()
        return f"Erro no Copilot: {e}"