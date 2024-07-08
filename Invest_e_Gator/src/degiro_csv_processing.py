import os
from typing import List

import pandas as pd
import numpy as np

import finnhub
from ratelimit import limits, sleep_and_retry
import time

from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

class CSVMerger:
    def __init__(self, path_folder_csv_transactions, name_pf):
        self.path_folder_csv_transactions  = path_folder_csv_transactions
        self.name_pf = name_pf
        
        os.makedirs(os.path.join(self.path_folder_csv_transactions, 'persisted_data'), exist_ok=True)
        self.path_processed_files = os.path.join(self.path_folder_csv_transactions, 'persisted_data', "processed_files.txt")
        self.path_all_transactions = os.path.join(self.path_folder_csv_transactions, 'persisted_data', "all_transactions.csv")
            
        self.processed_files = []
        self.all_transactions = pd.DataFrame()
        
        self._retrieve_existing_calcs()


    def _retrieve_existing_calcs(self):
        # check if a file tracking processed files exists
        if os.path.exists(self.path_processed_files):
            # if it does, read the names of the processed files from it
            with open(self.path_processed_files, 'r') as f:
                self.processed_files = f.read().splitlines()
 
        # check if the all_transactions.csv file already exists
        if os.path.exists(self.path_all_transactions):
            # if it does, read the existing data into the all_transactions DataFrame
            self.all_transactions = pd.read_csv(self.path_all_transactions)       


    def process_files(self): 
        # os.scandir() function to iterate over the files in directory transactions
        # then use the os.stat() function to get the file's creation time, which you can use to sort the files by date of creation
        transac_files = [(f.name, f.stat().st_ctime) for f in os.scandir(self.path_folder_csv_transactions) if f.is_file()]
        # Sort by creation time
        transac_files.sort(key=lambda x: x[1])
        # List of file names sorted by creation date
        file_names = [file[0] for file in transac_files]

        # iterate over the files in the specified directory
        for file in file_names:
            # check if the file is a CSV and if it has not been processed before
            if file.endswith('.csv') and file not in self.processed_files:
                # read the CSV file into a DataFrame
                df = pd.read_csv(os.path.join(self.path_folder_csv_transactions, file))
                #Reverse rows (transactions) order + reset index
                df = df.loc[::-1].reset_index(drop=True)
                # drop rows that have no date, romve some bugs in data export of degiro
                df = df.dropna(subset=['Date'])
                # append the file name to the processed_files list
                self.processed_files.append(''.join([self.name_pf, '_', file]))          
                # append the data from the CSV file to the all_transactions DataFrame
                self.all_transactions = pd.concat([self.all_transactions, df], ignore_index=True)
                # Necessary drop duplicates (some lines with NaN value are not droped with classical .drop_duplicates() when we retrieve preexisting data)
                                 # Date, Hour, Product, ISIN code, Brokerage fee, Negociated price, Order ID
                column_indices = [0, 1, 2, 3, 14, 16, 18]
                self.all_transactions = self.all_transactions.drop_duplicates(subset=self.all_transactions.columns[column_indices], keep='first')

    def write_to_csv(self):
        # write the combined data to a new CSV file
        self.all_transactions.to_csv(self.path_all_transactions, index=False)
        # write the names of the processed files to a file
        with open(self.path_processed_files, 'w') as f:
            for file in self.processed_files:
                f.write("%s\n" % file)
                
                
    def get_data(self) :
        return(self.all_transactions)
     
         

               
class DataProcess:
    
    def __init__(self, df:pd.DataFrame, 
                       mapper_file_path:str,
                       output_folder_path:str):
        self.df = df
        self.mapper_file_path = mapper_file_path
        self.output_folder_path = output_folder_path
        
        self.degiro_Date_Hour_format = '%d-%m-%Y %H:%M'
  
    def _check_tickersymbol_column(self):
        # Access rows without value in the 'Ticker Symbol' column
        rows_wo_tick = self.df[self.df['Ticker_symbol'].isna()]
        # Drop row that contains 'NON TRADEABLE' in their product name
        rows_wo_tick = rows_wo_tick[rows_wo_tick["Product"].str.contains("NON TRADEABLE") == False]
        # isin for which we didnt retrieve ticker symbol
        not_found_isin = rows_wo_tick['ISIN_code'].unique().tolist()
        
        if not_found_isin:
            raise ValueError(f"Couldn't find ticker symbol for the following isin codes: {not_found_isin}. Please provide them via the mapper csv file.")
    
    def _get_ticker_symbol_from_isin_via_finnhub(self):
        ONE_MINUTE = 60

        
        @sleep_and_retry
        @limits(calls=50, period=ONE_MINUTE)
        # 60 api calls max per minute
        def finnhub_api_call_symbl_lookup(isin):
            output = finnhub_client.symbol_lookup(isin)
            # {'count': 1, 'result': [{'description': 'Tomra Systems ASA', 'displaySymbol': 'TOM.OL', 'symbol': 'TOM.OL', 'type': 'Common Stock'}]}
            print('OK')
            
            return output['result'][0]['symbol'], output['result'][0]['type']
        
        
            SET UP SOMETHING TO CATCH POTENTIAL ERRORS
        
        def add_ticker_symbol(row):
            return ISIN_results[row['ISIN_code']]['ticker']
        
        def add_product_type(row):
            return ISIN_results[row['ISIN_code']]['type']
        
        # Get API key
        FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
        if FINNHUB_API_KEY is None:
            raise ValueError("No API key found. Set the FINNHUB_API_KEY environment variable.")
        # Get finnhub client
        finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)

        ISIN_results = {}
        ISIN_codes = self.df['ISIN_code'].unique().tolist()
        
        print('We will perform 60 API calls per minute to finnhub ')
        
        for isin in ISIN_codes:
            ticker_symbol, product_type = finnhub_api_call_symbl_lookup(isin)
            ISIN_results[isin] = {'ticker':ticker_symbol, 'type':product_type}
        
        # Apply the function to the 'ISIN_code' column and create a new 'Ticker_symbol' column
        self.df['Ticker_symbol'] = self.df['ISIN_code'].apply(add_ticker_symbol)
        self.df['Product_type'] = self.df['ISIN_code'].apply(add_product_type)
        
        print(self.df.columns,'\n', self.df)

    def _add_ticker_symbol(self):
        try:
            df_map = None
            # Check whether a path pointing to a file
            if os.path.isfile(self.mapper_file_path):
                df_map = pd.read_csv(self.mapper_file_path)  
            # Map 'Ticker Symbol' values (present in file ticker_list) in self.df according to 'Product' 
            self.df["Ticker_symbol"] = self.df["ISIN_code"].map(df_map.set_index("ISIN_code")["Ticker_symbol"])
            #self.df["Product_type"] = self.df["ISIN_code"].map(df_tickers.set_index("ISIN_code")["Product_type"])   
        except Exception:
            print(f'No mapper csv file (isin/ticker mapper) at the provided path : {self.mapper_file_path}. Fallback to _get_ticker_symbol_from_isin method to retrieve ticker symbols.')
            # Fallback to this method to get ticker symbols
            self._get_ticker_symbol_from_isin_via_finnhub()

        self._check_tickersymbol_column()
    


    def process_data (self):
        # Perform data cleaning and manipulation with the row appended csv file
        #Check if columns are in english 
        column_names = ['Date', 'Hour', 'Product', 'ISIN_code', 'Exchange', 'Venue', 'Quantity', 
                        'Share_price', 'Currency_SP', 'Total_price', 'Currency_TP', 'Total_price_in_my_currency', 
                        'Currency_TPIMC', 'Change_rate', 'Fee', 'Currency_fee', 'Total_paid', 'Currency_paid', 'ID_order']
        # if number columns = number elements in column_names 
        if len(self.df.axes[1]) == len(column_names) :
            #Change column names of the dataframe if df's column names != column_names
            result = all(col1 == col2 for col1, col2 in zip(self.df.columns, column_names))
            if not result:
                self.df.rename(columns=dict(zip(self.df.columns, column_names)), inplace=True) 
        else:
            ValueError("There should be 19 columns in the df.")      
            
        # remove rows without date
        self.df.dropna(subset = ['Date'], inplace= True)
        # remove duplicate rows from the all_transactions DataFrame
        self.df = self.df.drop_duplicates().reset_index(drop=True)
        # Combine 'date' and 'hour' columns and convert to datetime
        self.df['Datetime'] = pd.to_datetime(self.df['Date'] + ' ' + self.df['Hour'], format=self.degiro_Date_Hour_format)
        self.df.drop(columns=['Date', 'Hour'])
        # Convert the datetime to the desired format (american datetime) as string
        self.df['Datetime'] = self.df['Datetime'].dt.strftime('%m-%d-%Y %H:%M:%S')

        # Based on the mapper file or morningstar wrapper, add ticker
        self._add_ticker_symbol()

    def write_to_csv(self):
        # Create path if it doesn't exist
        if not os.path.exists(self.output_folder_path): 
            os.makedirs(self.output_folder_path)
        # write data to a new CSV file
        self.df.to_csv(os.path.join(self.output_folder_path, 'cleaned_transactions.csv'), index=False)
        
    def get_processed_df(self):
        return(self.df)
    
    
    
    
    
    
    
    
    
    
    
    
class DegiroCsvProcess:
    def __init__(self):
        # Access the Parent 'Portfolio' folder
        self.Invest_e_Gator_path = os.path.abspath(os.path.join(__file__ , "../.."))
        self.degiro_transactions_path = os.path.join(self.Invest_e_Gator_path, 'data', 'degiro_transactions')
        # Get folder names in self.degiro_transactions_path (i.e the different portfolios)
        self.pf_names = [pf for pf in os.listdir(self.degiro_transactions_path) if os.path.isdir(os.path.join(self.degiro_transactions_path, pf))]
        
        self.transaction_dfs = {}
        self.processed_dfs = {}
        
    def process_and_clean(self, pfs:List[str]=None):
        pf_names = self.pf_names if not pfs else pfs 
        
        for pf_name in pf_names:
            self.run_csv_processing(pf_name)
            self.run_data_cleaning(pf_name)
        
        
    def run_csv_processing(self, pf_name:str):         
        csv_process = CSVMerger(os.path.join(self.degiro_transactions_path, pf_name, 'transactions'), pf_name)
        csv_process.process_files()
        csv_process.write_to_csv()
        self.transaction_dfs[pf_name] = csv_process.get_data()   
        
    def run_data_cleaning(self, pf_name:str):
        transactions_df = self.transaction_dfs[pf_name]
        # Init DataProcess object
        cl = DataProcess(transactions_df, 
                        os.path.join(self.degiro_transactions_path, pf_name, 'mapper_file.csv'),
                        os.path.join(self.degiro_transactions_path, pf_name, 'cleaned_transactions'))
        # Clean the dataframe (add columns names, drop duplicates etc)
        cl.process_data()
        # Write final transaction files cleaned
        cl.write_to_csv()
        self.processed_dfs[pf_name] = cl.get_processed_df()
 
    
    
    def fuse_pfs(self, pfs_names:List[str]):
        if pfs_names < 2:
            raise ValueError("pfs_names arg should be a list containing at least two portfolio names as str type.")
        
        if not all([self.processed_df.get(pf_name) for pf_name in pfs_names]):
            raise ValueError("All portfolio names provided should be processed first.")
        
        fused_df = self.processed_df[pfs_names[0]]

        for pf_name in pfs_names[1:]:
            fused_df = pd.concat([fused_df, self.processed_df[pf_name]])
            
        fused_df = fused_df.sort_values(by='Datetime')
        


if __name__ == "__main__":

    degiro_process = DegiroCsvProcess()
    degiro_process.process_and_clean(pfs=['Val_test'])
    
    

    
    
    






