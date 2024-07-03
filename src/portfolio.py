


class Portfolio():
    def __init__(self):

        self.transaction_obj = []
        self.transaction_csv = None
        
        
    def load_transactions_csv(self, csv_file):
        
        VALID CSV FILE 
        VALID COLUMN CSV FILE ()
        PARSE CSV ROWS to Transaction Class 
        
    def add_transaction
        ADD TRANSACTION
        GET ALL TICKERS TRANSACTIONS, RETURN WHICH ARE NOT AVAILABLE AND CLEAN TRANSACTION
        
    def build_df:
        if there is a csv file loaded:
            KEEP WANTED COLUMNS (see Transaction Class)
            transaform df
            
            if there are some manually added transaction:
                parse transaction list add to df and sort by DATE_HOUR
                
        elif there are mannualy added transactions:
            Parse them and create a df
    
    
    def _df_metrics:
        
        ADD TAGS IN TRANSACTIONS !!!!!!
        
        
        stocks hold at a date
        cumulative investement (money you spent)
        
        Metrics computed via yfinance (ticker daily/weekly/etc prices) + df (positions held at that time):

        daily portfolio value (Net Asset Value)
        daily net_pl (Net Asset Value - investment)
        daily net_pl specific TAGS (sectors)
        
        cumulative Net Asset Value
        cumulative net_pl 
        cumulative net_pl  specific TAGS (sectors)
        
        annual returns CAGR 
        annual volatility 
        
        sharpe ratio 
        sortino ratio
        
        max drawdown 
        max drawdown date 
        



        
        portfolio drawdown     
        last Net Asset Value (current portfolio value)

        