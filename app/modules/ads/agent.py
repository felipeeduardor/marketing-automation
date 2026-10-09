"""Deterministic ad agent for selling VitaClini (WhatsApp scheduling for clinics)."""

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from app.schemas.ads import AdGenerationRequest, AdGenerationResponse, AdVariant


ANGLES = {
    "after_hours": {
        "label": "Pacientes sem resposta fora do horário",
        "headline": "Sua clínica responde pacientes depois do horário?",
        "text": (
            "Quando a recepção fecha, os pedidos de horário ficam sem resposta e o paciente marca em outro lugar. "
            "O VitaClini responde na hora pelo WhatsApp, mostra os horários livres e confirma a consulta."
        ),
        "creative": (
            "Formato 4:5 ou story. Conversa de WhatsApp fictícia às 21:47 com \"Oi, tem horário amanhã?\", "
            "seguida da consulta confirmada. Visual simples, com cara de story; não usar dados reais de pacientes."
        ),
        "video": [
            "Cena 1: 'Sua clínica responde pacientes depois do horário?'",
            "Cena 2: pedido de horário chegando à noite numa conversa fictícia.",
            "Cena 3: o VitaClini mostra os horários e confirma a consulta.",
            "Cena 4: CTA 'Crie sua conta grátis'.",
        ],
    },
    "reception_overload": {
        "label": "Recepção sobrecarregada",
        "headline": "Sua recepção ainda marca consulta uma por uma no WhatsApp?",
        "text": (
            "Tem horário? Qual médico atende? Pode ser sábado? O VitaClini responde essas perguntas e agenda "
            "pelo WhatsApp, e a recepção fica livre para quem está na clínica."
        ),
        "creative": (
            "Formato 4:5. À esquerda, várias mensagens fictícias repetidas; à direita, a agenda organizada no painel. "
            "Evitar fotos de profissionais exaustos ou pacientes identificáveis."
        ),
        "video": [
            "Cena 1: 'Sua recepção ainda marca consulta uma por uma no WhatsApp?'",
            "Cena 2: mensagens fictícias de horário, médico e dia da semana.",
            "Cena 3: o VitaClini responde e a consulta aparece no painel.",
            "Cena 4: CTA 'Crie sua conta grátis'.",
        ],
    },
    "confirmation": {
        "label": "Lembretes e faltas",
        "headline": "Seus pacientes esquecem a consulta?",
        "text": (
            "O VitaClini manda um lembrete automático pelo WhatsApp um dia antes de cada consulta. "
            "Sem ninguém da recepção precisar lembrar de lembrar."
        ),
        "creative": (
            "Formato 4:5. Mensagem de lembrete fictícia: 'Sua consulta é amanhã às 14h', ao lado da agenda do dia. "
            "Não prometer redução percentual de faltas sem dados reais."
        ),
        "video": [
            "Cena 1: 'Seus pacientes esquecem a consulta?'",
            "Cena 2: lembrete automático chegando no WhatsApp do paciente (fictício).",
            "Cena 3: agenda do dia no painel do VitaClini.",
            "Cena 4: CTA 'Crie sua conta grátis'.",
        ],
    },
    "scheduling": {
        "label": "Agendamento automático",
        "headline": "Transforme mensagens de WhatsApp em consultas marcadas.",
        "text": (
            "O paciente escolhe a especialidade, o médico e o horário livre, e a consulta fica confirmada. "
            "Comece grátis: 1 médico e até 50 agendamentos por mês, sem cartão."
        ),
        "creative": (
            "Formato 4:5. Sequência: mensagem do paciente → médicos → horários → consulta confirmada. "
            "Usar conversa fictícia ou ambiente de demonstração."
        ),
        "video": [
            "Cena 1: 'Transforme mensagens de WhatsApp em consultas marcadas.'",
            "Cena 2: paciente fictício pede um horário.",
            "Cena 3: o VitaClini oferece médicos e horários e confirma.",
            "Cena 4: CTA 'Crie sua conta grátis'.",
        ],
    },
    "lead_conversion": {
        "label": "Quem responde primeiro, agenda",
        "headline": "Quem responde primeiro no WhatsApp, agenda.",
        "text": (
            "O paciente que não recebe resposta marca na próxima clínica do Google. "
            "Com o VitaClini, a sua clínica responde e agenda na hora, 24 horas por dia."
        ),
        "creative": (
            "Formato 4:5. Duas conversas lado a lado: uma sem resposta, outra com a consulta confirmada pelo VitaClini. "
            "Destacar o processo, não resultados financeiros não comprovados."
        ),
        "video": [
            "Cena 1: 'Quem responde primeiro no WhatsApp, agenda.'",
            "Cena 2: mensagem fictícia sem resposta vs. respondida na hora.",
            "Cena 3: consulta confirmada e aparecendo no painel.",
            "Cena 4: CTA 'Crie sua conta grátis'.",
        ],
    },
}


class AdAgent:
    """Creates compliant, trackable clinic-SaaS ad concepts without publishing them."""

    @staticmethod
    def _build_tracking_url(destination_url: str | None, utm: dict[str, str]) -> str | None:
        if not destination_url:
            return None
        parsed = urlparse(destination_url)
        if not parsed.scheme or not parsed.netloc:
            return None
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query.update(utm)
        return urlunparse(parsed._replace(query=urlencode(query)))

    @staticmethod
    def _audience(request: AdGenerationRequest) -> str:
        location = f" em {request.city}" if request.city else ""
        specialty = f" de {request.specialty}" if request.specialty else " e consultórios"
        return (
            f"Donos e gestores de clínicas{specialty}{location} que marcam consultas pelo WhatsApp: "
            "médicos proprietários, gestores e responsáveis pela recepção."
        )

    def _variant(self, request: AdGenerationRequest, angle_key: str, variant_id: str) -> AdVariant:
        angle = ANGLES[angle_key]
        utm = {
            "utm_source": "meta" if request.channel in {"meta", "facebook", "instagram"} else request.channel,
            "utm_medium": "paid_social" if request.channel in {"meta", "facebook", "instagram"} else "display",
            "utm_campaign": request.campaign_name.strip().lower().replace(" ", "-"),
            "utm_content": variant_id.lower(),
        }
        description = "VitaClini: agendamento automático pelo WhatsApp. Comece grátis."
        return AdVariant(
            id=variant_id,
            angle=angle["label"],
            objective="Levar à página de vendas (VSL) e à criação da conta grátis",
            headline=angle["headline"],
            primary_text=angle["text"],
            description=description,
            cta=request.cta,
            creative_direction=angle["creative"],
            video_script=angle["video"],
            utm_parameters=utm,
            tracking_url=self._build_tracking_url(request.destination_url, utm),
        )

    def generate(self, request: AdGenerationRequest) -> AdGenerationResponse:
        angle_keys = list(ANGLES)
        current_index = angle_keys.index(request.angle)
        alternate_angle = angle_keys[(current_index + 1) % len(angle_keys)]
        primary = self._variant(request, request.angle, "AD-A")
        test = self._variant(request, alternate_angle, "AD-B")
        return AdGenerationResponse(
            campaign_name=request.campaign_name,
            channel=request.channel,
            audience=self._audience(request),
            primary_variant=primary,
            test_variant=test,
            ab_test_plan=[
                "Crie dois conjuntos idênticos de público, posicionamento e orçamento; altere apenas o ângulo do anúncio.",
                "Use a mesma página de vendas (/vsl) com UTMs diferentes em cada anúncio para comparar no Funil VSL.",
                "Compare quantas pessoas chegam a assistir o vídeo e a criar a conta grátis; não otimize só por clique barato.",
                "Não declare redução de faltas, aumento de receita ou resultados clínicos sem dados reais e verificáveis.",
            ],
            compliance_notes=[
                "O anúncio vende agendamento e atendimento administrativo; não deve prometer diagnóstico, orientação médica ou prescrição.",
                "Não use conversas, nomes, fotos ou dados de pacientes reais nos criativos sem autorização apropriada.",
                "Use o número/conta WhatsApp da empresa e respeite as políticas de consentimento para mensagens posteriores.",
            ],
        )


ad_agent = AdAgent()