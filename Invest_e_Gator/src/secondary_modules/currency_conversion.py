from forex_python.converter import CurrencyRates, RatesNotAvailableError
from currency_converter import CurrencyConverter

forex_python = CurrencyRates()
currency_convert = CurrencyConverter(fallback_on_missing_rate=True)

def currency_conversion(amount, currency, target_currency, date_obj, today:bool=False):
    if amount is None:
        return None 
    
    if currency.lower() == target_currency.lower():
        return amount
    
    try:
        # Get rate for the date or last rate available if today = True
        rate = forex_python.get_rate(currency, target_currency, date_obj) if not today else forex_python.get_rate(currency, target_currency)
        return amount * rate
    except Exception as e:

        try:
            # Get converted amount for the date or compute with last rate available if today = True
            # currency_converter need currency in uppercase
            return currency_convert.convert(amount, currency.upper(), target_currency.upper(), date_obj) if not today else currency_convert.convert(amount, currency.upper(), target_currency.upper())
        except Exception as ex:
            print(f"Error fetching currency conversion rate with forex_python nor currency_converter.\nforex_python error: {e}\ncurrency_converter error: {ex}\n")
