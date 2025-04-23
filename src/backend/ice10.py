import pandas as pd
import matplotlib.pyplot as plt
import mplcursors

# Load datasets
confirmed = pd.read_csv('src/backend/data/time_series_covid19_confirmed_US.csv')
deaths = pd.read_csv('src/backend/data/time_series_covid19_deaths_US.csv')
    
# Drop unnecessary columns
drop_cols = ['UID', 'iso2', 'iso3', 'code3', 'FIPS', 'Admin2', 
             'Country_Region', 'Lat', 'Long_', 'Combined_Key']

confirmed_clean = confirmed.drop(columns=drop_cols, errors='ignore')
deaths_clean = deaths.drop(columns=drop_cols + ['Population'], errors='ignore')

# Melt wide to long format
confirmed_melt = confirmed_clean.melt(id_vars=['Province_State'], var_name='Date', value_name='Confirmed_Cases')
deaths_melt = deaths_clean.melt(id_vars=['Province_State'], var_name='Date', value_name='Deaths')

# Convert Date column
confirmed_melt['Date'] = pd.to_datetime(confirmed_melt['Date'])
deaths_melt['Date'] = pd.to_datetime(deaths_melt['Date'])

# Merge datasets on State and Date
merged_df = pd.merge(confirmed_melt, deaths_melt, on=['Province_State', 'Date'])

# Filter for selected states
states = ['California', 'Florida', 'New York', 'Texas']
plot_df = merged_df[merged_df['Province_State'].isin(states)]

# Plot Scatter Plot
fig, ax = plt.subplots(figsize=(12, 7))

# Define colors for each state
colors = {'California': 'blue', 'Florida': 'green', 'New York': 'red', 'Texas': 'purple'}

# Plot each state's data
for state in states:
    state_data = plot_df[plot_df['Province_State'] == state]
    ax.scatter(state_data['Confirmed_Cases'], state_data['Deaths'], 
               label=state, color=colors[state], alpha=0.6, s=15)

# Set titles and labels
ax.set_title('COVID-19: Confirmed Cases vs Deaths')
ax.set_xlabel('Confirmed Cases')
ax.set_ylabel('Deaths')
ax.legend(title='States')

# Add interactive tooltips
cursor = mplcursors.cursor(ax, hover=True)

@cursor.connect("add")
def on_add(sel):
    state = sel.artist.get_label()
    sel.annotation.set_text(f"{state}\nCases: {int(sel.target[0])}\nDeaths: {int(sel.target[1])}")

# Show plot window (interactive)
plt.show()
