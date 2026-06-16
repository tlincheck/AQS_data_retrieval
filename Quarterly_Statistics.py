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

# Load in processed data
data = 'merged_data_processed.csv'
df = pd.read_csv(data)

# %%

### CALCULATE QUARTERLY STATISTICS ###

# For each year/quarter/pollutant/site, calculate the quarterly mean and max values

mon_arr = pd.to_datetime(df['Date']).dt.month

# Create a new column to assign each row to a quarter; 
# (1 = Jan-Mar, 2 = Apr-Jun, 3 = Jul-Sep, 4 = Oct-Dec). 
df['Quarter'] = pd.to_datetime(df['Date']).dt.quarter

# Create a new column for year
df['Year'] = pd.to_datetime(df['Date']).dt.year

# Function to detect outliers using IQR method
def count_outliers(x):
    Q1 = x.quantile(0.25)
    Q3 = x.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return sum((x < lower_bound) | (x > upper_bound))

# Group by year, quarter, pollutant, and site, then calculate mean and max
quarterly_stats = df.groupby(['Year', 'Quarter', 'Parameter', 'Site ID']).agg(
    Quarterly_Mean=('Sample Value', 'mean'),
    Quarterly_Max=('Sample Value', 'max'),
    Sample_Count=('Sample Value', 'count'),
    avg_MDL=('Alternate Method Detectable Limit', 'mean'),
    # MDL_Outlier_Count=('Alternate Method Detectable Limit', count_outliers)
).reset_index() 

#%%
# Check for MD qualifiers. Mark MD values as True (BMDL)
df['BMDL'] = df[['Qualifier - 1', 'Qualifier - 2', 'Qualifier - 3']].apply(
    lambda row: True if any('MD' in str(val) for val in row if pd.notna(val)) else None, # True if any qualifier contains 'MD'
    axis=1
)

# Searches for 'ND' qualifiers and 'MD' qualifiers. If 'MD' is found, marks as 'MD'. If 'ND' is found and no 'MD', marks as 'ND'. Otherwise, leaves as None.
df['Status'] = df[['Qualifier - 1', 'Qualifier - 2', 'Qualifier - 3']].apply(
    lambda row: 'MD' if any('MD' in str(val) for val in row if pd.notna(val)) 
                 else 'ND' if any('ND' in str(val) for val in row if pd.notna(val))
                 else None,
    axis=1
)



#%%

# ADD ADDITIONAL COLUMNS TO QUARTERLY_STATS


# Assign 'True' or 'False' in quarterly_stats['Valid Quarter'] based on count in quarterly_stats
# If sample count is >= 12, mark as 'True' (valid quarter). If sample count is < 12, mark as 'False' (invalid quarter).
quarterly_stats['Valid Quarter'] = quarterly_stats['Sample_Count'].apply(lambda x: True if x >= 12 else False)

# Join MDL column to quarterly_stats
quarter_stats = quarterly_stats.merge(df[['Year', 'Quarter', 'Parameter', 'Site ID', 'BMDL']], 
                                        on=['Year', 'Quarter', 'Parameter', 'Site ID'], 
                                        how='left')   #  








#%%

### DETERMINE PERCENTAGE OF SAMPLES THAT WERE ABOVE MDL ###
form_23 = df[(df["Parameter Code"] == 43502) & (pd.to_datetime(df['Date']).dt.year == 2023)]


form_1127 = df[(df["Parameter Code"] == 43502) \
               & (pd.to_datetime(df['Date']).dt.year == 2023) \
               & (df['Site ID'] == 1127)]


# By pollutant, year, and site, calculate the min, max, and average MDL values
mdls = df.groupby(['Year', 'Parameter', 'Site ID']).agg(
    avg_MDL=('Alternate Method Detectable Limit', 'mean'),
    min_MDL=('Alternate Method Detectable Limit', 'min'),
    max_MDL=('Alternate Method Detectable Limit', 'max')
).reset_index()

#%%

# Plot quarterly_stats as box and whisker plot

yr = 2025
pmtr = 'Formaldehyde'

data = df[(pd.to_datetime(df['Date']).dt.year == yr) & 
                       (df['Parameter'] == pmtr)].copy()

qty_data = quarterly_stats[(quarterly_stats['Year'] == yr) & (quarterly_stats['Parameter'] == pmtr)].copy

fig = px.box(data, y='Quarterly_Mean')



#%%
# This cell plots the quarterly average values for Formaldehyde at each site for the year 2025.

# Filter quarterly_stats for Formaldehyde and year 2025
formaldehyde_2025 = quarterly_stats[(quarterly_stats['Parameter'] == 'Formaldehyde') & 
                                     (quarterly_stats['Year'] == 2025)]

# Create a figure with subplots for each site
fig, axes = plt.subplots(figsize=(14, 8))

# Get unique sites
sites = formaldehyde_2025['Site ID'].unique()

# Create a grouped bar chart
for i, site in enumerate(sites):
    site_data = formaldehyde_2025[formaldehyde_2025['Site ID'] == site].sort_values('Quarter')
    x_pos = [q + (i * 0.2) for q in site_data['Quarter_Number']]
    print(x_pos)
    axes.bar(x_pos, site_data['Sample_Value'], width=0.18, 
             label=f'Site {site}', alpha=0.8)

axes.set_xlabel('Quarter', fontsize=12, fontweight='bold')
axes.set_ylabel('Average Sample Value (ppbC)', fontsize=12, fontweight='bold')
axes.set_title('Formaldehyde - Quarterly Averages by Site (2025)', fontsize=14, fontweight='bold')
axes.set_xticks([1, 2, 3, 4])
axes.set_xticklabels(['Q1', 'Q2', 'Q3', 'Q4'])
axes.legend(fontsize=10)
axes.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.show()

# Print summary statistics for reference
print("\nFormaldehyde 2025 - Summary Statistics by Site and Quarter:")
print(formaldehyde_2025[['Site ID', 'Quarter', 'Sample_Average', 'Sample_Max', 'Sample_Count']].to_string(index=False))



#%%
import seaborn as sns

# Filter df for Formaldehyde and year 2025
formaldehyde_2025 = df[(pd.to_datetime(df['Date']).dt.year == 2025) & 
                       (df['Parameter'] == 'Formaldehyde')].copy()

# Make sure we have Year and Quarter columns
formaldehyde_2025['Year'] = pd.to_datetime(formaldehyde_2025['Date']).dt.year
formaldehyde_2025['Quarter'] = pd.to_datetime(formaldehyde_2025['Date']).dt.quarter

# Create a figure
fig, axes = plt.subplots(figsize=(16, 8))

# Create a box plot with Site and Quarter on x-axis, Sample Value on y-axis
sns.boxplot(data=formaldehyde_2025, x='Site ID', y='Sample Value', hue='Quarter', ax=axes)

# Add horizontal dotted line for average MDL
avg_mdl = quarterly_stats[(quarterly_stats['Parameter'] == 'Formaldehyde') & 
                           (quarterly_stats['Year'] == 2025)]['avg_MDL'].mean()
axes.axhline(y=avg_mdl, color='red', linestyle=':', linewidth=2, label=f'Avg MDL: {avg_mdl:.2f}')

# AI Generated block
# Add horizontal line for MAAC value based on units
units = formaldehyde_2025['Units'].iloc[0]
if 'ppb' in units.lower():
    maac_col = 'MAAC ppb'
elif 'ug/m' in units.lower():
    maac_col = 'MAAC ug/m3'
else:
    maac_col = None

if maac_col:
    maac_value = df[df['Parameter'] == 'Formaldehyde'][maac_col].iloc[0]
    axes.axhline(y=maac_value, color='green', linestyle='-', linewidth=2, label=f'MAAC ({units}): {maac_value:.2f}')

axes.set_xlabel('Site ID', fontsize=12, fontweight='bold')
axes.set_ylabel('Sample Value (ppbC)', fontsize=12, fontweight='bold')
axes.set_title('Formaldehyde - Sample Distribution by Site and Quarter (2025)', fontsize=14, fontweight='bold')

# Get existing legend handles and labels to preserve box colors
handles, labels = axes.get_legend_handles_labels()
axes.legend(handles, labels, fontsize=10, loc='best')
axes.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.show()

# Print summary statistics
print("\nFormaldehyde 2025 - Sample count by Site and Quarter:")
print(formaldehyde_2025.groupby(['Site ID', 'Quarter']).size().unstack(fill_value=0))
# %%
import matplotlib.pyplot as plt
import seaborn as sns

# Filter df for Formaldehyde and year 2025
formaldehyde_2025 = df[(pd.to_datetime(df['Date']).dt.year == 2025) & 
                       (df['Parameter'] == 'Formaldehyde')].copy()

# Make sure we have Year and Quarter columns
formaldehyde_2025['Year'] = pd.to_datetime(formaldehyde_2025['Date']).dt.year
formaldehyde_2025['Quarter'] = pd.to_datetime(formaldehyde_2025['Date']).dt.quarter

# Create a figure
fig, axes = plt.subplots(figsize=(16, 8))

# Create a box plot with Site and Quarter on x-axis, Sample Value on y-axis
sns.boxplot(data=formaldehyde_2025, x='Site ID', y='Sample Value', hue='Quarter', ax=axes)

# Overlay individual data points
sns.stripplot(data=formaldehyde_2025, x='Site ID', y='Sample Value', hue='Quarter', 
              dodge=True, alpha=0.5, size=5, ax=axes, legend=False)

# Add horizontal dotted line for average MDL
# TODO: Define avg_MDL for horizontal line to work
# avg_mdl = quarterly_stats[(quarterly_stats['Parameter'] == 'Formaldehyde') & 
#                           (quarterly_stats['Year'] == 2025)]['avg_MDL'].mean()
# axes.axhline(y=avg_mdl, color='red', linestyle=':', linewidth=2, label=f'Avg MDL: {avg_mdl:.2f}')


# Add horizontal line for MAAC value based on units
units = formaldehyde_2025['Units'].iloc[0]
if 'ppb' in units.lower():
    maac_col = 'MAAC ppb'
elif 'ug/m' in units.lower():
    maac_col = 'MAAC ug/m3'
else:
    maac_col = None

if maac_col:
    maac_value = df[df['Parameter'] == 'Formaldehyde'][maac_col].iloc[0]
    axes.axhline(y=maac_value, color='green', linestyle='-', linewidth=2, label=f'MAAC ({units}): {maac_value:.2f}')

axes.set_xlabel('Site ID', fontsize=12, fontweight='bold')
axes.set_ylabel('Sample Value (ppbC)', fontsize=12, fontweight='bold')
axes.set_title('Formaldehyde - Sample Distribution by Site and Quarter (2025)', fontsize=14, fontweight='bold')

# Get existing legend handles and labels to preserve box colors
handles, labels = axes.get_legend_handles_labels()
axes.legend(handles, labels, fontsize=10, loc='best')
axes.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.show()

# Print summary statistics
print("\nFormaldehyde 2025 - Sample count by Site and Quarter:")
print(formaldehyde_2025.groupby(['Site ID', 'Quarter']).size().unstack(fill_value=0))
# %%
