from typing import Literal, Union
from datetime import datetime
from forex_python.converter import CurrencyRates
from Invest_e_Gator.src.secondary_modules.pydantic_valids import validate_transaction

class Transaction():    
    def __init__(self, 
                 date_hour: Union[str, datetime], 
                 transaction_type: Literal['buy', 'sale'],
                 ticker: str,
                 n_shares: float,
                 share_price: float,
                 share_currency: str,
                 expense_currency: str,
                 fee: float
                 ):
        
        validate_transaction(date_hour=date_hour, transaction_type=transaction_type,
                             ticker=ticker, n_shares=n_shares, share_price=share_price, share_currency=share_currency,
                             expense_currency=expense_currency, fee=fee)
        
        self.date_hour = date_hour 
        self.transaction_type = transaction_type.lower()
        self.ticker = ticker.lower()
        self.n_shares = n_shares 
        self.share_price = share_price 
        self.share_currency = share_currency.lower()
        self.fee = fee 
        self.expense_currency = expense_currency
        
    @property
    def transaction_direction(self) -> Literal[1, -1]:
        return 1 if self.transaction_type == 'buy' else -1

    @property
    def quantity(self) -> float:
        return self.transaction_direction * self.n_shares
    
    @property
    def transaction_cost_share_currency(self) -> float:
        return self.quantity * self.share_price

    @property
    def transaction_cost_expense_currency(self) -> float:
        if self.share_currency == self.expense_currency:
            return self.quantity * self.share_price 
        else:
            cr = CurrencyRates()
            return self.quantity * self.share_price * cr.get_rate(self.share_currency, self.expense_currency, self.date_hour)
