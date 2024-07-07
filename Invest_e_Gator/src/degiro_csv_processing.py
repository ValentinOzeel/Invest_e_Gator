import os
import pandas as pd
import numpy as np

class CSVProcessor:
    def __init__(self, path_csv_transactions, name_pf):
        self.path_csv_transactions  = path_csv_transactions
        self.name_pf = name_pf
        
        self.path_processed_files = os.path.join(self.path_csv_transactions, 'persisted_data', "processed_files.txt")
        self.path_all_transactions = os.path.join(self.path_csv_transactions, 'persisted_data', "all_transactions.csv")
        
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
        if os.path.exists(self.path_all_row_transactions):
            # if it does, read the existing data into the all_transactions DataFrame
            self.all_transactions = pd.read_csv(self.path_all_row_transactions)       


    def process_files(self): 
        # os.scandir() function to iterate over the files in directory transactions
        # then use the os.stat() function to get the file's creation time, which you can use to sort the files by date of creation
        transac_files = [(f.name, f.stat().st_ctime) for f in os.scandir(self.path_csv_transactions) if f.is_file()]
        # Sort by creation time
        transac_files.sort(key=lambda x: x[1])
        # List of file names sorted by creation date
        file_names = [file[0] for file in transac_files]

        # iterate over the files in the specified directory
        for file in file_names:
            # check if the file is a CSV and if it has not been processed before
            if file.endswith('.csv') and file not in self.processed_files:
                # read the CSV file into a DataFrame
                df = pd.read_csv(os.path.join(self.path_csv_transactions, file))
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

    def write_processed_files(self):
        # write the names of the processed files to a file
        with open(self.path_processed_files, 'w') as f:
            for file in self.processed_files:
                f.write("%s\n" % file)
                
    def get_data(self) :
        return(self.all_transactions)
     
         