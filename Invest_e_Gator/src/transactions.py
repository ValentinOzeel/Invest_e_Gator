from typing import Literal, Union
from datetime import datetime

from Invest_e_Gator.src.secondary_modules.pydantic_valids import validate_transaction
from Invest_e_Gator.src.secondary_modules.currency_conversion import currency_conversion

class Transaction():    
    def __init__(self, 
                 date_hour: Union[str, datetime], 
                 transaction_type: Literal['buy', 'sale'],
                 ticker_symbol: str,
                 n_shares: float,
                 share_price: float,
                 share_currency: str,
                 transact_currency: str,
                 fee: float,
                 transaction_action: str
                 ):
        
        self.date_hour = date_hour 
        self.transaction_type = transaction_type.lower()
        self.ticker_symbol = ticker_symbol.lower()
        self.n_shares = n_shares 
        self.share_price = share_price 
        self.share_currency = share_currency.lower()
        self.fee = fee 
        self.transact_currency = transact_currency.lower()
        self.transaction_action = transaction_action
        
        validate_transaction(date_hour=self.date_hour, transaction_type=self.transaction_type,
                             ticker_symbol=self.ticker_symbol, n_shares=self.n_shares, share_price=self.share_price, share_currency=self.share_currency,
                             transact_currency=self.transact_currency, fee=self.fee,
                             transaction_action=self.transaction_action)
        
    @property
    def transaction_direction(self) -> Literal[1, -1]:
        return 1 if self.transaction_type == 'buy' else -1

    @property
    def quantity(self) -> float:
        return self.transaction_direction * self.n_shares

    @property 
    def share_price_transact_currency(self) -> float:
        return currency_conversion(
                amount=self.share_price, 
                date_obj=self.date_hour, 
                currency=self.share_currency, 
                target_currency=self.transact_currency
            )

    @property
    def transaction_amount_transact_currency(self) -> float:
        if self.share_currency == self.transact_currency:
            return self.quantity * self.share_price 
        else:
            # Check if exepense currency == base currency, otherwise make conversion            
            return currency_conversion(
                amount=self.quantity * self.share_price, 
                date_obj=self.date_hour, 
                currency=self.share_currency, 
                target_currency=self.transact_currency
            )