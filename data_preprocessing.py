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
# Load AQS data file(s)
files = os.listdir()

# data_dir = r"C:\Users\378306\OneDrive - State of Oklahoma\\ToxicsData"

files_xlsx = [f for f in files if (f[-3:] == 'xls' or f[-4:] == 'xlsx') & (not f.startswith(('~$','MA', 'stats')))]
print(files_xlsx)



#%%
##### READ IN DATA AND STORE IN DATAFRAME #####

dir = os.getcwd()
# [A]* -> only include files that start with '2'
data_files = sorted(glob.glob(dir + "\\data/[A]*.xlsx")) #Creates list of .xlsx files in data directory; [! ] tells glob to ignore specified symbols
csv_files = sorted(glob.glob(dir + "\\data/[A]*.csv"))

df = pd.concat([pd.read_excel(f, sheet_name='Raw Data') for f in data_files]) #List comprehension method - creates a list of Pandas DataFrame objects, which are then concatenated into one large DataFrame
df_csv = pd.concat([pd.read_csv(f, sep='|', skiprows=[1], engine='python', skipfooter=1) for f in csv_files])

#%%
#TODO Check .csv file and .xlsx data files are identical -> checks .csv formatting methods are correct

# Drop 'Action Code' column since it's not needed for analysis
df.drop(columns=["Action Code"])
df_csv.drop(columns=["Action Code"])

# Rename column headers for merging with other tables
df.rename(columns={'Parameter' : 'Parameter Code'}, inplace=True)
df_csv.rename(columns={'Parameter' : 'Parameter Code', 'Unit' : 'Unit Code'}, inplace=True)



#%%
##### READ IN ADDITIONAL DATA TABLES #####
# Pollutant (i.e. parameter) names
parameters_df = pd.read_csv('parameters.csv')


#%%
# Merge parameters dataframe into df to match 'Parameter' names with 'Parameter Codes'
merged_df = df.merge(parameters_df, how='inner', on='Parameter Code')

#%%

#Join 



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