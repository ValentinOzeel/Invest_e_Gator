available_currencies = ['usd', 'eur', 'jpy', 'gbp', 'aud', 'cad', 'chf', 'cny', 'hkd', 'nzd', 'sgd', 
                        'krw', 'inr', 'rub', 'brl', 'mxn', 'zar', 'try', 'pln', 'dkk', 'sek', 'nok', 
                        'czk', 'ils', 'myr', 'thb', 'idr', 'huf', 'ron', 'bgn', 'hrk', 'ltl', 'php']

# Define a list of attribute names and their corresponding keys in the info dictionary
yfinance_info_attributes = {
    ## business presentation
    'name': 'longName',
    'uuid': 'uuid',
    'type': 'quoteType',
    'exchange': 'exchange',
    'business_summary': 'longBusinessSummary',
    'country': 'country',
    'industry': 'industryKey',
    'sector': 'sectorKey',
    'employees': 'fullTimeEmployees',
    'managment': 'companyOfficers',
    'currency': 'currency',
    
    ## risks
    'audit_risk': 'auditRisk',
    'board_risk': 'boardRisk',
    'compensation_risk': 'compensationRisk',
    'shareholder_rights_risk': 'shareHolderRightsRisk',
    'overall_risk': 'overallRisk',
    
    ### price movments, volatility and volume
    'current_price': 'currentPrice',
    'last_close': 'previousClose',
    'open': 'open',
    'day_low': 'dayLow',
    'day_high': 'dayHigh',
    
    '52w_low': 'fiftyTwoWeekLow',
    '52w_high': 'fiftyTwoWeekHigh',
    '52w_change': '52WeekChange',
    '52w_change_S&P500': 'SandP52WeekChange',
    'fifty_d_average': 'fiftyDayAverage',
    '200d_average': 'twoHundredDayAverage',
    
    'beta': 'beta', #measure of a stock's volatility in relation to the overall market
    'volume': 'volume',
    'average_volume': 'averageVolume',
    'average_volume_10d': 'averageVolume10days',
    
    ## Analists target
    'n_analysts': 'numberOfAnalystOpinions',
    'analysts_high': 'targetHighPrice',
    'analysts_low': 'targetLowPrice',
    'analyst_mean': 'targetMeanPrice',
    'analyst_median': 'targetMedianPrice',
    'analyst_recommendation_mean': 'recommendationMean',
    'analyst_recommendation': 'recommendationKey',
    
    ## dividends
    'dividend_rate': 'dividendRate',
    'dividend_yield': 'dividendYield',
    'dividend_yield_5y_average': 'fiveYearAvgDividendYield',
    'payout_ratio': 'payoutRatio',
    'trailing_annual_dividend_rate': 'trailingAnnualDividendRate',
    'trailing_annual_dividend_yield': 'trailingAnnualDividendYield',
    'last_dividend': 'lastDividendValue',
    
    ## shares
    'shares_float': 'floatShares',
    'shares_outstanding': 'sharesOutstanding',
    'shares_shorted': 'sharesShort',
    'shares_shorted_prior_month': 'sharesShortPriorMonth',
    'percent_share_outstanding_shorted': 'sharesPercentSharesOut',
    'percent_shares_float_shorted': 'shortPercentOfFloat',
    'short_interest': 'shortRatio', # the number of shares held short in a stock and it divides this by the stock's average daily trading volume
    'last_split_factor': 'lastSplitFactor',
    'last_split_date': 'lastSplitDate',
    
    ## holder
    'insider_holdings_percent': 'heldPercentInsiders',
    'institutional_holdings_percent': 'heldPercentInstitutions',
    
    ## valuation and ratios
    'market_cap': 'marketCap',
    'enterprise_value': 'enterpriseValue',
    'book_value': 'bookValue',
    'pb': 'priceToBook',
    'trailing_pe': 'trailingPE',
    'forward_pe': 'forwardPE',
    'trailing_ps': 'priceToSalesTrailing12Months',
    'EV/Revenue': 'enterpriseToRevenue',
    'EV/EBITDA': 'enterpriseToEbitda',
    'peg': 'pegRatio',
    'trailing_peg': 'trailingPegRatio',
    'quick_ratio': 'quickRatio', # Current assets / current liabilities
    'current_ratio': 'currentRatio', # ability to cover its short-term obligations with its current assets
    'debt_to_equity': 'debtToEquity',

    ## margins
    'profit_margins': 'profitMargins',
    'gross_margins': 'grossMargins',
    'EBITDA_margins': 'ebitdaMargins',
    'operating_margins': 'operatingMargins',
    
    ## earnings
    'trailing_eps': 'trailingEps',
    'forward_eps': 'forwardEps',
    
    ## growth
    'earnings_quarterly_growth': 'earningsQuarterlyGrowth',
    'earnings_growth': 'earningsGrowth',
    'revenue_growth': 'revenueGrowth',
    
    ## financials
    'cash': 'totalCash',
    'cash_per_share': 'totalCashPerShare',
    'total_debt': 'totalDebt',
    'EBITDA': 'ebitda',
    'revenue': 'totalRevenue',
    'revenue_per_share': 'revenuePerShare',
    'FCF': 'freeCashflow',
    'OCF': 'operatingCashflow',
    
    ## returns
    'ROA': 'returnOnAssets',
    'ROE': 'returnOnEquity',
}


yfinance_history_interval_period_choices = {
    'interval': ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo'],
    'period': ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max', None],
}