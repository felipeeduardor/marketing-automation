"""VitaClini plans, as sold on vitaclini.com.br.

Keep in sync with the product: backend/app/planos.py and frontend/src/pages/Planos.jsx
in the VitaClini repository (github.com/felipeeduardor/-demo-clinica).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Plan:
    id: str
    name: str
    price_monthly: int  # BRL cents
    features: tuple[str, ...]


PLANS: dict[str, Plan] = {
    "free": Plan(
        id="free",
        name="Free",
        price_monthly=0,
        features=("1 médico", "50 agendamentos/mês", "Chatbot WhatsApp", "Painel básico"),
    ),
    "pro": Plan(
        id="pro",
        name="Pro",
        price_monthly=9700,
        features=(
            "Até 10 médicos",
            "Agendamentos ilimitados",
            "Chatbot + base de conhecimento da clínica",
            "Lembretes automáticos",
            "Painel completo",
            "Suporte por e-mail",
        ),
    ),
    "enterprise": Plan(
        id="enterprise",
        name="Enterprise",
        price_monthly=24700,
        features=(
            "Médicos ilimitados",
            "Agendamentos ilimitados",
            "Multi-unidade",
            "Lembretes automáticos",
            "Relatórios avançados",
            "Suporte prioritário",
        ),
    ),
}


def get_plan(plan_id: str) -> Plan:
    plan = PLANS.get(plan_id)
    if not plan:
        raise ValueError(f"Plano inválido: {plan_id}")
    return plan


def format_brl(cents: int) -> str:
    return f"R$ {cents / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def plan_to_dict(plan: Plan) -> dict:
    return {
        "id": plan.id,
        "name": plan.name,
        "price_monthly": plan.price_monthly,
        "price_display": format_brl(plan.price_monthly).removesuffix(",00"),
        "features": list(plan.features),
    }
