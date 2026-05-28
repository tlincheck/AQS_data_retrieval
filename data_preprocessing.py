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
import plotly.express as px

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
methods_haps = pd.read_csv('methods_haps.csv') # method codes and descriptions for HAPs
MAAC_values = pd.read_csv('MAAC_values.csv') # MAAC values for each pollutant
MAAC_values["Parameter Code"] = MAAC_values["Parameter Code"].astype('Int64')  # Convert parameter code to int to match dataframes

#%%
### FORMAT PANDAS DATAFRAMES COLUMNS ###

# Updating 'Date' column to datetime obj (Format = YYYYMMDD)
df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d')
df_yr_csv['Date'] = pd.to_datetime(df_yr_csv['Date'], format='%Y%m%d')
# {1-year df} df_yr_csv['Date'] = pd.to_datetime(df_yr_csv['Date'], format='%Y%m%d', inplace='True')

# Updating 'Start Time' column to datetime obj (Format = Hour:Minute:Sec)
df['Start Time'] = pd.to_datetime(df['Start Time'], format='%H:%M')
df_yr_csv['Start Time'] = pd.to_datetime(df_yr_csv['Start Time'], format='%H:%M') # format='%H:%M:%S for excel df

# Drop 'Action Code' column since it's not needed for analysis
df.drop(columns=["Action Code"], inplace=True)
df_xlsx.drop(columns=["Action Code"], inplace=True)
df_yr_csv.drop(columns=["Action Code"], inplace=True)

# Rename column headers to merge with other tables
df.rename(columns={'Parameter' : 'Parameter Code', 'Unit' : 'Unit Code', 'Method' : 'Method Code'}, inplace=True)
df_xlsx.rename(columns={'Parameter' : 'Parameter Code', 'Unit' : 'Unit Code', 'Method' : 'Method Code'}, inplace=True)
df_yr_csv.rename(columns={'Parameter' : 'Parameter Code', 'Unit' : 'Unit Code', 'Method' : 'Method Code'}, inplace=True)


#%%

# REMOVE SAMPLES WITH NULL DATA (Marked by Null Data Code)
mask = df["Null Data Code"].isnull() # Creates a mask for valid samples - "null data code" == NaN returns True
dff = df[mask] # dff stands for filtered df

# REMOVE PARTICULATE SPECIATION DATA (i.e. FROM SASS INSTRUMENT) IF PRESENT IN DATA
method_codes = dff["Method Code"].unique()
methods_to_remove = [126, 800, 811] # List method codes to remove (126 - )
dff_temp = dff[~dff["Method Code"].isin(methods_to_remove)] # Keep rows which do NOT contain specified method codes

#### REMOVE DUPLICATE SAMPLES WHEN MORE THAN 1 PER DAY ####
#Define lists to loop through below
param_codes = dff_temp["Parameter Code"].unique()
sites = dff_temp["Site ID"].unique()

dffs_list = []

for i in param_codes: # For each parameter & each site, 
    # print(f"Parameter = {i}")
    for id in sites:
        # print the number of POC samples for each pollutant/site
        # print(len(df.loc[(df["Parameter Code"]==i) & (df["Site ID"]==id)]["POC"].unique()))
        n_samples = len(dff_temp.loc[(dff_temp["Parameter Code"]==i) & (dff_temp["Site ID"]==id)]["POC"].unique())
        # print(f"Number of samples={n_samples}")
        # print(n_samples > 1)
 
        # If POC > 1, proceed to locate and remove collocated samples
        if n_samples > 1:
            print(n_samples)
            print(f"Parameter {i} has collocated samples at site={id}")

            # retrieve dataframe for one parameter & site
            param_df = dff_temp.loc[(dff_temp["Parameter Code"]==i) & (dff_temp["Site ID"]==id)]

            # create boolean mask where duplicate dates are marked as "True"
            # dups_mask = dff.loc[(dff["Parameter Code"]==i) & (dff["Site ID"]==id)].duplicated(subset=["Date"])
                    
            # Drop duplicates/collocates
            no_dups = dff_temp.loc[(dff_temp["Parameter Code"]==i) & (dff_temp["Site ID"]==id)].drop_duplicates(subset=["Date"], keep='first').copy()

            # print(no_dups["Date"].value_counts())

            # append parameter dataframe without duplicates (e.g. without POC == 7 or 8)
            dffs_list.append(no_dups)

        else:
            # Append subsetted dataframe
            param_df_nodups = dff_temp.loc[(dff_temp["Parameter Code"]==i) & (dff_temp["Site ID"]==id)]
            dffs_list.append(param_df_nodups)


# resulting df without duplicate values
dffs = pd.concat(dffs_list, ignore_index=True)
# result = pd.concat(dffs_temp, ignore_index=True)

#%%

# CHECK THAT ALL NON-DETECTS 'ND' ARE REPORTED AS ZEROS
# TODO: Create routine to handle instances of '0's in non-detects
non_detect_sample_vals = (dffs.loc[dffs['Qualifier - 1'] == 'ND', 'Sample Value'].unique()).astype(int)

# CONVERT NEGATIVE CONCENTRATIONS TO ZERO AND FLAG ACCORDINGLY AS "ND"
# TODO: ADD QA FLAG COLUMN 

#%%

# CHECK THE 1-IN-6 SCHEDULE FOR EACH POLLUTANT PER SITE

# Define start and end dates of 1-in-6 schedule
start_date = dffs['Date'].min()
end_date = dffs['Date'].max()

# Generate 6-day frequency range of dates for 1-in-6 schedule
date_range = pd.date_range(start=start_date, end=end_date, freq='6D') # Create date range for entire period of record

# Evaluate each entry of dffs['Date'] and return True if that value is in the 1-in-6 schedule; False if not
dffs['Date'].isin(date_range) 

# Create new column to flag samples that do not match 1-in-6 schedule; True = sample does NOT match schedule;
dffs['Makeup Sample'] = ~(dffs['Date'].isin(date_range)) #  False = sample matches 1-in-6 schedule

#%%

# CONVERT NEGATIVE SAMPLE VALUES TO ZERO AND FLAG AS "ND"

# If sample value is negative, flag as "ND"; else flag as "Valid"
dffs["Sample Value Flag"] = np.where(dffs["Sample Value"] < 0.0, "ND", "Valid") 

# If sample value is negative, convert to 0; else keep original value
dffs["Sample Value"] = np.where(dffs["Sample Value"] < 0.0, 0.0, dffs["Sample Value"]) # np.where(condition, value_if_true, value_if_false)


# df.groupby(["Parameter Code", "Site ID", "Date"])["Date"].agg(['count'])
#%%

### MERGE DATA TABLES INTO PANDAS DATAFRAME ###
 
# Merge parameters dataframe into dffs to match 'Parameter' names with 'Parameter Codes'
merged_params = pd.merge(dffs, parameters, how='inner', on='Parameter Code')
merged_units = merged_params.merge(units, how='inner', on='Unit Code') # Merge units df into sample df

merged_dffs = merged_units.merge(MAAC_values[['Parameter Code', 'MAAC ppb', 'MAAC ug/m3', 'Type']],\
                                  how='left', on='Parameter Code') # Merge MAAC values into sample df; use left join to keep all rows in sample df


### SORT THE COLUMNS IN THE DESIRED ORDER ###
cols_list = merged_dffs.columns.tolist()

post_dff = merged_dffs[['# RD',
                    'State Code', 'County Code', 'Site ID', 'Parameter Code', 'Parameter', \
                    'Parameter Abbreviation','Parameter Alternate Name', 'CAS Number', 'POC', \
                    'Sample Duration','Unit Code', 'Units', 'Method Code', 'Date', 'Start Time',\
                    'Sample Value', 'Null Data Code','Sampling Frequency', 'Qualifier - 1', \
                    'Qualifier - 2', 'Qualifier - 3', 'Alternate Method Detectable Limit',\
                    'Makeup Sample','Standard Units','Still Valid','Round or Truncate',\
                    'MAAC ppb', 'MAAC ug/m3', 'Type']].copy()

# Omitting  following columns:
# 'Monitor Protocol (MP) ID', 'Qualifier - 4',
# 'Qualifier - 5',
# 'Qualifier - 6',
# 'Qualifier - 7',
# 'Qualifier - 8',
# 'Qualifier - 9',
# 'Qualifier - 10',
# 'Uncertainty',

#%%

### SAVE POST_PROCESSED DATAFRAME TO CSV ###


path = dir + '\\merged_data_processed.xlsx'
post_dff.to_excel('merged_data_processed.xlsx', index=False)
post_dff.to_csv('merged_data_processed.csv', index=False)

#%%

### SAVE RAW MERGED DATAFRAME AS CSV FILE ###

path = dir + '\\merged_data_raw.xlsx'
# xlwriter = pd.ExcelWriter(path=path, engine='openpyxl') # mode='a'


# merged_df.to_excel('merged_data_raw.xlsx', index=False)
#merged_df.to_csv('merged_data_raw.csv', index=False)
#with pd.ExcelWriter('existing_file.xlsx', mode='a', engine='openpyxl') as writer:
#   df.to_excel(writer, sheet_name='Sheet2')




#%%
'''
for i in param_codes:
# print(f"Param code={i}. dtype={type(i)}")

# Where condition "parameter code" = True, return parameter name and unit
param_name_str = df.loc[df_AllYears['Parameter Code'] == i, 'Parameter Name'].iat[0] # Parameter name; str
param_name = param_name_str.split( "(", maxsplit=1)[0]
param_unit = df_AllYears.loc[df_AllYears['Parameter Code'] == i, 'Units of Measure'].iat[0]
print(f"Parameter = {param_name}")
print(f"Units = {param_unit}")

# Locate groupby dataframe for parameter 'i'
stats = df_stats.loc[i] # Annual means, max values, and counts for each 

# Reset the row index
stats.reset_index(inplace=True) # Resets index from Site Num to #; retains Site Num as column ()

# Create pivot table of Annual Means for specific parameter from grouped dataframe 
pivot = stats.pivot(index='year', columns='Site Num', values='mean')
print(pivot)

# Append pivot table to list for storage
pivot_tables.append(pivot)



df.loc[df["Parameter Code"]==12103, "Date"]

# What was the number of sample values, per parameter AND per Site
# for each distinct parameter code -- categorical data
# for each distinct site -- categorical data
# what was the number of samples?

'''

#%%

# %%

# title = sample_df['Parameter'].iat[0]
# df['Sample Value']

# x and y given as DataFrame columns
# df = px.data_df() # iris is a pandas DataFrame
# fig = px.scatter(sample_df, x="Date", y="Sample Value", color="Site ID", title="Parameter")
# fig.show()


#%%



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
# files_xlsx = [f for f in filedir if (f[-3:] == 'xls' or f[-4:] == 'xlsx') & (not f.startswith(('~$','MA', 'stats')))]
# print(files_xlsx)


# REMOVE METHOD CODES: 800, 811 - SASS and 126 - VOCS in ppbC 
# methods_rm = [126, 800, 811]
# method_mask = dff[~dff["Method"].isin(methods_rm)]


### REMOVE TRIBAL SITES ###
# tribal_sites = [9000, 9001, 9009]
# deq_sites = dffs[~dffs["Site ID"].isin(tribal_sites)] 

# result.loc[(result["Parameter Code"]==12103) & (result["Site ID"]==235)]["Date"].value_counts().unique()

# result.groupby(["Parameter Code", "Site ID", "Date"])["Date"].agg(['count']).max()

# Check that all "ND" sample values are reported as "0"
# non_detects = result.loc[result["Qualifier - 1"] == "ND", "Sample Value"].unique()
# print(f"ND values = {non_detects}")

# # Locate specific parameter given a condition
# i = 43502
# param_name = merged_df.loc[merged_df['Parameter Code'] == i, 'Parameter'].iat[0]
# param_series = merged_df.loc[merged_df['Parameter Code'] == i, 'Parameter']

# sample_vals = merged_df.loc[merged_df['Parameter Code'] == i, 'Sample Value']
# dates = merged_df.loc[merged_df['Parameter Code'] == i, 'Date']

#dataframe for one parameter
# sample_df = merged_df.loc[merged_df['Parameter Code'] == i]
