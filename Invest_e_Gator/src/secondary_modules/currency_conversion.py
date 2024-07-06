from forex_python.converter import CurrencyRates, RatesNotAvailableError
from currency_converter import CurrencyConverter

forex_python = CurrencyRates()
currency_converter = CurrencyConverter(fallback_on_missing_rate=True)

def currency_conversion(amount, currency, target_currency, date_obj):
    if currency == target_currency:
        return amount
    
    try:
        rate = forex_python.get_rate(currency, target_currency, date_obj)
        return amount * rate
    except Exception as e:
        print(f"Coudn't fetch currency conversion rate with forex_python, let's try with currency_converter...")  
        try:
            # currency_converter need currency in uppercase
            return currency_converter.convert(amount, currency.upper(), target_currency.upper(), date_obj)
        except Exception as ex:
            print(f"Error fetching currency conversion rate with currency_converter neither.\nforex_python error: {e}\ncurrency_converter error: {ex}\n")
