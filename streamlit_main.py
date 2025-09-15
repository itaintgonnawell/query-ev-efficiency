from get_eff import get_eff, add_si_eff
from get_spec import add_spec_data
from datetime import datetime
from constants import maker_list, market_class_list, drive_list
import streamlit as st
import pandas as pd

st.title('Electric Vehicle Efficiency Comparison')


# Add dropdown filters for year, make, market class, and drive type
year_options = list(range(2010, datetime.now().year+2))
year1 = st.sidebar.selectbox('Select Start Year', options=year_options, index=len(year_options)-2)
year2 = st.sidebar.selectbox('Select End Year', options=year_options, index=len(year_options)-1)

make = st.sidebar.multiselect('Select Make', options=maker_list, default=["Hyundai", "Kia"])
mclass = st.sidebar.multiselect('Select Market Class', options=market_class_list, default=market_class_list)
drive = st.sidebar.multiselect('Select Drive Type', options=drive_list, default=drive_list)

# add checkbox to include spec data
include_spec = st.sidebar.checkbox('Include Specification Data (may take longer)', value=False)

if st.sidebar.button('Get Data'):
    with st.spinner('Fetching data...'):
        data = get_eff(year1=year1, year2=year2, make=make, mclass=mclass, drive=drive)

        if isinstance(data, dict) and 'error' in data:
            st.error(f"Error: {data['error']}")
        elif isinstance(data, list):
            # add si efficiency data
            data = add_si_eff(data)

            if include_spec:
                spec_data = add_spec_data(data)

                if isinstance(spec_data, dict) and 'error' in spec_data:
                    st.error(f"Error during get specification data: {spec_data['error']}")
                elif isinstance(spec_data, list):
                    data = spec_data

            df = pd.DataFrame(data)

            # remove 'ID' column if exists
            if 'ID' in df.columns:
                df = df.drop(columns=['ID'])

            # reorder columns to have km/kWh at right after config
            cols = df.columns.tolist()
            if 'km/kWh' in cols:
                cols.insert(cols.index('Config') + 1, cols.pop(cols.index('km/kWh')))
                df = df[cols]

            st.dataframe(df)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name='ev_efficiency_data.csv',
                mime='text/csv',
            )

            # Plotting
            if not df.empty:
                st.subheader('Efficiency Comparison (km/kWh)')
                
                # create data for bar chart with Model as index and km/kWh as values and Year as color
                chart_data = df[['Model', 'km/kWh', 'Year']]

                st.bar_chart(chart_data, x='Model', y='km/kWh', color='Year', stack=False, use_container_width=True)
            else:
                st.info("No data available for the selected filters.")

    