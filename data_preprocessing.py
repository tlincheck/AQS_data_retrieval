# ------------------------------------------------------------------
### PURPOSE: ###

# Calculate quarterly averages by pollutant/site/sampling duration
#       Requires 24hr sample data
# calculate annual averages from 24hr data (requires quarterly averages)
# ------------------------------------------------------------------

#%%  
### Load in necessary packages ###

# from toxicsdata_functions import unit_convert
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


#%%
### READ ALL YRS OF DATA ###

# Locate + sort files in directory
csv_files = sorted(glob.glob(dir + "\\data/[A]*.csv")) # [A]* -> only look for files that start with 'A'
data_files = sorted(glob.glob(dir + "\\data/[A]*.xlsx")) #Create list of .xlsx files in data directory; [! ] tells glob to ignore specified symbols

# Concatenate all years of data
df_xlsx = pd.concat([pd.read_excel(f, sheet_name='Raw Data', skipfooter=1) for f in data_files]) # 'skipfooter' skips the comment line at the bottom of each xlsx file
df = pd.concat([pd.read_csv(f, sep='|', skiprows=[1], engine='python', skipfooter=1) for f in csv_files]) # 'skiprow=[1]' skips the # RC title row in each csv file

#%%
##### READ IN ADDITIONAL DATA TABLES #####

parameters = pd.read_csv('parameters.csv') # Pollutant (i.e. parameter) names
units = pd.read_csv('units.csv') # Unit codes and corresponding unit names
quals = pd.read_csv('qualifiers.csv', encoding='latin1') # qualifier codes and descriptions

#%%
### FORMAT PANDAS DATAFRAMES ###

# Updating 'Date' column to datetime obj (Format = YYYYMMDD)
df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d')
# df_xlsx['Date'] = pd.to_datetime(df_xlsx['Date'], format='%Y%m%d')
# {1-year df} df_yr_csv['Date'] = pd.to_datetime(df_yr_csv['Date'], format='%Y%m%d', inplace='True')

# Updating 'Start Time' column to datetime obj (Format = Hour:Minute:Sec)
df['Start Time'] = pd.to_datetime(df['Start Time'], format='%H:%M')
# df_yr_csv['Start Time'] = pd.to_datetime(df_yr_csv['Start Time'], format='%H:%M') # format='%H:%M:%S for excel df

# Drop 'Action Code' column since it's not needed for analysis
df.drop(columns=["Action Code"], inplace=True)
df_xlsx.drop(columns=["Action Code"], inplace=True)
# df_yr_csv.drop(columns=["Action Code"])

# Rename column headers to merge with other tables
df.rename(columns={'Parameter' : 'Parameter Code', 'Unit' : 'Unit Code'}, inplace=True)
df_xlsx.rename(columns={'Parameter' : 'Parameter Code', 'Unit' : 'Unit Code'}, inplace=True)


#%%
### MERGE DATA TABLES INTO PANDAS DATAFRAME ###

# Merge parameters dataframe into df to match 'Parameter' names with 'Parameter Codes'
merged_df1 = df.merge(parameters, how='inner', on='Parameter Code')
merged_df = merged_df1.merge(units, how='inner', on='Unit Code')

#%%


# Locate specific parameter given a condition
i = 43502
param_name = merged_df.loc[merged_df['Parameter Code'] == i, 'Parameter'].iat[0]

# %%

##### PREPROCESSING STEPS
# 1. Check for duplicates - make sure that there's only 1 sample per pollutant/site/date
#       FILTER FOR 6-DAY SAMPLING SCHEDULE!
#       i. Ensure all null data qualified data is null or nan
#      ii. Filter out 
#     iii. Handle any duplicates or replicate data --> per date/pollutant/site

##### CALCULATE QUARTERLY AVERAGES
# a. Count number of samples per quarter
#       i. assign quarter 1,2,3,4 to each value
# b. Include substitution of zeros '0' for NDs in count for average

# ------------------------------------------------------------------
def daily2annual():
    # INITIALIZE GLOBAL VARIABLES
    daysINquarter_min = 6 # minimum number of 24hr average samples needed to create a valid quarter
    quartINyr_min = 3 # minimum number of valid quarters needed to create a valid annual average

# ------------------------------------------------------------------

#### Code graveyard ####

# data_dir = r"C:\Users\378306\OneDrive - State of Oklahoma\\ToxicsData"

# Old code to search directory for .xlsx data files 
files_xlsx = [f for f in filedir if (f[-3:] == 'xls' or f[-4:] == 'xlsx') & (not f.startswith(('~$','MA', 'stats')))]
print(files_xlsx)
