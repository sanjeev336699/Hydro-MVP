import streamlit as st
from lcoh import ProjectInputs, calculate_project
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF

st.set_page_config(page_title='HYDRA-Lite v2', layout='wide')
st.title('HYDRA-Lite v2 — Coastal Green Ammonia Hub (MVP)')
st.markdown('Solar → Groundwater Treatment → Electrolyser → Ammonia | Interactive LCOH / LCOA model')

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

col_left, col_right = st.columns([1,2])

with col_left:
    st.subheader('Inputs Summary')
    st.write(f"Solar: {solar_capacity_mw} MW @ CF {solar_cf}")
    st.write(f"Electrolyser: {electrolyser_mw} MW, {electrolyser_eff} kWh/kg H2")
    st.write(f"Water: {water_kwh_m3} kWh/m3, ₹{water_cost_m3}/m3")
    st.write(f"Ammonia CAPEX: ₹{int(ammonia_capex_total):,}")
    if st.button('Run Model'):
        run = True
    else:
        run = False

with col_right:
    st.subheader('Results & Visuals')
    if run:
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

        # Top metrics
        st.metric('LCOH (INR/kg)', f"₹{res['lcoh_inr_per_kg']:.2f}", delta=None)
        st.metric('LCOH (USD/kg)', f"${res['lcoh_usd_per_kg']:.3f}", delta=None)
        st.metric('LCOA (INR/kg NH3)', f"₹{res['lcoa_inr_per_kg']:.2f}", delta=None)
        st.metric('LCOA (USD/kg NH3)', f"${res['lcoa_usd_per_kg']:.3f}", delta=None)

        st.write(f"Annual H2: {br['annual_h2_kg']/1000:.2f} t | Annual NH3: {br['annual_nh3_kg']/1000:.2f} t")

        # Sankey diagram (energy flow)
        energy_for_electrolysis = br['energy_for_electrolysis_kwh']
        total_solar = inputs.solar_capacity_mw*1000*8760*inputs.solar_capacity_factor
        losses = max(total_solar - energy_for_electrolysis, 0)
        labels = ['Total Solar (kWh)', 'To Electrolysis (kWh)', 'Used in H2 (kWh eq)', 'H2 (kg)', 'NH3 (kg)']
        sources = [0,1,2,3]
        targets = [1,2,3,4]
        values = [total_solar, energy_for_electrolysis, br['annual_h2_kg']*inputs.electrolyser_eff_kwh_per_kg if br['annual_h2_kg']>0 else 0, br['annual_h2_kg']]

        sankey = go.Figure(data=[go.Sankey(
            arrangement='snap',
            node=dict(label=labels, pad=15, thickness=20),
            link=dict(source=sources, target=targets, value=values)
        )])
        sankey.update_layout(title_text='Energy & Mass Flow (simplified)', font_size=10, height=350)
        st.plotly_chart(sankey, use_container_width=True)

        # CAPEX Pie
        capex_labels = ['Solar', 'Electrolyser', 'Ammonia']
        capex_values = [br['solar_capex_inr'], br['electrolyser_capex_inr'], br['ammonia_capex_inr']]
        capex_fig = go.Figure(data=[go.Pie(labels=capex_labels, values=capex_values, hole=0.3)])
        capex_fig.update_layout(title_text='CAPEX Split (INR)')

        # OPEX Pie
        opex_labels = ['Solar O&M', 'Electrolyser O&M', 'Ammonia O&M', 'Electricity (Electrolysis)', 'Water Cost']
        opex_values = [br['solar_om_inr'], br['electrolyser_om_inr'], br['ammonia_om_inr'], br['electricity_cost_inr'], br['total_water_cost_inr']]
        opex_fig = go.Figure(data=[go.Pie(labels=opex_labels, values=opex_values, hole=0.3)])
        opex_fig.update_layout(title_text='OPEX Split (INR)')

        # Show CAPEX & OPEX side by side
        c1, c2 = st.columns(2)
        c1.plotly_chart(capex_fig, use_container_width=True)
        c2.plotly_chart(opex_fig, use_container_width=True)

        # Table & CSV download
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
        st.dataframe(df.style.format({'value_inr':'{:,}'}))
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button('Download Cost Breakdown CSV', csv, file_name='cost_breakdown.csv', mime='text/csv')

        # PDF Export
        def create_pdf(res, inputs):
            pdf = FPDF(orientation='P', unit='mm', format='A4')
            pdf.add_page()
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 8, 'HYDRA-Lite v2 Report', ln=1)
            pdf.set_font('Arial', size=10)
            pdf.cell(0, 6, f"Solar: {inputs.solar_capacity_mw} MW | Electrolyser: {inputs.electrolyser_capacity_mw} MW", ln=1)
            pdf.cell(0, 6, f"LCOH: ₹{res['lcoh_inr_per_kg']:.2f} /kg  |  LCOA: ₹{res['lcoa_inr_per_kg']:.2f} /kg", ln=1)
            pdf.ln(4)
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0,6,'Key Annual Outputs', ln=1)
            pdf.set_font('Arial', size=10)
            br = res['breakdown']
            pdf.cell(0,6, f"Annual H2: {br['annual_h2_kg']/1000:.2f} t | Annual NH3: {br['annual_nh3_kg']/1000:.2f} t", ln=1)
            pdf.ln(4)
            pdf.cell(0,6,'CAPEX (INR)', ln=1)
            pdf.cell(0,6, f"Solar: ₹{int(br['solar_capex_inr']):,}", ln=1)
            pdf.cell(0,6, f"Electrolyser: ₹{int(br['electrolyser_capex_inr']):,}", ln=1)
            pdf.cell(0,6, f"Ammonia: ₹{int(br['ammonia_capex_inr']):,}", ln=1)
            pdf.ln(6)
            pdf.cell(0,6,'OPEX (INR / year)', ln=1)
            pdf.cell(0,6, f"Electricity: ₹{int(br['electricity_cost_inr']):,}", ln=1)
            pdf.cell(0,6, f"Total OPEX: ₹{int(br['total_annual_opex_inr']):,}", ln=1)
            return pdf.output(dest='S').encode('latin-1')

        pdf_bytes = create_pdf(res, inputs)
        st.download_button('Download 1-Page PDF Report', data=pdf_bytes, file_name='hydra_report.pdf', mime='application/pdf')
    else:
        st.info('Press Run Model in left column to compute results and view visuals.')

