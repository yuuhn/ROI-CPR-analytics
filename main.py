
# coding: utf-8

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import style
plt.style.use('fivethirtyeight')


# # Prepare table for calculations

get_ipython().run_cell_magic('time', '', '\n# Parce sheets\nxl = pd.ExcelFile("raw.xlsx")\ndf_orders = xl.parse(\'Orders\')\ndf_users = xl.parse(\'Users\')\ndf_traffic_date = xl.parse(\'Costs by source\')')
get_ipython().run_cell_magic('time', '', "\n# Merge 2 tables\ndf_users_orders_date = pd.merge(df_users, df_orders, left_on='id', right_on='id_user')")
get_ipython().run_cell_magic('time', '', "\n# Rename columns\ndf_users_orders_date = df_users_orders_date.rename(columns={'id_x':'user_id','id_y':'order_id'})\ndf_users_orders_date = df_users_orders_date.drop(['id_user'], axis=1)")
get_ipython().run_cell_magic('time', '', "\n# Datetime to date\ndf_users_orders_date['user_date'] = df_users_orders_date['date_created'].dt.date      \ndf_users_orders_date['order_date'] = df_users_orders_date['date_order'].dt.date      \ndf_users_orders_date = df_users_orders_date.drop(['date_created', 'date_order'], axis=1)")
get_ipython().run_cell_magic('time', '', "\n# Datetime to date\ndf_traffic_date['traffic_date'] = df_traffic_date['date'].dt.date                     \ndf_traffic_date = df_traffic_date.drop(['date'], axis=1)")
get_ipython().run_cell_magic('time', '', "\n# Merge into one table\ndf_traffic_user_order = pd.merge(df_traffic_date, df_users_orders_date, \n                                 left_on=['source', 'traffic_date'], \n                                 right_on=['source', 'user_date'])")
get_ipython().run_cell_magic('time', '', "\n# Change columns order\ndf_traffic_user_order = df_traffic_user_order[\n    ['source',\n     'traffic_date',\n     'cost',\n     'user_id',\n     'user_date',\n     'order_id',\n     'order_date',\n     'amount'\n    ]]\n\n# Sort\ndf_traffic_user_order = df_traffic_user_order.sort_values(['source', 'traffic_date'])")


# # Calculate CPR for each traffic source

# Count Cost per Registration
df_source_registration = df_traffic_user_order[['source', 'traffic_date', 'cost', 'user_id']].drop_duplicates()

# List of different sources' cpr
list_df_cpr = []
for i in set(df_source_registration['source']):
    list_df_cpr.append(df_source_registration[df_source_registration['source'] == i].reset_index(drop=True))

# Group every source and count regs per day => then divide cost for regs
df_registrations = (df_source_registration.groupby(['source', 'traffic_date'])
    .agg({'cost':'mean', 'user_id':'count'})
    .reset_index()
    .rename(columns={'user_id':'number'}))              

# Make CPR from cost,number of registrations
df_cpr = pd.DataFrame(data={
    'Source':df_registrations['source'],
    'Date':df_registrations['traffic_date'],
    'CPR':df_registrations['cost']/df_registrations['number']})

# List of different sources' cpr
list_df_cpr = []
for i in set(df_cpr['Source']):
    list_df_cpr.append(df_cpr[df_cpr['Source'] == i].reset_index(drop=True))

df_source_cpr = pd.DataFrame()

# All sources in one DataFrame
for source_cpr in list_df_cpr:
    if df_source_cpr.empty:
        df_source_cpr = pd.DataFrame(data={'CPR 1':source_cpr['CPR'], 'Date':source_cpr['Date']})
    else:
        df_source_cpr['CPR ' + str(source_cpr['Source'].iloc[0])] = source_cpr['CPR']

# Set index
df_source_cpr['Date'] = pd.to_datetime(df_source_cpr['Date'])
df_source_cpr = df_source_cpr.set_index('Date')

# Create plot

# CPR for all sources
df_source_cpr.plot()
plt.show()


# # Calculate ROI of groups for each traffic source

def roi(cost, gain):
    return (gain-cost)/cost


# Fill groups of gain, order satisfies
def all_gain_per_order(days_since_reg, gain):
    
    # Gain from order by 4 groups
    # [gain_0, gain_7, gain_30, gain_180]
    order_gain = np.array([0, 0, 0, 0], dtype=float)
    
    if(days_since_reg <= 180):
        order_gain[3] = gain
        if(days_since_reg <= 30):
            order_gain[2] = gain
            if(days_since_reg <= 7):
                order_gain[1] = gain
                if(days_since_reg == 0):
                    order_gain[0] = gain
    
    return order_gain

# Counts roi for each group
def make_roi_row(traffic_source, traffic_date, traffic_cost, traffic_gain):
    
    # Write data into DataFrame
    pd_row = pd.DataFrame(data={
        'source': traffic_source,
        'date': traffic_date, 
        'roi_0': roi(traffic_cost,traffic_gain[0]),
        'roi_7': roi(traffic_cost,traffic_gain[1]),
        'roi_30': roi(traffic_cost,traffic_gain[2]),
        'roi_180': roi(traffic_cost,traffic_gain[3]),
    }, index=[0])
    
    return pd_row


get_ipython().run_cell_magic('time', '', "\n# Empty DataFrame for resulting roi\ndf_roi_day = pd.DataFrame(columns=['source', 'date', 'roi_0', 'roi_7', 'roi_30', 'roi_180'])\n\ntraffic_date = 0\ntraffic_source, traffic_cost = 0, 0\n\n# All gain from traffic by 4 groups\n# [gain_0, gain_7, gain_30, gain_180]\ntraffic_gain = np.array([0, 0, 0, 0], dtype=float)\n\n# Explore all data row by row\nfor row_traffic_order in df_traffic_user_order.iloc[:,:].itertuples():\n    \n    # Whether next day or next source\n    if traffic_date != row_traffic_order[2] or traffic_source != row_traffic_order[1]:\n        \n        # If not first step\n        if traffic_date:\n            \n            # Append to others in DataFrame\n            df_roi_day = df_roi_day.append(\n                make_roi_row(traffic_source, traffic_date, traffic_cost, traffic_gain),\n                ignore_index=True\n            )\n        \n        # Clear array for traffic gain\n        traffic_gain = np.array([0, 0, 0, 0], dtype=float)\n        \n        # Get traffic date\n        traffic_date = row_traffic_order[2]\n        \n        # Get traffic id\n        traffic_source = row_traffic_order[1]\n        \n        # Get traffic cost\n        traffic_cost = row_traffic_order[3]\n   \n    # Days passed since registration\n    days_since_reg = (row_traffic_order[7] - traffic_date).days\n\n    # Gain from order\n    gain = row_traffic_order[8]\n\n    # Add gain from order\n    traffic_gain += all_gain_per_order(days_since_reg, gain)\n    \n# Append to others in DataFrame    \ndf_roi_day = df_roi_day.append(\n    make_roi_row(traffic_source, traffic_date, traffic_cost, traffic_gain),\n    ignore_index=True\n)\n\n# Change columns order\ndf_roi_day = df_roi_day[['source', 'date', 'roi_0', 'roi_7', 'roi_30', 'roi_180']]")


# List of sources' roi
list_of_roi = []
for i in set(df_roi_day['source']):
    list_of_roi.append(df_roi_day[df_roi_day['source'] == i].reset_index(drop=True))

# Set dates for each roi group
df_roi_0 = pd.DataFrame(data={'Date': pd.to_datetime(list_of_roi[0]['date'])})
df_roi_7 = pd.DataFrame(data={'Date': pd.to_datetime(list_of_roi[0]['date'])})
df_roi_30 = pd.DataFrame(data={'Date': pd.to_datetime(list_of_roi[0]['date'])})
df_roi_180 = pd.DataFrame(data={'Date': pd.to_datetime(list_of_roi[0]['date'])})


# Add sources' data into each roi group separately
for df_traffic_roi in list_of_roi:
    df_roi_0['Source ' + str(df_traffic_roi.iloc[0,0])] = df_traffic_roi['roi_0']
    df_roi_7['Source ' + str(df_traffic_roi.iloc[0,0])] = df_traffic_roi['roi_7']
    df_roi_30['Source ' + str(df_traffic_roi.iloc[0,0])] = df_traffic_roi['roi_30']
    df_roi_180['Source ' + str(df_traffic_roi.iloc[0,0])] = df_traffic_roi['roi_180']

# Group by month (optional)
df_roi_0 = df_roi_0.set_index('Date').groupby(pd.TimeGrouper(freq='M')).mean()
df_roi_7 = df_roi_7.set_index('Date').groupby(pd.TimeGrouper(freq='M')).mean()
df_roi_30 = df_roi_30.set_index('Date').groupby(pd.TimeGrouper(freq='M')).mean()
df_roi_180 = df_roi_180.set_index('Date').groupby(pd.TimeGrouper(freq='M')).mean()


# Create plots

# Roi for 0 day
df_roi_0.plot()
plt.show()

# Roi for 7 days
df_roi_7.plot()
plt.show()

# Roi for 30 days
df_roi_30.plot()
plt.show()

# Roi for 180 days
df_roi_180.plot()
plt.show()


# Obviously, 2nd source has best ROI figures
# among all on time span of 0, 7, 30 and 180 days.
# 1st and 3rd sources however differ from month to month,
# none returns investment from all months after half a year YET.
# 3rd source slightly better performs than 1st and both 
# look REALLY PROMISSING to gain above full return of 
# investments in another couple of months. 
