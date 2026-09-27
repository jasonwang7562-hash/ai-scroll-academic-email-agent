from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class CostInputs:
    average_prompt_tokens: float
    average_completion_tokens: float
    input_price_per_million_usd: float
    output_price_per_million_usd: float
    new_emails_per_day: int = 20
    days_per_month: int = 30


def model_call_cost(inputs: CostInputs) -> float:
    return (
        inputs.average_prompt_tokens * inputs.input_price_per_million_usd
        + inputs.average_completion_tokens * inputs.output_price_per_million_usd
    ) / 1_000_000


def polling_cost_scenarios(inputs: CostInputs) -> dict:
    """Compare model calls; inbox polling itself is treated as a non-LLM operation."""
    per_call = model_call_cost(inputs)
    email_calls = inputs.new_emails_per_day * inputs.days_per_month
    hourly_polls = 24 * inputs.days_per_month
    fifteen_minute_polls = 96 * inputs.days_per_month
    return {
        "inputs": asdict(inputs),
        "cost_per_processed_email_usd": round(per_call, 8),
        "on_demand": {
            "model_calls_per_month": email_calls,
            "estimated_monthly_cost_usd": round(email_calls * per_call, 6),
        },
        "naive_hourly_llm_polling": {
            "model_calls_per_month": hourly_polls,
            "estimated_monthly_cost_usd": round(hourly_polls * per_call, 6),
        },
        "naive_15_minute_llm_polling": {
            "model_calls_per_month": fifteen_minute_polls,
            "estimated_monthly_cost_usd": round(fifteen_minute_polls * per_call, 6),
        },
        "event_filtered_polling": {
            "inbox_checks_per_month_hourly": hourly_polls,
            "inbox_checks_per_month_15_minute": fifteen_minute_polls,
            "model_calls_per_month": email_calls,
            "estimated_monthly_model_cost_usd": round(email_calls * per_call, 6),
            "design_note": "Check the inbox without an LLM and invoke the model only for new messages.",
        },
    }
