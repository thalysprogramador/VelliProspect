"""
Velli Prospect V3 — AI Evaluator (Gemini 2.5 Flash)
Avaliação inteligente de leads com Tags Semânticas e Score granular.
"""
from google import genai
import json


def evaluate_lead(lead, api_key, criteria):
    """
    Avalia um lead usando Gemini e retorna um dicionário rico:
    {
        "score": int (0-10),
        "reason": str,
        "tags": list[str],
        "decision_maker": str,
        "whatsapp_ready": bool
    }
    """
    if not api_key:
        return {
            "score": 0,
            "reason": "Chave de API não configurada.",
            "tags": [],
            "decision_maker": "Desconhecido",
            "whatsapp_ready": False
        }

    try:
        client = genai.Client(api_key=api_key)

        prompt = f"""Você é um analista sênior de prospecção B2B em Marketing Digital.
Analise esta empresa/perfil encontrado na internet e avalie o potencial de COMPRA de serviços de marketing.

=== INSTRUÇÃO PERSONALIZADA DO USUÁRIO ===
"{criteria}"

=== DADOS DO PROSPECT ===
- Nome: {lead.get('Nome', 'N/A')}
- Descrição / Bio / Snippet: {lead.get('Descrição (Bio/Web)', 'N/A')}
- Link: {lead.get('Link', 'N/A')}
- Tem telefone visível: {'Sim' if lead.get('_has_contact') else 'Não'}

=== SUA ANÁLISE DEVE CONTER ===

1. **score** (inteiro 0-10): Nota de potencial de compra. 
   - 0-3: Lead frio, sem potencial
   - 4-6: Lead morno, tem potencial mas com ressalvas
   - 7-8: Lead quente, bom prospect
   - 9-10: Lead incandescente, prospect ideal

2. **reason** (string, máximo 2 frases): Justificativa objetiva e curta.

3. **tags** (lista de strings): Classifique o prospect com 2 a 4 tags dentre estas opções (use SOMENTE estas):
   - "Ticket Alto" — Parece ser um negócio com ticket médio alto
   - "Ticket Baixo" — Micro-empreendedor ou operação simples
   - "Sem Site" — Não aparenta ter site profissional
   - "Boa Presença Digital" — Já tem presença online razoável
   - "Baixa Presença Digital" — Presença digital fraca ou inexistente
   - "Franquia / Rede" — Aparenta ser franquia ou rede grande
   - "Novo no Mercado" — Parece ser um negócio recente
   - "Decisor Acessível" — O decisor parece acessível para contato direto
   - "Alta Concorrência" — Nicho com muita competição local
   - "Oportunidade Urgente" — Demonstra necessidade urgente de marketing

4. **decision_maker** (string): Chute educado sobre quem é o decisor (ex: "Proprietário", "Gerente", "Sócio", "Diretor de Marketing", "Desconhecido")

5. **whatsapp_ready** (boolean): true se há indício de telefone/WhatsApp nos dados

=== FORMATO DE RESPOSTA ===
Retorne APENAS um JSON válido, sem markdown, sem explicação extra:
{{"score": 8, "reason": "...", "tags": ["...", "..."], "decision_maker": "...", "whatsapp_ready": true}}
"""

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )

        text = response.text.strip()

        # Limpar possíveis wrappers de markdown
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        result = json.loads(text.strip())

        # Garantir que todos os campos existem
        return {
            "score": int(result.get("score", 0)),
            "reason": str(result.get("reason", "Sem justificativa")),
            "tags": list(result.get("tags", [])),
            "decision_maker": str(result.get("decision_maker", "Desconhecido")),
            "whatsapp_ready": bool(result.get("whatsapp_ready", False))
        }

    except Exception as e:
        return {
            "score": 0,
            "reason": f"Erro na IA: {str(e)[:100]}",
            "tags": ["Erro"],
            "decision_maker": "Desconhecido",
            "whatsapp_ready": False
        }


def evaluate_leads_batch(leads, api_key, criteria):
    """
    Avalia uma lista inteira de leads de VÁRIAS fontes de uma só vez (Batching).
    Reduz massivamente as chamadas do GEMINI e acelera até 20x.
    """
    if not api_key:
        return [{
            "score": 0,
            "reason": "Chave de API não configurada.",
            "tags": [],
            "decision_maker": "Desconhecido",
            "whatsapp_ready": False
        } for _ in leads]

    try:
        client = genai.Client(api_key=api_key)
        
        leads_json_str = json.dumps([{
            "id": i,
            "Nome": l.get('Nome'),
            "Descrição": l.get('Descrição (Bio/Web)'),
            "Link": l.get('Link'),
            "_has_contact": l.get('_has_contact')
        } for i, l in enumerate(leads)])

        prompt = f"""Você é um super-computador de IA analisando potenciais clientes B2B. AVALIE ESTES LEADS EM LOTE.
=== CRITÉRIOS DE COMPRA ===
"{criteria}"

=== DADOS DOS PROSPECTS (JSON DE ENTRADA) ===
{leads_json_str}

=== INSTRUÇÕES ===
Retorne APENAS um Array JSON. Cada objeto deve seguir este modelo EXATO:
{{
  "id": <id original do lead da entrada>,
  "score": <nota 0-10 baseada no potencial>,
  "reason": "<justificativa muito curta e objetiva: 1 frase só>",
  "tags": ["<tag1>", "<tag2>"], 
  "decision_maker": "<provável decisor>",
  "whatsapp_ready": <true se _has_contact for true, senao false>
}}
Tags permitidas: "Ticket Alto", "Ticket Baixo", "Sem Site", "Boa Presença Digital", "Baixa Presença Digital", "Franquia / Rede", "Novo no Mercado", "Decisor Acessível", "Alta Concorrência", "Oportunidade Urgente".
IMPORTANTE: NÃO escreva mais NADA além do array JSON (iniciando com [ e fechando com ]).
"""

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )

        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        results_array = json.loads(text.strip())
        
        # Mapeando ordem
        evaluations = {r.get("id"): r for r in results_array}

        final_results = []
        for i in range(len(leads)):
            result = evaluations.get(i, {})
            final_results.append({
                "score": int(result.get("score", 0)),
                "reason": str(result.get("reason", "Inconclusivo")),
                "tags": list(result.get("tags", ["Avaliação Incompleta"])),
                "decision_maker": str(result.get("decision_maker", "Desconhecido")),
                "whatsapp_ready": bool(result.get("whatsapp_ready", False))
            })
            
        return final_results
    except Exception as e:
        print("Erro de batch via Gemini API:", e)
        return [{
            "score": 0,
            "reason": f"Erro na super-avaliação: {str(e)[:50]}",
            "tags": ["Erro de API"],
            "decision_maker": "Desconhecido",
            "whatsapp_ready": False
        } for _ in leads]


def generate_pitch(lead_data, api_key, pitch_type="whatsapp"):
    """
    Gera um pitch personalizado para abordar o lead.
    pitch_type: 'whatsapp', 'email', 'instagram_dm'
    """
    if not api_key:
        return "Configure sua API Key primeiro."

    try:
        client = genai.Client(api_key=api_key)

        channel_instructions = {
            "whatsapp": "WhatsApp (mensagem curta, informal mas profissional, com emoji)",
            "email": "E-mail frio (assunto + corpo, formal mas empático)",
            "instagram_dm": "DM do Instagram (muito curta, informal, com emoji)"
        }

        channel = channel_instructions.get(pitch_type, channel_instructions["whatsapp"])

        prompt = f"""Você é um copywriter de vendas B2B especializado em abordagem fria.
Crie uma mensagem de primeiro contato para o canal: {channel}

=== DADOS DO PROSPECT ===
- Nome da empresa: {lead_data.get('name', 'N/A')}
- Descrição: {lead_data.get('description', 'N/A')}
- Decisor provável: {lead_data.get('decision_maker', 'Proprietário')}
- Tags do perfil: {', '.join(lead_data.get('tags', []))}
- Score Velli: {lead_data.get('score', 'N/A')}/10

=== REGRAS ===
- NÃO mencione que você é IA
- NÃO use clichês como "venho por meio desta"
- Seja direto, humano e mostre que pesquisou sobre o negócio
- Máximo 3 parágrafos curtos
- Finalize com uma pergunta que incentive resposta

Retorne APENAS o texto da mensagem, sem aspas, sem explicação."""

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )

        return response.text.strip()

    except Exception as e:
        return f"Erro ao gerar pitch: {e}"


def copilot_chat(message, leads_context, api_key):
    """
    Assistente Copilot que entende os leads e ajuda o usuário.
    """
    if not api_key:
        return "Configure sua API Key nas Configurações para usar o Copilot."

    try:
        client = genai.Client(api_key=api_key)

        # Resumir os leads para contexto (máximo 20 para caber no prompt)
        leads_summary = ""
        if leads_context:
            for i, lead in enumerate(leads_context[:20]):
                tags = ", ".join(lead.get("tags", [])) if isinstance(lead.get("tags"), list) else ""
                leads_summary += f"  {i+1}. {lead.get('name', 'N/A')} — Score: {lead.get('score', 0)}/10 — Tags: {tags}\n"
        else:
            leads_summary = "  Nenhum lead carregado no momento.\n"

        prompt = f"""Você é o Velli Copilot, um assistente especialista em prospecção B2B e vendas de serviços de Marketing Digital.
Você está dentro do software Velli Prospect e tem acesso à base de leads do usuário.

=== BASE DE LEADS ATUAL ===
{leads_summary}

=== MENSAGEM DO USUÁRIO ===
"{message}"

=== SUAS CAPACIDADES ===
- Analisar a base de leads e sugerir estratégias de abordagem
- Criar pitches de vendas personalizados para qualquer lead
- Sugerir segmentações e filtros inteligentes
- Dar dicas de prospecção e outbound sales
- Responder dúvidas sobre estratégia de marketing

Responda de forma objetiva, prática e útil. Use emojis com moderação. Seja como um consultor de vendas sênior conversando com o usuário."""

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )

        return response.text.strip()

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            return "⚠️ **Calma lá, velocista!** 😅\n\nO plano gratuito do Google permite até 15 interações por minuto e você atingiu esse limite. \n\n**Aguarde cerca de 40 a 60 segundos** e me mande a mensagem novamente!"
        return f"Erro no Copilot: {e}"
