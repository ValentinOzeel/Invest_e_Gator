from typing import Literal, Union
from datetime import datetime

from secondary_modules.pydantic_valids import validate_transaction

class Transaction():    
    def __init__(self, 
                 date_hour: Union[str, datetime], 
                 transaction_type: Literal['buy', 'sale'],
                 currency: Literal['usd', 'eur', 'jpy', 'gbp', 'cnh', 'aud', 'cad', 'chf'],
                 ticker: str,
                 n_shares: float,
                 share_price: float,
                 fee: float
                 ):
        
        validate_transaction(date_hour=date_hour, 
                             transaction_type=transaction_type, currency=currency, 
                             ticker=ticker, n_shares=n_shares, share_price=share_price, fee=fee)
        
        self.date_hour = date_hour 
        self.hour 
        self.transaction_type = transaction_type.lower()
        self.currency = currency.lower()
        self.ticker = ticker.lower()
        self.n_shares = n_shares 
        self.share_price = share_price 
        self.fee = fee 
        
    @property
    def transaction_direction(self) -> Literal[1, -1]:
        return 1 if self.transaction_type == 'buy' else -1

    @property
    def quantity(self) -> float:
        return self.transaction_direction * self.n_shares
    
    @property
    def transaction_cost(self) -> float:
        return self.quantity * self.share_price

