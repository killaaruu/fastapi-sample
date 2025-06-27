async def get_exchange_rate(from_currency: str, to_currency: str = "USD") -> float:
    fake_rates = {"USD": 1.0, "EUR": 0.85, "RUB": 74.5, "GBP": 0.74, "JPY": 110.0}

    if from_currency == to_currency:
        return 1.0

    if from_currency not in fake_rates or to_currency not in fake_rates:
        return 1.0

    rate = fake_rates[from_currency] / fake_rates[to_currency]
    return rate
