"""Streamlit dashboard for the clinic SaaS acquisition CRM."""

import hmac
import os
from datetime import datetime, time, timedelta, timezone

import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
ADMIN_API_TOKEN = os.getenv("ADMIN_API_TOKEN", "")
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "")
PIPELINE_LABELS = {
    "new": "Novo",
    "contacted": "Contatado",
    "responded": "Respondeu",
    "decision_maker_identified": "Decisor identificado",
    "demo_scheduled": "Demo agendada",
    "demo_completed": "Demo realizada",
    "pilot_proposed": "Convite p/ conta grátis",
    "pilot_active": "Usando o plano Free",
    "customer": "Cliente pago (Pro/Enterprise)",
    "lost": "Perdido",
}

st.set_page_config(
    page_title="Marketing Automation Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("Clinic Growth OS")

if not DASHBOARD_PASSWORD or not ADMIN_API_TOKEN:
    st.error("Defina DASHBOARD_PASSWORD e ADMIN_API_TOKEN nas variáveis de ambiente do dashboard.")
    st.stop()

if not st.session_state.get("authenticated"):
    with st.form("login"):
        password = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            if hmac.compare_digest(password.encode(), DASHBOARD_PASSWORD.encode()):
                st.session_state["authenticated"] = True
                st.rerun()
            st.error("Senha incorrecta.")
    st.stop()

st.caption("Painel interno para captar, acompanhar e converter clínicas em clientes do VitaClini.")

st.sidebar.header("Ligação à API")
tenant_id = st.sidebar.text_input("Tenant ID", value=os.getenv("TENANT_ID", "default"))
st.sidebar.caption(f"API: {API_BASE_URL}")


def api_request(method: str, path: str, **kwargs):
    headers = {"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {ADMIN_API_TOKEN}"}
    headers.update(kwargs.pop("headers", {}))
    try:
        response = httpx.request(method, f"{API_BASE_URL}{path}", headers=headers, timeout=10, **kwargs)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as exc:
        st.error(f"Não foi possível comunicar com a API: {exc}")
        return None


overview, vsl_tab, marketing_tab, ads_tab, activities_tab, campaigns_tab, leads_tab, pipeline_tab, followups_tab, add_lead_tab = st.tabs(
    [
        "Visão geral",
        "Funil VSL",
        "Agente de marketing",
        "Agente de anúncios",
        "Actividades",
        "Campanhas",
        "Clínicas",
        "Pipeline",
        "Follow-ups",
        "Adicionar clínica",
    ]
)

with overview:
    data = api_request("GET", "/crm/overview")
    if data:
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("Clínicas", data["total_leads"])
        col2.metric("Contactadas", data["contacted_leads"])
        col3.metric("Demos", data["demos_scheduled"])
        col4.metric("Pilotos", data["active_pilots"])
        col5.metric("Clientes", data["customers"])
        col6.metric("Follow-ups hoje", data["follow_ups_due"])

        st.subheader("Funil comercial")
        funnel_rows = [
            {"Etapa": PIPELINE_LABELS.get(stage, stage), "Clínicas": total}
            for stage, total in data["funnel"].items()
        ]
        st.bar_chart({row["Etapa"]: row["Clínicas"] for row in funnel_rows})
        st.dataframe(funnel_rows, use_container_width=True, hide_index=True)

with vsl_tab:
    st.subheader("Funil VSL")
    vsl_base_url = API_BASE_URL.rsplit("/api/", 1)[0]
    st.caption(
        f"Página pública: {vsl_base_url}/vsl?tenant={tenant_id} — acrescente as UTMs da campanha ao link do anúncio. "
        "O botão “Criar conta grátis” leva ao cadastro do VitaClini com as mesmas UTMs."
    )
    vsl_days = st.selectbox("Período", [7, 30, 90], index=1, format_func=lambda days: f"Últimos {days} dias")
    vsl = api_request("GET", f"/vsl/metrics?days={vsl_days}")
    if vsl:
        steps = {step["step"]: step for step in vsl["funnel"]}
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Visitantes", steps["page_view"]["visitors"])
        col2.metric("Deram play", steps["play"]["visitors"], f"{steps['play']['rate_from_view']}%", delta_color="off")
        col3.metric("Viram 50%", steps["progress_50"]["visitors"], f"{steps['progress_50']['rate_from_view']}%", delta_color="off")
        col4.metric("Viram a oferta", steps["cta_shown"]["visitors"], f"{steps['cta_shown']['rate_from_view']}%", delta_color="off")
        col5.metric("Foram ao cadastro", steps["cta_click"]["visitors"], f"{steps['cta_click']['rate_from_view']}%", delta_color="off")
        st.caption(f"Cliques em “Falar com especialista”: {vsl['specialist_clicks']}")

        vsl_labels = {
            "page_view": "Visitou a página",
            "play": "Deu play",
            "progress_25": "Assistiu 25%",
            "progress_50": "Assistiu 50%",
            "progress_75": "Assistiu 75%",
            "progress_100": "Assistiu 100%",
            "cta_shown": "Viu a oferta",
            "cta_click": "Foi para o cadastro",
        }
        funnel_rows = [
            {
                "Etapa": vsl_labels.get(step["step"], step["step"]),
                "Visitantes": step["visitors"],
                "% dos visitantes": step["rate_from_view"],
                "% da etapa anterior": step["rate_from_previous"],
            }
            for step in vsl["funnel"]
        ]
        st.dataframe(funnel_rows, use_container_width=True, hide_index=True)

        st.subheader("Por campanha")
        if vsl["by_campaign"]:
            st.dataframe(
                [
                    {
                        "Campanha (utm_campaign)": row["utm_campaign"],
                        "Visitantes": row["page_views"],
                        "Plays": row["plays"],
                        "Foram ao cadastro": row["cta_clicks"],
                        "Conversão %": row["cta_rate"],
                    }
                    for row in vsl["by_campaign"]
                ],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("Ainda não há visitas na VSL neste período.")

with marketing_tab:
    insights = api_request("GET", "/marketing/insights")
    if insights:
        summary = insights["summary"]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Follow-ups pendentes", summary["follow_ups_due"])
        col2.metric("Taxa até demo", f"{summary['demo_rate']}%")
        col3.metric("Taxa até piloto", f"{summary['pilot_rate']}%")
        col4.metric("Taxa até cliente", f"{summary['customer_rate']}%")

        st.subheader("Prioridades recomendadas para hoje")
        for recommendation in insights["recommendations"]:
            heading = f"{recommendation['priority'].upper()} — {recommendation['title']}"
            if recommendation["priority"] == "alta":
                st.error(heading)
            elif recommendation["priority"] == "média":
                st.warning(heading)
            else:
                st.info(heading)
            st.write(recommendation["reason"])
            st.caption(f"Acção: {recommendation['action']}")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Leads por origem")
            if insights["channel_breakdown"]:
                st.bar_chart(insights["channel_breakdown"])
            else:
                st.caption("Ainda não há origens de lead registadas.")
        with col2:
            st.subheader("Clínicas por especialidade")
            if insights["specialty_breakdown"]:
                st.bar_chart(insights["specialty_breakdown"])
            else:
                st.caption("Adiciona a especialidade das clínicas para comparar os nichos.")

        st.subheader("Mensagens comerciais prontas")
        selected_template = st.selectbox(
            "Escolhe o momento da conversa",
            options=list(insights["message_templates"]),
            format_func=lambda key: insights["message_templates"][key]["title"],
        )
        template = insights["message_templates"][selected_template]
        st.text_area("Template", value=template["message"], height=170)

with ads_tab:
    st.subheader("Crie anúncios para conseguir demos de consultórios")
    st.caption("O agente gera copy, direcção visual, vídeo curto, UTMs e uma variação para teste A/B. Não publica nem gasta dinheiro automaticamente.")
    with st.form("ad_generation"):
        col1, col2 = st.columns(2)
        campaign_name = col1.text_input("Nome da campanha *", placeholder="clinicas-whatsapp-outubro")
        channel = col2.selectbox(
            "Canal",
            options=["meta", "instagram", "facebook", "google_display"],
            format_func=lambda value: {
                "meta": "Meta Ads (Facebook + Instagram)",
                "instagram": "Instagram",
                "facebook": "Facebook",
                "google_display": "Google Display",
            }[value],
        )
        angle = col1.selectbox(
            "Ângulo principal",
            options=["after_hours", "reception_overload", "confirmation", "scheduling", "lead_conversion"],
            format_func=lambda value: {
                "after_hours": "Pacientes sem resposta fora do horário",
                "reception_overload": "Recepção sobrecarregada",
                "confirmation": "Confirmações e faltas",
                "scheduling": "Agendamento e remarcação",
                "lead_conversion": "Mensagens que viram consultas",
            }[value],
        )
        cta = col2.text_input("CTA", value="Ver demonstração")
        specialty = col1.text_input("Especialidade (opcional)", placeholder="Dermatologia")
        city = col2.text_input("Cidade (opcional)", placeholder="São Paulo")
        destination_url = st.text_input(
            "URL de destino para UTMs (opcional)",
            placeholder="https://seu-dominio.com/demo ou https://wa.me/5511999999999",
        )
        submit_ad = st.form_submit_button("Gerar campanha", type="primary")

    if submit_ad:
        if not campaign_name.strip():
            st.error("O nome da campanha é obrigatório.")
        else:
            campaign = api_request(
                "POST",
                "/ads/generate",
                json={
                    "campaign_name": campaign_name.strip(),
                    "channel": channel,
                    "angle": angle,
                    "specialty": specialty or None,
                    "city": city or None,
                    "destination_url": destination_url or None,
                    "cta": cta or "Ver demonstração",
                },
            )
            if campaign:
                st.success("Campanha gerada. Copia a variação A e B para criar o teste no gestor de anúncios.")
                st.markdown(f"**Público recomendado:** {campaign['audience']}")
                variant_a, variant_b = st.tabs(["Anúncio A", "Anúncio B — teste"])
                for tab, variant in ((variant_a, campaign["primary_variant"]), (variant_b, campaign["test_variant"])):
                    with tab:
                        st.markdown(f"### {variant['angle']}")
                        st.markdown(f"**Objectivo:** {variant['objective']}")
                        st.markdown(f"**Headline:** {variant['headline']}")
                        st.markdown("**Texto principal:**")
                        st.code(variant["primary_text"], language=None)
                        st.markdown(f"**Descrição:** {variant['description']}")
                        st.markdown(f"**CTA:** {variant['cta']}")
                        st.markdown("**Direcção de criativo:**")
                        st.write(variant["creative_direction"])
                        st.markdown("**Script de vídeo curto:**")
                        for scene in variant["video_script"]:
                            st.write(f"- {scene}")
                        st.markdown("**UTMs:**")
                        st.code("&".join(f"{key}={value}" for key, value in variant["utm_parameters"].items()), language=None)
                        if variant.get("tracking_url"):
                            st.markdown("**Link rastreável:**")
                            st.code(variant["tracking_url"], language=None)
                        else:
                            st.info("Adiciona uma URL de destino para o agente gerar o link rastreável completo.")

                st.markdown("### Plano de teste A/B")
                for item in campaign["ab_test_plan"]:
                    st.write(f"- {item}")
                st.markdown("### Limites de comunicação")
                for note in campaign["compliance_notes"]:
                    st.warning(note)

with activities_tab:
    st.subheader("Actividades comerciais")
    operations = api_request("GET", "/operations/overview")
    if operations:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Pendentes", operations["pending_activities"])
        col2.metric("Vencidas", operations["overdue_activities"])
        col3.metric("Campanhas activas", operations["active_campaigns"])
        col4.metric("Campanhas em rascunho", operations["draft_campaigns"])

    all_leads = api_request("GET", "/crm/leads") or []
    with st.form("new_activity", clear_on_submit=True):
        col1, col2 = st.columns(2)
        activity_title = col1.text_input("Actividade *", placeholder="Fazer follow-up com a clínica")
        activity_type = col2.selectbox(
            "Tipo",
            ["follow_up", "call", "demo", "proposal", "onboarding", "task"],
            format_func=lambda value: {
                "follow_up": "Follow-up",
                "call": "Chamada",
                "demo": "Demo",
                "proposal": "Proposta",
                "onboarding": "Onboarding",
                "task": "Tarefa",
            }[value],
        )
        activity_lead = st.selectbox(
            "Clínica associada (opcional)",
            options=[None, *all_leads],
            format_func=lambda lead: "Sem clínica" if lead is None else (lead.get("company_name") or lead.get("name") or "Sem nome"),
        )
        due_date = col1.date_input("Data", value=datetime.now().date())
        due_time = col2.time_input("Hora", value=time(9, 0))
        activity_notes = st.text_area("Notas")
        create_activity = st.form_submit_button("Criar actividade", type="primary")
        if create_activity:
            if not activity_title.strip():
                st.error("O título da actividade é obrigatório.")
            else:
                due_at = datetime.combine(due_date, due_time, tzinfo=timezone.utc)
                created = api_request(
                    "POST",
                    "/operations/activities",
                    json={
                        "lead_id": activity_lead["id"] if activity_lead else None,
                        "activity_type": activity_type,
                        "title": activity_title.strip(),
                        "notes": activity_notes or None,
                        "due_at": due_at.isoformat(),
                    },
                )
                if created:
                    st.success("Actividade criada.")

    activities = api_request("GET", "/operations/activities?status=pending")
    if activities is not None:
        st.markdown("### Actividades pendentes")
        lead_names = {lead["id"]: lead.get("company_name") or lead.get("name") or "Sem nome" for lead in all_leads}
        rows = [
            {
                "Actividade": item["title"],
                "Tipo": item["activity_type"],
                "Clínica": lead_names.get(item.get("lead_id"), "—"),
                "Prazo": item.get("due_at") or "—",
                "Notas": item.get("notes") or "—",
                "ID": item["id"],
            }
            for item in activities
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)
        if activities:
            selected_activity = st.selectbox(
                "Concluir actividade",
                options=activities,
                format_func=lambda item: item["title"],
            )
            if st.button("Marcar como concluída"):
                completed = api_request("POST", f"/operations/activities/{selected_activity['id']}/complete")
                if completed:
                    st.success("Actividade concluída. Actualize a página para ver a lista actualizada.")

with campaigns_tab:
    st.subheader("Campanhas de aquisição")
    st.caption("Regista campanhas criadas no Agente de Anúncios para acompanhar origem e qualidade dos leads.")
    with st.form("new_campaign", clear_on_submit=True):
        col1, col2 = st.columns(2)
        campaign_name = col1.text_input("Nome da campanha *", placeholder="clinicas-whatsapp-outubro")
        campaign_channel = col2.selectbox("Canal", ["meta", "instagram", "facebook", "google_display", "outbound", "referral"])
        campaign_objective = col1.text_input("Objectivo", value="Gerar demonstrações")
        campaign_status = col2.selectbox("Estado", ["draft", "active", "paused", "completed"])
        utm_source = col1.text_input("UTM source", value="meta")
        utm_medium = col2.text_input("UTM medium", value="paid_social")
        utm_campaign = col1.text_input("UTM campaign")
        daily_budget = col2.number_input("Orçamento diário", min_value=0.0, value=0.0, step=10.0)
        campaign_url = st.text_input("URL de destino")
        campaign_notes = st.text_area("Notas da campanha")
        create_campaign = st.form_submit_button("Guardar campanha", type="primary")
        if create_campaign:
            if not campaign_name.strip():
                st.error("O nome da campanha é obrigatório.")
            else:
                created = api_request(
                    "POST",
                    "/operations/campaigns",
                    json={
                        "name": campaign_name.strip(),
                        "channel": campaign_channel,
                        "objective": campaign_objective,
                        "status": campaign_status,
                        "utm_source": utm_source or None,
                        "utm_medium": utm_medium or None,
                        "utm_campaign": utm_campaign or None,
                        "destination_url": campaign_url or None,
                        "daily_budget": daily_budget or None,
                        "notes": campaign_notes or None,
                    },
                )
                if created:
                    st.success("Campanha guardada.")

    campaigns = api_request("GET", "/operations/campaigns")
    if campaigns is not None:
        st.markdown("### Campanhas registadas")
        st.dataframe(
            [
                {
                    "Campanha": campaign["name"],
                    "Canal": campaign["channel"],
                    "Estado": campaign["status"],
                    "Objectivo": campaign["objective"],
                    "UTM": campaign.get("utm_campaign") or "—",
                    "Orçamento/dia": campaign.get("daily_budget") or "—",
                }
                for campaign in campaigns
            ],
            use_container_width=True,
            hide_index=True,
        )

with leads_tab:
    selected_stage = st.selectbox(
        "Filtrar por etapa",
        options=["Todas", *PIPELINE_LABELS.keys()],
        format_func=lambda value: "Todas" if value == "Todas" else PIPELINE_LABELS[value],
    )
    path = "/crm/leads" if selected_stage == "Todas" else f"/crm/leads?stage={selected_stage}"
    leads = api_request("GET", path)
    if leads is not None:
        rows = [
            {
                "Clínica": lead.get("company_name") or lead.get("name") or "Sem nome",
                "Especialidade": lead.get("specialty") or "—",
                "Cidade": lead.get("city") or "—",
                "Decisor": lead.get("decision_maker_name") or "—",
                "Telefone": lead.get("phone") or "—",
                "Etapa": PIPELINE_LABELS.get(lead["status"], lead["status"]),
                "Follow-up": lead.get("next_follow_up_at") or "—",
                "ID": lead["id"],
            }
            for lead in leads
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)
        if leads:
            chosen_lead = st.selectbox(
                "Actualizar uma clínica",
                options=leads,
                format_func=lambda lead: f"{lead.get('company_name') or lead.get('name') or 'Sem nome'} — {PIPELINE_LABELS.get(lead['status'], lead['status'])}",
            )
            new_stage = st.selectbox(
                "Mover para",
                options=list(PIPELINE_LABELS),
                index=list(PIPELINE_LABELS).index(chosen_lead["status"]),
                format_func=lambda value: PIPELINE_LABELS[value],
            )
            notes = st.text_area("Notas", value=chosen_lead.get("notes") or "")
            saved_follow_up = (
                datetime.fromisoformat(chosen_lead["next_follow_up_at"])
                if chosen_lead.get("next_follow_up_at")
                else datetime.now() + timedelta(days=1)
            )
            follow_up_date = st.date_input(
                "Data do próximo follow-up",
                value=saved_follow_up.date(),
            )
            follow_up_time = st.time_input(
                "Hora do próximo follow-up",
                value=saved_follow_up.time().replace(tzinfo=None, microsecond=0),
            )
            if st.button("Guardar actualização", type="primary"):
                follow_up = datetime.combine(follow_up_date, follow_up_time, tzinfo=timezone.utc)
                api_request("POST", f"/crm/leads/{chosen_lead['id']}/stage", json={"status": new_stage})
                api_request(
                    "PATCH",
                    f"/crm/leads/{chosen_lead['id']}",
                    json={"notes": notes or None, "next_follow_up_at": follow_up.replace(tzinfo=timezone.utc).isoformat()},
                )
                st.success("Clínica actualizada. Actualize a página para ver os dados novos.")

with pipeline_tab:
    leads = api_request("GET", "/crm/leads")
    if leads is not None:
        columns = st.columns(5)
        stages = list(PIPELINE_LABELS)
        for index, stage in enumerate(stages):
            with columns[index % 5]:
                stage_leads = [lead for lead in leads if lead["status"] == stage]
                st.markdown(f"**{PIPELINE_LABELS[stage]} ({len(stage_leads)})**")
                for lead in stage_leads:
                    st.caption(lead.get("company_name") or lead.get("name") or "Sem nome")

with followups_tab:
    due_leads = api_request("GET", "/crm/leads?follow_up_due=true")
    if due_leads is not None:
        if due_leads:
            st.warning(f"Tens {len(due_leads)} follow-up(s) pendente(s).")
            st.dataframe(
                [
                    {
                        "Clínica": lead.get("company_name") or lead.get("name") or "Sem nome",
                        "Decisor": lead.get("decision_maker_name") or "—",
                        "Telefone": lead.get("phone") or "—",
                        "Etapa": PIPELINE_LABELS.get(lead["status"], lead["status"]),
                        "Data": lead.get("next_follow_up_at"),
                        "Notas": lead.get("notes") or "—",
                    }
                    for lead in due_leads
                ],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.success("Não há follow-ups pendentes.")

with add_lead_tab:
    with st.form("new_clinic_lead", clear_on_submit=True):
        col1, col2 = st.columns(2)
        company_name = col1.text_input("Nome da clínica *")
        specialty = col2.text_input("Especialidade")
        city = col1.text_input("Cidade")
        source_channel = col2.selectbox("Origem", ["outbound", "whatsapp", "instagram", "facebook", "google_ads", "referral", "organic"])
        decision_maker_name = col1.text_input("Nome do decisor")
        decision_maker_role = col2.text_input("Cargo do decisor")
        phone = col1.text_input("WhatsApp/telefone")
        email = col2.text_input("E-mail")
        instagram = col1.text_input("Instagram")
        website = col2.text_input("Website")
        notes = st.text_area("Notas iniciais")
        submit = st.form_submit_button("Adicionar clínica", type="primary")
        if submit:
            if not company_name.strip():
                st.error("O nome da clínica é obrigatório.")
            else:
                result = api_request(
                    "POST",
                    "/crm/leads",
                    json={
                        "company_name": company_name.strip(),
                        "specialty": specialty or None,
                        "city": city or None,
                        "source_channel": source_channel,
                        "decision_maker_name": decision_maker_name or None,
                        "decision_maker_role": decision_maker_role or None,
                        "phone": phone or None,
                        "email": email or None,
                        "instagram": instagram or None,
                        "website": website or None,
                        "notes": notes or None,
                    },
                )
                if result:
                    st.success(f"{result['company_name']} adicionada ao pipeline.")

st.divider()
st.caption("Clinic Growth OS | CRM interno para vender o SaaS de WhatsApp a consultórios.")
