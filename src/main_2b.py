##########################
# Question 2b
##########################


import numpy as np
import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import matplotlib.pyplot as plt

from data_ops.data_loader import DataLoader
from opt_model.opt_model_2 import OptModel2b, InputData2b


data = DataLoader('.')

app_data2b = data._load_data_file('data/question_1c', 'appliance_params.json')
bus_data2b = data._load_data_file('data/question_1c', 'bus_params.json')
con_data2b = data._load_data_file('data/question_1c', 'consumer_params.json')
DER_data2b = data._load_data_file('data/question_1c', 'DER_production.json')
usa_data2b = data._load_data_file('data/question_1c', 'usage_preferences.json') 

variables2b = ['P_PV', 'P_imp', 'P_exp', 'P_bat_ch', 'P_bat_dis', 'SOC']
el_prices2b = bus_data2b[0]['energy_price_DKK_per_kWh']
imp_tariff2b = bus_data2b[0]['import_tariff_DKK/kWh']
exp_tariff2b = bus_data2b[0]['export_tariff_DKK/kWh']
upper_power_PV_rhs2b = np.array(DER_data2b[0]['hourly_profile_ratio']) * app_data2b['DER'][0]['max_power_kW']
upper_power_PV_rhs2b = upper_power_PV_rhs2b.tolist()
upper_power_rhs2b = [bus_data2b[0]['max_import_kW'], bus_data2b[0]['max_export_kW']]
hourly_balance_rhs2b = np.array(usa_data2b[0]['load_preferences'][0]['hourly_profile_ratio']) * app_data2b['load'][0]['max_load_kWh_per_hour']
hourly_balance_rhs2b = hourly_balance_rhs2b.tolist()
hourly_balance_sense2b = [GRB.EQUAL]
eta_ch = app_data2b['storage'][0]['charging_efficiency']
eta_dis = app_data2b['storage'][0]['discharging_efficiency']
battery_intial_soc = usa_data2b[0]['storage_preferences'][0]['initial_soc_ratio']  # 50% of capacity
battery_min_soc = 0.1   # 10% of capacity
max_charge = app_data2b['storage'][0]['max_charging_power_ratio'] # 0.5C rate
max_discharge = app_data2b['storage'][0]['max_discharging_power_ratio'] # 0.5C rate
lifetime = 10 * 365.25
capex = 300 # Subject to change




input_data2b = InputData2b(variables2b, 
                       el_prices2b, 
                       imp_tariff2b,
                       exp_tariff2b, 
                       upper_power_PV_rhs2b, 
                       upper_power_rhs2b, 
                       hourly_balance_rhs2b, 
                       hourly_balance_sense2b,
                       eta_ch,
                       eta_dis,
                       battery_intial_soc,
                       battery_min_soc,
                       max_charge,
                       max_discharge,
                       lifetime,
                       capex
                       )
model2b = OptModel2b(input_data2b, 'Question 2b Model')
model2b.run()
model2b.display_results()


# EXPERIMENT SETUP FOR CAPEX
experiment_capex = {
    'base': capex, 
    'high capex': capex * 10, 
    'low capex': capex * 0.5
}


# SCENARIO ANALYSIS FOR LOAD
experiment_results_capex = {}

for exp_name, exp_capex in experiment_capex.items():
    print(f"Running experiment: {exp_name}")
    input_data2b = InputData2b(
        variables2b, 
        el_prices2b, 
        imp_tariff2b,
        exp_tariff2b, 
        upper_power_PV_rhs2b, 
        upper_power_rhs2b, 
        hourly_balance_rhs2b, 
        hourly_balance_sense2b,
        eta_ch,
        eta_dis,
        battery_intial_soc,
        battery_min_soc,
        max_charge,
        max_discharge,
        lifetime,
        exp_capex
    )
    model2b = OptModel2b(input_data2b, f'Question 2b Model {exp_name}')
    model2b.run()
    model2b.display_results()
    # Store results
    experiment_results_capex[exp_name] = {
        "objective": model2b.results.obj_val,
        "var_vals": model2b.results.var_vals,
        "dual_vals": model2b.results.dual_vals,
        "load_profile": hourly_balance_rhs2b
    }

# Plotting the result for the 

for exp_name, results in experiment_results_capex.items():
    hours = range(len(results['load_profile']))
    
    load = results['load_profile']
    P_imp = [results['var_vals'][('P_imp', t)] for t in hours]
    P_exp = -np.array([results['var_vals'][('P_exp', t)] for t in hours])
    P_pv  = [results['var_vals'][('P_PV', t)] for t in hours]
    P_charge = [results['var_vals'][('P_bat_ch', t)] for t in hours]
    P_discharge = -np.array([results['var_vals'][('P_bat_dis', t)] for t in hours])
    SOC = [results['var_vals'][('SOC', t)] for t in hours]
    prices = el_prices2b

    plt.figure(figsize=(15, 10))
    plt.suptitle(f'Scenario: {exp_name}', fontsize=16)

    # 1. Hourly Load and PV Production
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

    # 2. Prices and Power Import & Export
    ax1 = plt.subplot(3, 1, 2)  # Primary axis
    ax1.bar(hours, P_imp, width=0.95, label='Power Import [kW]', alpha=0.9, align='edge', color='skyblue')
    ax1.bar(hours, P_exp, width=0.95, label='Power Export [kW]', alpha=0.9, align='edge', color='grey')
    ax1.set_xlabel('Hour')
    ax1.set_ylabel('Power [kW]')
    ax1.set_title('Power Import, Export & Prices Over 24 Hours')
    ax1.set_xlim(0, 24)
    ax1.grid()

    # Create secondary y-axis for prices
    prices_step = list(prices) + [prices[-1]]
    ax2 = ax1.twinx()
    ax2.step(hours_step, prices_step, label='Electricity Prices [DKK/kWh]', color='green', linewidth=2)
    ax2.set_ylabel('Electricity Price [DKK/kWh]')
    ax2.set_xlim(0, 24)

    # Combine legends from both axes
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(handles1 + handles2, labels1 + labels2)


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
    plt.legend(loc = 'upper right')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

exp_names = list(experiment_results_capex.keys())
costs = [experiment_results_capex[exp]['objective'] for exp in exp_names]

plt.figure(figsize=(8, 5))
plt.bar(exp_names, costs, color='steelblue')
plt.ylabel('Profit (DKK)')
plt.title('Profit over 10 years')
plt.grid(axis='y', alpha=0.3)
plt.show()


# EXPERIMENT SETUP FOR COST STRUCTURE
experiment_cost = {
    'base': el_prices2b,
    'fixed': [np.mean(el_prices2b)] * len(el_prices2b),
    'no_day_tariff': [price - imp_tariff2b if 7 <= i <= 22 else price
                  for i, price in enumerate(el_prices2b)],
    'no_night_tariff': [price - imp_tariff2b if i < 7 or i > 22 else price
                  for i, price in enumerate(el_prices2b)],
}

# # SCENARIO ANALYSIS FOR COST STRUCTURE
experiment_results_cost = {}

for exp_name, exp_prices in experiment_cost.items():
    print(f"Running experiment: {exp_name}")
    input_data2b = InputData2b(
        variables2b, 
        exp_prices, 
        imp_tariff2b,
        exp_tariff2b, 
        upper_power_PV_rhs2b, 
        upper_power_rhs2b, 
        hourly_balance_rhs2b, 
        hourly_balance_sense2b,
        eta_ch,
        eta_dis,
        battery_intial_soc,
        battery_min_soc,
        max_charge,
        max_discharge,
        lifetime,
        capex
    )
    model2b = OptModel2b(input_data2b, f'Question 1c Model {exp_name}')
    model2b.run()
    model2b.display_results()
    # Store results
    experiment_results_cost[exp_name] = {
        "objective": model2b.results.obj_val,
        "var_vals": model2b.results.var_vals,
        "dual_vals": model2b.results.dual_vals,
        "prices": exp_prices
    }


for exp_name, results in experiment_results_cost.items():
    hours = range(len(results['prices']))
    
    load = hourly_balance_rhs2b
    P_imp = [results['var_vals'][('P_imp', t)] for t in hours]
    P_exp = -np.array([results['var_vals'][('P_exp', t)] for t in hours])
    P_pv  = [results['var_vals'][('P_PV', t)] for t in hours]
    P_charge = [results['var_vals'][('P_bat_ch', t)] for t in hours]
    P_discharge = -np.array([results['var_vals'][('P_bat_dis', t)] for t in hours])
    SOC = [results['var_vals'][('SOC', t)] for t in hours]
    prices = results['prices']
    

    plt.figure(figsize=(15, 10))
    plt.suptitle(f'Scenario: {exp_name}', fontsize=16)

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

    # 2. Prices and Power Import & Export
    ax1 = plt.subplot(3, 1, 2)  # Primary axis
    ax1.bar(hours, P_imp, width=0.95, label='Power Import (kW)', alpha=0.9, align='edge', color='skyblue')
    ax1.bar(hours, P_exp, width=0.95, label='Power Export (kW)', alpha=0.9, align='edge', color='grey')
    ax1.set_xlabel('Hour')
    ax1.set_ylabel('Power [kW]')
    ax1.set_title('Power Import, Export & Prices Over 24 Hours')
    ax1.set_xlim(0, 24)
    ax1.grid()

    # Create secondary y-axis for prices
    ax2 = ax1.twinx()
    prices_step = list(prices) + [prices[-1]]
    ax2.step(hours_step, prices_step, label='Electricity Prices [DKK/kWh]', color='green', linewidth=2)
    ax2.set_ylabel('Electricity Price [DKK/kWh]')
    ax2.set_xlim(0, 24)
    # Combine legends from both axes
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(handles1 + handles2, labels1 + labels2, loc='upper right')


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

exp_names = list(experiment_results_cost.keys())
costs = [experiment_results_cost[exp]['objective'] for exp in exp_names]

plt.figure(figsize=(8, 5))
plt.bar(exp_names, costs, color = 'steelblue')
plt.ylabel('Profit (DKK)')
plt.title('Profit over 10 years (DKK)')
plt.grid(axis='y', alpha=0.3)
plt.show()




#EXPERIMENT SETUP FOR LOAD
experiment_load = {
    'base': hourly_balance_rhs2b, 
    'high': [1.2 * val for val in hourly_balance_rhs2b], 
    'low': [0.8 * val for val in hourly_balance_rhs2b],
    'fixed': [np.mean(hourly_balance_rhs2b)] * len(hourly_balance_rhs2b)
}

# SCENARIO ANALYSIS FOR LOAD
experiment_results_load = {}

for exp_name, exp_rhs in experiment_load.items():
    print(f"Running experiment: {exp_name}")
    input_data1c = InputData2b(
        variables2b, 
        el_prices2b, 
        imp_tariff2b,
        exp_tariff2b, 
        upper_power_PV_rhs2b, 
        upper_power_rhs2b, 
        exp_rhs, 
        hourly_balance_sense2b,
        eta_ch,
        eta_dis,
        battery_intial_soc,
        battery_min_soc,
        max_charge,
        max_discharge,
        lifetime,
        capex
    )
    model2b = OptModel2b(input_data1c, f'Question 2b Model {exp_name}')
    model2b.run()
    model2b.display_results()
    # Store results
    experiment_results_load[exp_name] = {
        "objective": model2b.results.obj_val,
        "var_vals": model2b.results.var_vals,
        "dual_vals": model2b.results.dual_vals,
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
    prices = el_prices2b
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

    # 2. Prices and Power Import & Export
    ax1 = plt.subplot(3, 1, 2)  # Primary axis
    ax1.bar(hours, P_imp, width=0.95, label='Power Import [kW]', alpha=0.9, align='edge', color='skyblue')
    ax1.bar(hours, P_exp, width=0.95, label='Power Export [kW]', alpha=0.9, align='edge', color='grey')
    ax1.set_xlabel('Hour')
    ax1.set_ylabel('Power [kW]')
    ax1.set_title('Power Import, Export & Prices Over 24 Hours')
    ax1.grid()
    ax1.set_xlim(0, 24)

    # Create secondary y-axis for prices
    ax2 = ax1.twinx()
    prices_step = list(prices) + [prices[-1]]
    ax2.step(hours_step, prices_step, label='Electricity Prices [DKK/kWh]', color='green', linewidth=2)
    ax2.set_ylabel('Electricity Price [DKK/kWh]')

    # Combine legends from both axes
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(handles1 + handles2, labels1 + labels2)
    ax2.set_xlim(0, 24)


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

plt.figure(figsize=(8, 5))
plt.bar(exp_names, costs, color='steelblue')
plt.ylabel('Profit Cost (DKK)')
plt.title('Profit by Different Load Profiles')
plt.grid(axis='y', alpha=0.3)
plt.show()
