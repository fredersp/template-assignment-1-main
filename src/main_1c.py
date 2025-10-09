##########################
# Question 1c
##########################

import numpy as np
from gurobipy import GRB
import matplotlib.pyplot as plt


from data_ops.data_loader import DataLoader
from opt_model.opt_model import OptModel1c, InputData1c


data = DataLoader('..')

app_data1c = data._load_data_file('data/question_1c', 'appliance_params.json')
bus_data1c = data._load_data_file('data/question_1c', 'bus_params.json')
con_data1c = data._load_data_file('data/question_1c', 'consumer_params.json')
DER_data1c = data._load_data_file('data/question_1c', 'DER_production.json')
usa_data1c = data._load_data_file('data/question_1c', 'usage_preferences.json') 

variables1c = ['P_PV', 'P_imp', 'P_exp', 'P_bat_ch', 'P_bat_dis', 'SOC']
el_prices1c = bus_data1c[0]['energy_price_DKK_per_kWh']
imp_tariff1c = bus_data1c[0]['import_tariff_DKK/kWh']
upper_power_PV_rhs1c = np.array(DER_data1c[0]['hourly_profile_ratio']) * app_data1c['DER'][0]['max_power_kW']
upper_power_PV_rhs1c = upper_power_PV_rhs1c.tolist()
upper_power_rhs1c = [bus_data1c[0]['max_import_kW'], bus_data1c[0]['max_export_kW']]
hourly_balance_rhs1c = np.array(usa_data1c[0]['load_preferences'][0]['hourly_profile_ratio']) * app_data1c['load'][0]['max_load_kWh_per_hour']
hourly_balance_rhs1c = hourly_balance_rhs1c.tolist()
hourly_balance_sense1c = [GRB.EQUAL]
battery_capacity = app_data1c['storage'][0]['storage_capacity_kWh']
eta_ch = app_data1c['storage'][0]['charging_efficiency']
eta_dis = app_data1c['storage'][0]['discharging_efficiency']
battery_intial_soc = usa_data1c[0]['storage_preferences'][0]['initial_soc_ratio'] * battery_capacity  # 50% of capacity
battery_min_soc = 0.1 * battery_capacity  # 10% of capacity
max_charge = app_data1c['storage'][0]['max_charging_power_ratio'] * battery_capacity  # 0.5C rate
max_discharge = app_data1c['storage'][0]['max_discharging_power_ratio'] * battery_capacity  # 0.5C rate




input_data1c = InputData1c(variables1c, 
                       el_prices1c, 
                       imp_tariff1c, 
                       upper_power_PV_rhs1c, 
                       upper_power_rhs1c, 
                       hourly_balance_rhs1c, 
                       hourly_balance_sense1c,
                       battery_capacity,
                       eta_ch,
                       eta_dis,
                       battery_intial_soc,
                       battery_min_soc,
                       max_charge,
                       max_discharge)
model1c = OptModel1c(input_data1c, 'Question 1c Model')
model1c.run()
model1c.display_results()

# EXPERIMENT SETUP FOR LOAD
experiment_load = {
    'base': hourly_balance_rhs1c, 
    'high': [1.2 * val for val in hourly_balance_rhs1c], 
    'low': [0.8 * val for val in hourly_balance_rhs1c],
    'fixed': [np.mean(hourly_balance_rhs1c)] * len(hourly_balance_rhs1c)
}

# SCENARIO ANALYSIS FOR LOAD
experiment_results_load = {}

for exp_name, exp_rhs in experiment_load.items():
    print(f"Running experiment: {exp_name}")
    input_data1c = InputData1c(
        variables1c, 
        el_prices1c, 
        imp_tariff1c, 
        upper_power_PV_rhs1c, 
        upper_power_rhs1c, 
        exp_rhs, 
        hourly_balance_sense1c,
        battery_capacity,
        eta_ch,
        eta_dis,
        battery_intial_soc,
        battery_min_soc,
        max_charge,
        max_discharge
    )
    model1c = OptModel1c(input_data1c, f'Question 1c Model {exp_name}')
    model1c.run()
    model1c.display_results()
    # Store results
    experiment_results_load[exp_name] = {
        "objective": model1c.results.obj_val,
        "var_vals": model1c.results.var_vals,
        "dual_vals": model1c.results.dual_vals,
        "load_profile": exp_rhs
    }

# Plotting the result for the 

for exp_name, results in experiment_results_load.items():
    hours = range(len(results['load_profile']))
    
    load = results['load_profile']
    P_imp = [results['var_vals'][('P_imp', t)] for t in hours]
    P_exp = -np.array([results['var_vals'][('P_exp', t)] for t in hours])
    P_pv  = [results['var_vals'][('P_PV', t)] for t in hours]
    P_charge = [results['var_vals'][('P_bat_ch', t)] for t in hours]
    P_discharge = -np.array([results['var_vals'][('P_bat_dis', t)] for t in hours])
    SOC = [results['var_vals'][('SOC', t)] for t in hours]
    prices = el_prices1c
    #cost = results['objective']

    plt.figure(figsize=(15, 10))
    plt.suptitle(f'Experiment: {exp_name}', fontsize=16)

    # 1. Electricity Price + PV Production (shared plot)
    plt.subplot(3, 1, 1)
    hours_step = list(hours) + [hours[-1] + 1] 
    load_step = list(load) + [load[-1]]
    plt.step(hours_step, load_step, label='Hourly Load Profile [kW]', linewidth=2 , where='post', color='blue')
    plt.bar(hours, P_pv, color = 'orange', width=0.95, label='PV Production [kW]', alpha=0.9, align='edge')
    plt.xlabel('Hour')
    plt.ylabel('Power [kW]')
    plt.title('Hourly Load Profile and PV Production')
    plt.xlim(0,24)
    plt.grid()
    plt.legend()

    # 2. Power Import & Export
    plt.subplot(3, 1, 2)
    prices_step = list(prices) + [prices[-1]]
    plt.step(hours_step, prices_step, color = 'green', label = 'Electricity Prices [DKK/kWh]', where='post')
    plt.bar(hours, P_imp, width=0.95, label='Power Import [kW]', alpha=0.9, align='edge', color='skyblue')
    plt.bar(hours, P_exp, width=0.95, label='Power Export [kW]', alpha=0.9, align='edge', color='grey')
    plt.xlabel('Hour')
    plt.ylabel('Power [kW] / Price [DKK/kWh]')
    plt.title('Power Import and Export Over 24 Hours')
    plt.xlim(0,24)
    plt.grid()
    plt.legend()

    # 3. Battery SOC, charging and discharging
    plt.subplot(3, 1, 3)
    SOC_step = list(SOC) + [SOC[-1]]
    plt.step(hours_step, SOC_step, color = 'black', label = 'Battery State of Charge [kWh]', where='post')
    plt.bar(hours, P_charge, color = 'darkgreen', width=0.95, label='Battery Charging [kW]', alpha=0.9, align='edge')
    plt.bar(hours, P_discharge, color = 'darkred', width=0.95, label='Battery Discharging [kW]', alpha=0.9, align='edge')
    plt.xlabel('Hour')
    plt.ylabel('Energy [kWh] / Power [kW]')
    plt.title('SOC, Charging and Discharging Over 24 Hours')
    plt.xlim(0,24)
    plt.grid()
    plt.legend()

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

exp_names = list(experiment_results_load.keys())
costs = [experiment_results_load[exp]['objective'] for exp in exp_names]

"""
plt.figure(figsize=(8, 5))
plt.bar(exp_names, costs, color='steelblue')
plt.ylabel('Procurement Cost (DKK)')
plt.title('Procurement Cost by Different Load Profiles')
plt.grid(axis='y', alpha=0.3)
plt.show()
"""



# EXPERIMENT SETUP FOR COST STRUCTURE
experiment_cost = {
    'base': el_prices1c,
    'fixed': [np.mean(el_prices1c)] * len(el_prices1c),
    'no_day_tariff': [price - imp_tariff1c if 7 <= i <= 22 else price
                  for i, price in enumerate(el_prices1c)],
    'no_night_tariff': [price - imp_tariff1c if i < 7 or i > 22 else price
                  for i, price in enumerate(el_prices1c)],
}

# # SCENARIO ANALYSIS FOR COST STRUCTURE
experiment_results_cost = {}

for exp_name, exp_prices in experiment_cost.items():
    print(f"Running experiment: {exp_name}")
    input_data1c = InputData1c(
        variables1c, 
        exp_prices, 
        imp_tariff1c, 
        upper_power_PV_rhs1c, 
        upper_power_rhs1c, 
        hourly_balance_rhs1c, 
        hourly_balance_sense1c,
        battery_capacity,
        eta_ch,
        eta_dis,
        battery_intial_soc,
        battery_min_soc,
        max_charge,
        max_discharge
    )
    model1c = OptModel1c(input_data1c, f'Question 1c Model {exp_name}')
    model1c.run()
    model1c.display_results()
    # Store results
    experiment_results_cost[exp_name] = {
        "objective": model1c.results.obj_val,
        "var_vals": model1c.results.var_vals,
        "dual_vals": model1c.results.dual_vals,
        "prices": exp_prices
    }


for exp_name, results in experiment_results_cost.items():
    hours = range(len(results['prices']))
    
    load = hourly_balance_rhs1c
    P_imp = [results['var_vals'][('P_imp', t)] for t in hours]
    P_exp = -np.array([results['var_vals'][('P_exp', t)] for t in hours])
    P_pv  = [results['var_vals'][('P_PV', t)] for t in hours]
    P_charge = [results['var_vals'][('P_bat_ch', t)] for t in hours]
    P_discharge = -np.array([results['var_vals'][('P_bat_dis', t)] for t in hours])
    SOC = [results['var_vals'][('SOC', t)] for t in hours]
    prices = results['prices']
    

    plt.figure(figsize=(15, 10))
    plt.suptitle(f'Experiment: {exp_name}', fontsize=16)

    # 1. Electricity Price + PV Production (shared plot)
    plt.subplot(3, 1, 1)
    hours_step = list(hours) + [hours[-1] + 1]
    load_step = list(load) + [load[-1]]
    plt.step(hours_step, load_step, label='Hourly Load Profile [kW]', linewidth=2, where='post', color='blue')
    plt.bar(hours, P_pv, color = 'orange', width=0.95, label='PV Production [kW]', alpha=0.9, align='edge')
    plt.xlabel('Hour')
    plt.ylabel('Power [kW]')
    plt.title('Hourly Load Profile and PV Production')
    plt.xlim(0,24)
    plt.grid()
    plt.legend()

    # 2. Power Import & Export
    plt.subplot(3, 1, 2)
    prices_step = list(prices) + [prices[-1]]
    plt.step(hours_step, prices_step, color = 'green', label = 'Electricity Prices [DKK/kWh]', linewidth=2, where='post')
    plt.bar(hours, P_imp, width=0.95, label='Power Import [kW]', alpha=0.9, color='skyblue', align='edge')
    plt.bar(hours, P_exp, width=0.95, label='Power Export (kW)', alpha=0.9, color='grey', align='edge')
    plt.xlabel('Hour')
    plt.ylabel('Power [kW] / Price [DKK/kWh]')
    plt.title('Power Import and Export Over 24 Hours')
    plt.xlim(0, 24)
    plt.grid()
    plt.legend()

    # 3. Battery SOC, charging and discharging
    plt.subplot(3, 1, 3)
    SOC_step = list(SOC) + [SOC[-1]]
    plt.step(hours_step, SOC_step, color = 'black', label = 'Battery State of Charge [kWh]', where='post')
    plt.bar(hours, P_charge, color = 'darkgreen', width=0.95, label='Battery Charging [kW]', alpha=0.9, align='edge')
    plt.bar(hours, P_discharge, color = 'darkred', width=0.95, label='Battery Discharging [kW]', alpha=0.9, align='edge')
    plt.xlabel('Hour')
    plt.ylabel('Energy [kWh] / Power [kW]')
    plt.title('SOC, Charging and Discharging Over 24 Hours')
    plt.xlim(0, 24)
    plt.grid()
    plt.legend()

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

exp_names = list(experiment_results_cost.keys())
costs = [experiment_results_cost[exp]['objective'] for exp in exp_names]

plt.figure(figsize=(8, 5))
plt.bar(exp_names, costs, color = 'steelblue')
plt.ylabel('Procurement Cost (DKK)')
plt.title('Procurement Cost by Different Cost Structures')
plt.grid(axis='y', alpha=0.3)
plt.show()
