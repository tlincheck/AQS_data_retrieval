# ------------------------------------------------------------------
### PURPOSE: ###

# Load, clean, and process ERG data reports for analysis and visualization
# Calculate quarterly averages by pollutant/site/sampling duration
#       Requires 24hr sample data
# Calculate annual averages from 24hr data (requires quarterly averages
# ------------------------------------------------------------------

#%%  ### Load in necessary libraries ###

# from toxicsdata_functions import unit_convert
from datetime import datetime
import math
import numpy as np
import xarray as xr
import os 
import zipfile
import pandas as pd
import openpyxl
import glob as glob
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import plotly.express as px

#%% ### Specify path to data directory ###

# Load data
path = r"C:\Users\378306\Py_projects\AQS_data_retrieval\ERG_reports\2026" 
files = os.chdir(path)

# list containing data files
files = os.listdir(path) #List all files in specified directory

#%%
# Exclude PDFs and keep only Excel files (.xlsx and .xls)
excel_files = [f for f in files if (f.lower().endswith(('.xlsx', '.xls'))) & ("eto" not in f.lower())] # (not f.startswith(('~$','MA', 'stats')))]
print(excel_files)


# Dictionary to map shorthand month abbreviations to structural dates for sorting
months = { "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, 
          "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
        }


# Helper function to break down the file name into sortable keys
def get_sort_key(filename):
    name, _ = os.path.splitext(filename.lower()) # _ == '.xlsx'
    parts = name.split() # name of file e.g. parts == 'ocok apr 26 voc'

    # Edge-case file handling (e.g., 'aug_dec 25 eto tmok')
    if parts[0].startswith("aug_dec"):
        site = "tmok"
        date_sort = datetime(2025, 8, 1)  # Sorts as August 2025
        label = "eto"
        return (site, date_sort, label)

    # Standard case handling (e.g., 'ocok apr 26 carb')
    site = parts[0]
    label = parts[-1] if "rev1" not in parts else parts[-2] # Handles 'rev1' irregular label

    # Date key extraction from irregular filename structures
    try:
        month_str = parts[1]
        year_str = parts[2]

        # Handles double month ranges (e.g., 'oct25')
        if "oct25" in month_str:
            month_str = "oct"
            year_str = "25"

        month_num = months.get(month_str[:3], 1) # If unexpected str is found, returns Jan == 1 as default
        year_num = int("20" + year_str) if len(year_str) == 2 else int(year_str)
        date_sort = datetime(year_num, month_num, 1)
    
    except Exception:
        date_sort = datetime(2000, 1, 1)  # Fallback date if unexpected structure

    return (site, date_sort, label)


# 4. Sort the filtered Excel list by Site -> Date -> Label
sorted_excel_files = sorted(excel_files, key=get_sort_key)


# 5. Read and merge files chronologically into a single Dataframe
dataframe_list = []
for file in sorted_excel_files:
    try:
        # Read the excel data sheet
        df = pd.read_excel(file)

        # Append source tracking columns to know where the data originated
        df["Source_File"] = file
        df["Site"] = get_sort_key(file)[0].upper()

        dataframe_list.append(df)
        print(f"Successfully loaded: {file}")
    except Exception as e:
        print(f"Skipping error-prone file {file}: {e}")


# Combine everything into a clean final dataset
final_dataframe = pd.concat(dataframe_list, ignore_index=True)
print("\nFinal Dataframe Shape:", final_dataframe.shape)
#%%

### READ IN DATA AND STORE IN PANDAS DATAFRAME ###

# List working directory
dir = os.getcwd() # return abs path of cwd
filedir = os.listdir() # Returns list containing all files and dirs in cwd

#%%
### READ In ONE YR OF DATA ###

yr = 2025 # Define year of interest
# 1. Find & sort data file of specified yr
df_yrFile = sorted(glob.glob(dir + f"\\data\\AMP501_{yr}.csv"))
df_yr_xlsFile = sorted(glob.glob(dir + f"\\data\\AMP501_{yr}.xlsx"))

# 2. Read data from file into Pandas dataframes
df_yr_csv = pd.read_csv(df_yrFile[0], sep='|', skiprows=[1], engine='python', skipfooter=1)
df_yr_xls = pd.read_excel(df_yr_xlsFile[0], sheet_name='Raw Data', skipfooter=1)
