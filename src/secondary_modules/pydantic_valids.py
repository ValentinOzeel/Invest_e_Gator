from typing import Any
from datetime import datetime
import re
from pydantic import BaseModel, field_validator, ValidationInfo, ValidationError

from constants import yfinance_history_interval_period_choices
   
   
############# data_history #############
          
class DataHistoryPydantic(BaseModel):
    interval: str
    period: str 
    start: Any
    end: Any
    include_divs_splits: bool
    repair: bool
    keepna: bool

    @field_validator('interval')
    @classmethod
    def validate_interval(cls, value, info: ValidationInfo):
        if not isinstance(value, str):
            raise ValueError(f"Input {info.field_name} -- {value} -- is not an instance of {str}. It should be assigned to one of the following: {yfinance_history_interval_period_choices['interval']}.")
        
        if value not in yfinance_history_interval_period_choices["interval"]:
            raise ValueError(f"Input {info.field_name} -- {value} -- is not a valid interval. It should be assigned to one of the following: {yfinance_history_interval_period_choices['interval']}.")
        
        return value
    
    @field_validator('period')
    @classmethod
    def validate_period(cls, value, info: ValidationInfo):
        if not isinstance(value, str):
            raise ValueError(f"Input {info.field_name} -- {value} -- is not an instance of {str}. It should be assigned to one of the following: {yfinance_history_interval_period_choices['period']}.")
        
        if value not in yfinance_history_interval_period_choices["period"]:
            raise ValueError(f"Input {info.field_name} -- {value} -- is not a valid period. It should be assigned to one of the following: {yfinance_history_interval_period_choices['period']}.")
        
        return value
    
    @field_validator('start', 'end')
    @classmethod
    def validate_start_end(cls, value, info: ValidationInfo):
        # Return value if is None
        if value is None:
            return value
        # Check if value is either str or datetime
        if not any([isinstance(value, str), isinstance(value, datetime)]):
            raise ValueError(f"Input {info.field_name} -- {value} -- is not an instance of {str} nor {datetime}.")
        # If value is str, check if valid str
        if isinstance(value, str):
            # Define the regular expression pattern for YYYY-MM-DD
            pattern = r'^\d{4}-\d{2}-\d{2}$'
            # Check if the date_str matches the pattern
            if not re.match(pattern, value):
                raise ValueError(f"Input {info.field_name} -- {value} -- should follow the 'YYYY-MM-DD' format or be a datetime object.")
            # Try to parse the date_str to a datetime object to check if it is a valid date
            try:
                datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                raise ValueError(f"Input {info.field_name} -- {value} -- is not a valid date.")
        return value
    
    @field_validator('include_divs_splits', 'repair', 'keepna')
    @classmethod
    def validate_divs_repair_keepna(cls, value, info: ValidationInfo):
        # Return value if is None
        if value is None:
            return value
        # Check if value is bool
        if not isinstance(value, bool):
            raise ValueError(f"Input {info.field_name} -- {value} -- is not an instance of {bool}.")
        return value
  
  
def validate_data_history(**kwargs):  
    # Validate data_history parameters input through pydantic model
    try:
        DataHistoryPydantic(**kwargs)
    except ValidationError as e:
        raise ValueError(f'Invalid data_history parameters:\n{e}')





############# financials #############

class FinancialsPydantic(BaseModel):
    income_stmt: bool
    balance_sheet: bool 
    cash_flow: bool
    quarterly: bool
    pretty: bool

    @field_validator('income_stmt', 'balance_sheet', 'cash_flow', 'quarterly', 'pretty')
    @classmethod
    def validate_interval(cls, value, info: ValidationInfo):
        if not isinstance(value, bool):
            raise ValueError(f"Input {info.field_name} -- {value} -- is not an instance of {bool}.")
        return value
    
def validate_financials(**kwargs):  
    # Validate data_history parameters input through pydantic model
    try:
        FinancialsPydantic(**kwargs)
    except ValidationError as e:
        raise ValueError(f'Invalid data_history parameters:\n{e}')