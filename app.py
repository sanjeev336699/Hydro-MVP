import streamlit as st
from lcoh import ProjectInputs, calculate_project
import pandas as pd

st.set_page_config(page_title='HYDRA-Lite MVP', layout='wide')
st.title('HYDRA-Lite: Coastal Green Ammonia Hub (MVP)')
st.write('Model: Solar → Groundwater Treatment → Electrolyser → Ammonia Synth. Edit inputs and run.')

# Sidebar inputs
st.sidebar.header('Renewable (Solar)')
solar_capacity_mw = st.sidebar.number_input('Solar capacity (MW)', value=5.0, step=1.0)
solar_cf = st.sidebar.number_input('Solar capacity factor (fraction)', value=0.22, format="%.2f")
solar_capex = st.sidebar.number_input('Solar CAPEX (₹/kW)', value=40000.0, step=1000.0)
solar_om = st.sidebar.number_input('Solar O&M (% of CAPEX/yr)', value=1.5, format="%.2f")

st.sidebar.header('Electrolyser')
electrolyser_mw = st.sidebar.number_input('Electrolyser capacity (MW)', value=5.0, step=1.0)
electrolyser_eff = st.sidebar.number_input('Electrolyser efficiency (kWh/kg H2)', value=52.0, format="%.2f")
electrolyser_capex = st.sidebar.number_input('Electrolyser CAPEX (₹/kW)', value=55000.0, step=1000.0)
electrolyser_om = st.sidebar.number_input('Electrolyser O&M (% of CAPEX/yr)', value=3.0, format="%.2f")

st.sidebar.header('Water (Groundwater Treatment)')
water_kwh_m3 = st.sidebar.number_input('Water energy (kWh/m3)', value=0.8, format="%.2f")
water_cost_m3 = st.sidebar.number_input('Water OPEX (₹/m3)', value=15.0, format="%.2f")
water_m3_per_kg = st.sidebar.number_input('Water required (m3/kg H2)', value=0.01, format="%.3f")

st.sidebar.header('Ammonia Synthesis')
ammonia_capex_total = st.sidebar.number_input('Ammonia plant CAPEX (₹ total)', value=20000000.0, step=1000000.0)
ammonia_om = st.sidebar.number_input('Ammonia O&M (% of CAPEX/yr)', value=4.0, format="%.2f")

st.sidebar.header('Finance & Currency')
discount_rate = st.sidebar.number_input('Discount rate (%)', value=8.0, format="%.2f")
project_life = st.sidebar.number_input('Project life (years)', value=20, step=1)
elec_cost = st.sidebar.number_input('Electricity cost (₹/kWh)', value=2.5, format="%.2f")
inr_per_usd = st.sidebar.number_input('INR per USD', value=83.0, format="%.2f")

if st.sidebar.button('Run Model'):
    inputs = ProjectInputs(
        solar_capacity_mw=solar_capacity_mw,
        solar_capex_per_kw_inr=solar_capex,
        solar_capacity_factor=solar_cf,
        solar_om_percent=solar_om,
        water_energy_kwh_per_m3=water_kwh_m3,
        water_cost_inr_per_m3=water_cost_m3,
        water_required_m3_per_kg_h2=water_m3_per_kg,
        electrolyser_capacity_mw=electrolyser_mw,
        electrolyser_capex_per_kw_inr=electrolyser_capex,
        electrolyser_om_percent=electrolyser_om,
        electrolyser_eff_kwh_per_kg=electrolyser_eff,
        ammonia_capex_total_inr=ammonia_capex_total,
        ammonia_om_percent=ammonia_om,
        project_life_years=int(project_life),
        discount_rate_percent=discount_rate,
        electricity_cost_inr_per_kwh=elec_cost,
        inr_per_usd=inr_per_usd
    )
    res = calculate_project(inputs)
    br = res['breakdown']

    st.subheader('Key Results')
    col1, col2 = st.columns(2)
    col1.metric('LCOH (INR/kg)', f"₹{res['lcoh_inr_per_kg']:.2f}")
    col1.metric('LCOH (USD/kg)', f"${res['lcoh_usd_per_kg']:.3f}")
    col2.metric('LCOA (INR/kg NH3)', f"₹{res['lcoa_inr_per_kg']:.2f}")
    col2.metric('LCOA (USD/kg NH3)', f"${res['lcoa_usd_per_kg']:.3f}")

    st.subheader('Annual Production')
    st.write(f"Annual H2: {br['annual_h2_kg'] / 1000:.2f} tonnes")
    st.write(f"Annual NH3: {br['annual_nh3_kg'] / 1000:.2f} tonnes")

    st.subheader('Cost Breakdown (INR)')
    df = pd.DataFrame({
        'item': [
            'Solar CAPEX', 'Electrolyser CAPEX', 'Ammonia CAPEX', 'Annualized CAPEX',
            'Solar O&M', 'Electrolyser O&M', 'Ammonia O&M', 'Electricity Cost (Electrolysis)', 'Water Cost (Total)', 'Total OPEX'
        ],
        'value_inr': [
            br['solar_capex_inr'], br['electrolyser_capex_inr'], br['ammonia_capex_inr'], br['annualized_capex_inr'],
            br['solar_om_inr'], br['electrolyser_om_inr'], br['ammonia_om_inr'], br['electricity_cost_inr'], br['total_water_cost_inr'], br['total_annual_opex_inr']
        ]
    })
    st.table(df)

    # Download CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button('Download Cost Breakdown CSV', csv, file_name='cost_breakdown.csv', mime='text/csv')

    st.info('To export a PDF report or deploy publicly, follow README instructions.')
else:
    st.info('Adjust inputs in the sidebar and click "Run Model" to compute LCOH & LCOA.')
