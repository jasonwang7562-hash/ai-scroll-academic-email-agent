from app.cost_model import CostInputs, model_call_cost, polling_cost_scenarios


def test_cost_uses_separate_input_and_output_prices():
    inputs = CostInputs(
        average_prompt_tokens=1000,
        average_completion_tokens=500,
        input_price_per_million_usd=2,
        output_price_per_million_usd=4,
    )
    assert model_call_cost(inputs) == 0.004


def test_event_filtered_polling_calls_model_only_for_new_email():
    inputs = CostInputs(
        average_prompt_tokens=1000,
        average_completion_tokens=0,
        input_price_per_million_usd=1,
        output_price_per_million_usd=0,
        new_emails_per_day=20,
        days_per_month=30,
    )
    result = polling_cost_scenarios(inputs)
    assert result["on_demand"]["model_calls_per_month"] == 600
    assert result["naive_hourly_llm_polling"]["model_calls_per_month"] == 720
    assert result["naive_15_minute_llm_polling"]["model_calls_per_month"] == 2880
    assert result["event_filtered_polling"]["model_calls_per_month"] == 600
