"""Deterministic marketing and funnel agent for selling VitaClini to clinics."""

from collections import Counter
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead
from app.modules.crm.routes import PIPELINE_STAGES


MESSAGE_TEMPLATES = {
    "first_contact": {
        "title": "Primeiro contato",
        "message": (
            "Olá, [nome]! Vi que a [clínica] marca consultas pelo WhatsApp. "
            "Eu criei o VitaClini, que responde os pacientes na hora, mostra os horários livres, "
            "agenda a consulta e manda lembrete um dia antes, inclusive à noite e no fim de semana. "
            "Posso te mandar um vídeo curto mostrando funcionando?"
        ),
    },
    "follow_up": {
        "title": "Follow-up após primeiro contato",
        "message": (
            "Oi, [nome], tudo bem? Só retomando: o VitaClini cuida dos agendamentos pelo WhatsApp, "
            "e a recepção fica livre para quem está na clínica. Dá para começar no plano grátis, "
            "sem cartão. Quer que eu te mostre em 15 minutos?"
        ),
    },
    "demo": {
        "title": "Confirmação de demonstração",
        "message": (
            "Oi, [nome]! Confirmando nossa conversa de [data/hora]. Vou mostrar o paciente marcando "
            "uma consulta pelo WhatsApp, do primeiro \"oi\" até a confirmação, e o lembrete automático. "
            "Leva uns 15 minutos."
        ),
    },
    "pilot": {
        "title": "Convite para criar a conta grátis",
        "message": (
            "Oi, [nome]! Como combinamos, é só criar a conta grátis em [link]: o plano Free tem 1 médico "
            "e até 50 agendamentos por mês, sem cartão. Se quiser, eu te ajudo a cadastrar os médicos "
            "e os horários agora mesmo."
        ),
    },
    "conversion": {
        "title": "Upgrade para o plano Pro",
        "message": (
            "Oi, [nome]! Vi que a [clínica] já está agendando pelo VitaClini. No plano Pro (R$ 97/mês) "
            "você coloca até 10 médicos, tem agendamentos ilimitados e os lembretes automáticos para "
            "reduzir faltas. Quer que eu te mande o link para ativar?"
        ),
    },
}


class MarketingFunnelAgent:
    """Turns CRM data into actionable daily sales and marketing priorities."""

    async def get_insights(self, db: AsyncSession, tenant_id: str) -> dict:
        now = datetime.now(timezone.utc)
        result = await db.execute(select(Lead).where(Lead.tenant_id == tenant_id))
        leads = list(result.scalars().all())
        funnel = Counter(lead.status for lead in leads)
        for stage in PIPELINE_STAGES:
            funnel.setdefault(stage, 0)

        active_leads = [lead for lead in leads if lead.status not in {"customer", "lost"}]
        follow_ups_due = [
            lead
            for lead in active_leads
            if lead.next_follow_up_at and lead.next_follow_up_at <= now
        ]
        leads_without_follow_up = [
            lead
            for lead in active_leads
            if lead.status in {"contacted", "responded", "decision_maker_identified", "demo_completed", "pilot_proposed"}
            and not lead.next_follow_up_at
        ]

        recommendations = self._build_recommendations(
            funnel=funnel,
            follow_ups_due=len(follow_ups_due),
            leads_without_follow_up=len(leads_without_follow_up),
        )

        channel_result = await db.execute(
            select(Lead.source_channel, func.count(Lead.id))
            .where(Lead.tenant_id == tenant_id)
            .group_by(Lead.source_channel)
            .order_by(func.count(Lead.id).desc())
        )
        channel_breakdown = {
            channel or "não definido": count for channel, count in channel_result.all()
        }

        specialty_result = await db.execute(
            select(Lead.specialty, func.count(Lead.id))
            .where(Lead.tenant_id == tenant_id, Lead.specialty.is_not(None))
            .group_by(Lead.specialty)
            .order_by(func.count(Lead.id).desc())
        )
        specialty_breakdown = {
            specialty: count for specialty, count in specialty_result.all()
        }

        total = len(leads)
        demos = funnel["demo_scheduled"] + funnel["demo_completed"] + funnel["pilot_proposed"] + funnel["pilot_active"] + funnel["customer"]
        pilots = funnel["pilot_active"] + funnel["customer"]
        return {
            "summary": {
                "total_leads": total,
                "follow_ups_due": len(follow_ups_due),
                "leads_without_follow_up": len(leads_without_follow_up),
                "demo_rate": round((demos / total) * 100, 1) if total else 0.0,
                "pilot_rate": round((pilots / total) * 100, 1) if total else 0.0,
                "customer_rate": round((funnel["customer"] / total) * 100, 1) if total else 0.0,
            },
            "funnel": dict(funnel),
            "channel_breakdown": channel_breakdown,
            "specialty_breakdown": specialty_breakdown,
            "recommendations": recommendations,
            "message_templates": MESSAGE_TEMPLATES,
        }

    @staticmethod
    def _build_recommendations(
        *, funnel: Counter, follow_ups_due: int, leads_without_follow_up: int
    ) -> list[dict[str, str]]:
        recommendations: list[dict[str, str]] = []

        if follow_ups_due:
            recommendations.append({
                "priority": "alta",
                "title": f"Faça {follow_ups_due} follow-up(s) hoje",
                "reason": "Existem clínicas interessadas sem uma próxima ação concluída.",
                "action": "Abra a aba Follow-ups, fale com essas clínicas e marque a próxima data antes de encerrar a conversa.",
            })

        if leads_without_follow_up:
            recommendations.append({
                "priority": "alta",
                "title": f"Marque a próxima ação para {leads_without_follow_up} clínica(s)",
                "reason": "Leads sem follow-up se perdem porque não existe uma tarefa definida.",
                "action": "Defina a data do próximo contato para cada clínica em andamento no funil.",
            })

        if funnel["new"] >= 10 and funnel["contacted"] == 0:
            recommendations.append({
                "priority": "alta",
                "title": "Transforme a lista de clínicas em contatos reais",
                "reason": "Você tem clínicas novas, mas ainda não há prospecção registrada.",
                "action": "Fale com 20 clínicas hoje usando o template de primeiro contato e mova cada uma para Contatado.",
            })

        if funnel["responded"] + funnel["decision_maker_identified"] >= 3 and funnel["demo_scheduled"] == 0:
            recommendations.append({
                "priority": "alta",
                "title": "Converta respostas em demonstrações",
                "reason": "Há interesse, mas nenhuma demo agendada no funil.",
                "action": "Use uma chamada única: 'Posso te mostrar em 15 minutos o VitaClini agendando pelo WhatsApp da clínica?'.",
            })

        if funnel["demo_completed"] >= 1 and funnel["pilot_proposed"] + funnel["pilot_active"] + funnel["customer"] == 0:
            recommendations.append({
                "priority": "média",
                "title": "Feche a próxima ação depois da demo",
                "reason": "Uma demo sem convite para criar a conta perde força rapidamente.",
                "action": "No mesmo dia da demo, envie o convite para a conta grátis e ofereça ajuda para cadastrar médicos e horários.",
            })

        if funnel["pilot_active"] >= 1 and funnel["customer"] == 0:
            recommendations.append({
                "priority": "média",
                "title": "Prepare o upgrade de quem está no plano grátis",
                "reason": "Quem usa o plano Free já viu valor; o próximo passo é o Pro.",
                "action": "Mostre quantas consultas o VitaClini já marcou e ofereça o Pro (R$ 97/mês) com lembretes automáticos e mais médicos.",
            })

        if not recommendations:
            recommendations.append({
                "priority": "normal",
                "title": "Monte a primeira lista de clínicas",
                "reason": "Ainda não há volume suficiente no CRM para identificar um gargalo específico.",
                "action": "Cadastre 30 clínicas com especialidade, cidade, WhatsApp/Instagram e origem do contato. Depois comece a prospecção.",
            })
        return recommendations


marketing_funnel_agent = MarketingFunnelAgent()