import math
from dataclasses import dataclass

@dataclass
class ProjectInputs:
    # Renewable (Solar)
    solar_capacity_mw: float = 5.0
    solar_capex_per_kw_inr: float = 40000.0
    solar_capacity_factor: float = 0.22
    solar_om_percent: float = 1.5

    # Groundwater treatment (per m3)
    water_energy_kwh_per_m3: float = 0.8
    water_cost_inr_per_m3: float = 15.0
    water_required_m3_per_kg_h2: float = 0.01

    # Electrolyser
    electrolyser_capacity_mw: float = 5.0
    electrolyser_capex_per_kw_inr: float = 55000.0
    electrolyser_om_percent: float = 3.0
    electrolyser_eff_kwh_per_kg: float = 52.0
    electrolyser_degradation_percent_per_year: float = 0.5

    # Ammonia synthesis (Haber-Bosch)
    ammonia_conversion_kgnh3_per_kgh2: float = 1000.0/177.0
    ammonia_capex_total_inr: float = 20_000_000.0
    ammonia_om_percent: float = 4.0

    # Finance
    project_life_years: int = 20
    discount_rate_percent: float = 8.0
    electricity_cost_inr_per_kwh: float = 2.5

    # Currency
    inr_per_usd: float = 83.0

def annuity_factor(r, n):
    if r == 0:
        return 1.0 / n
    return (r * (1 + r)**n) / ((1 + r)**n - 1)

def calculate_project(inputs: ProjectInputs):
    hours_per_year = 8760.0

    # Solar generation per year (kWh)
    solar_capacity_kw = inputs.solar_capacity_mw * 1000.0
    annual_solar_energy_kwh = solar_capacity_kw * hours_per_year * inputs.solar_capacity_factor

    # Electrolyser maximum energy capacity per year (kWh)
    electrolyser_capacity_kw = inputs.electrolyser_capacity_mw * 1000.0
    electrolyser_max_energy_kwh = electrolyser_capacity_kw * hours_per_year

    # Electrolyser actual utilization limited by available RE
    energy_for_electrolysis_kwh = min(annual_solar_energy_kwh, electrolyser_max_energy_kwh)
    electrolyser_actual_cf = energy_for_electrolysis_kwh / electrolyser_max_energy_kwh if electrolyser_max_energy_kwh>0 else 0.0

    # Annual H2 production (kg)
    annual_h2_kg = energy_for_electrolysis_kwh / inputs.electrolyser_eff_kwh_per_kg if inputs.electrolyser_eff_kwh_per_kg>0 else 0.0

    # Annual NH3 production (kg)
    annual_nh3_kg = annual_h2_kg * inputs.ammonia_conversion_kgnh3_per_kgh2

    # CAPEX totals
    solar_capex_inr = inputs.solar_capacity_mw * 1000.0 * inputs.solar_capex_per_kw_inr
    electrolyser_capex_inr = inputs.electrolyser_capacity_mw * 1000.0 * inputs.electrolyser_capex_per_kw_inr
    ammonia_capex_inr = inputs.ammonia_capex_total_inr

    total_capex_inr = solar_capex_inr + electrolyser_capex_inr + ammonia_capex_inr

    # Annualized CAPEX (using annuity factor)
    r = inputs.discount_rate_percent / 100.0
    n = inputs.project_life_years
    ann = annuity_factor(r, n)
    annualized_capex_inr = total_capex_inr * ann

    # Annual OPEX
    solar_om_inr = solar_capex_inr * (inputs.solar_om_percent/100.0)
    electrolyser_om_inr = electrolyser_capex_inr * (inputs.electrolyser_om_percent/100.0)
    ammonia_om_inr = ammonia_capex_inr * (inputs.ammonia_om_percent/100.0)

    # Electricity cost for electrolysis (assuming solar LCOE as electricity cost)
    electricity_cost_inr = energy_for_electrolysis_kwh * inputs.electricity_cost_inr_per_kwh

    # Water cost (treatment + pumping)
    annual_water_m3 = annual_h2_kg * inputs.water_required_m3_per_kg_h2
    water_cost_total_inr = annual_water_m3 * inputs.water_cost_inr_per_m3
    water_energy_cost_inr = annual_water_m3 * inputs.water_energy_kwh_per_m3 * inputs.electricity_cost_inr_per_kwh
    total_water_cost_inr = water_cost_total_inr + water_energy_cost_inr

    # Total annual OPEX
    total_annual_opex_inr = solar_om_inr + electrolyser_om_inr + ammonia_om_inr + electricity_cost_inr + total_water_cost_inr

    # LCOH (₹/kg H2)
    lcoh_inr_per_kg = (annualized_capex_inr + total_annual_opex_inr) / max(annual_h2_kg, 1.0)

    # LCOA (₹/kg NH3)
    annualized_ammonia_capex_inr = ammonia_capex_inr * ann
    ammonia_annual_opex_inr = ammonia_om_inr
    kg_h2_per_kg_nh3 = 1.0 / inputs.ammonia_conversion_kgnh3_per_kgh2
    h2_cost_component_per_kg_nh3 = lcoh_inr_per_kg * kg_h2_per_kg_nh3
    ammonia_component_per_kg_nh3 = (annualized_ammonia_capex_inr + ammonia_annual_opex_inr) / max(annual_nh3_kg, 1.0)
    lcoa_inr_per_kg = h2_cost_component_per_kg_nh3 + ammonia_component_per_kg_nh3

    breakdown = {
        'solar_capex_inr': solar_capex_inr,
        'electrolyser_capex_inr': electrolyser_capex_inr,
        'ammonia_capex_inr': ammonia_capex_inr,
        'total_capex_inr': total_capex_inr,
        'annualized_capex_inr': annualized_capex_inr,
        'solar_om_inr': solar_om_inr,
        'electrolyser_om_inr': electrolyser_om_inr,
        'ammonia_om_inr': ammonia_om_inr,
        'electricity_cost_inr': electricity_cost_inr,
        'total_water_cost_inr': total_water_cost_inr,
        'total_annual_opex_inr': total_annual_opex_inr,
        'annual_h2_kg': annual_h2_kg,
        'annual_nh3_kg': annual_nh3_kg,
        'electrolyser_actual_cf': electrolyser_actual_cf,
        'energy_for_electrolysis_kwh': energy_for_electrolysis_kwh
    }

    usd_per_inr = 1.0 / inputs.inr_per_usd
    lcoh_usd_per_kg = lcoh_inr_per_kg * usd_per_inr
    lcoa_usd_per_kg = lcoa_inr_per_kg * usd_per_inr

    results = {
        'lcoh_inr_per_kg': lcoh_inr_per_kg,
        'lcoh_usd_per_kg': lcoh_usd_per_kg,
        'lcoa_inr_per_kg': lcoa_inr_per_kg,
        'lcoa_usd_per_kg': lcoa_usd_per_kg,
        'breakdown': breakdown
    }

    return results

if __name__ == "__main__":
    defaults = ProjectInputs()
    res = calculate_project(defaults)
    print("LCOH INR/kg:", res['lcoh_inr_per_kg'])
    print("LCOA INR/kg:", res['lcoa_inr_per_kg'])
