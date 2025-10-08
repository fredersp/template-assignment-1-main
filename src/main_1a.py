
import numpy as np
import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from data_ops.data_loader import DataLoader
from opt_model.opt_model import OptModel1a, InputData1a, OptModel1b, InputData1b


data = DataLoader('.')

#########################
# Question 1a
#########################

app_data1a = data._load_data_file('data/question_1a', 'appliance_params.json')
bus_data1a = data._load_data_file('data/question_1a', 'bus_params.json')
con_data1a = data._load_data_file('data/question_1a', 'consumer_params.json')
DER_data1a = data._load_data_file('data/question_1a', 'DER_production.json')
usa_data1a = data._load_data_file('data/question_1a', 'usage_preference.json')

variables1a = ['P_PV', 'P_imp', 'P_exp']
el_prices1a = bus_data1a[0]['energy_price_DKK_per_kWh']
imp_tariff1a = bus_data1a[0]['import_tariff_DKK/kWh']
upper_power_PV_rhs1a = np.array(DER_data1a[0]['hourly_profile_ratio']) * app_data1a['DER'][0]['max_power_kW']
upper_power_PV_rhs1a = upper_power_PV_rhs1a.tolist()
upper_power_rhs1a = [bus_data1a[0]['max_import_kW'], bus_data1a[0]['max_export_kW']]
hourly_balance_rhs1a = [app_data1a['load'][0]['max_load_kWh_per_hour'], 0]
hourly_balance_sense1a = [GRB.LESS_EQUAL, GRB.GREATER_EQUAL]
daily_balance_rhs1a = usa_data1a[0]['load_preferences'][0]['min_total_energy_per_day_hour_equivalent'] * app_data1a['load'][0]['max_load_kWh_per_hour'] 

input_data1a = InputData1a(variables1a, 
                       el_prices1a, 
                       imp_tariff1a, 
                       upper_power_PV_rhs1a, 
                       upper_power_rhs1a, 
                       hourly_balance_rhs1a, 
                       hourly_balance_sense1a,
                       daily_balance_rhs1a)


model1a = OptModel1a(input_data1a, 'Question 1a Model')
model1a.run()
model1a.display_results()

### SCENARIO/SENSITIVITY ANALYSIS
# Creating experiments with different cost structure scenarios

experiment = {
    'base': el_prices1a,
    'fixed': [np.mean(el_prices1a)] * len(el_prices1a),
    'no_day_tariff': [price - imp_tariff1a if 7 <= i <= 22 else price
                  for i, price in enumerate(el_prices1a)],
    'no_night_tariff': [price - imp_tariff1a if i < 7 or i > 22 else price
                  for i, price in enumerate(el_prices1a)],
}

experiment_results = {}
for exp_name, exp_prices in experiment.items():
    print(f"Running experiment: {exp_name}")
    input_data1a = InputData1a(variables1a, 
                       exp_prices, 
                       imp_tariff1a, 
                       upper_power_PV_rhs1a, 
                       upper_power_rhs1a, 
                       hourly_balance_rhs1a, 
                       hourly_balance_sense1a,
                       daily_balance_rhs1a)
    model1a = OptModel1a(input_data1a, f'Experiment: {exp_name}')
    model1a.run()
    model1a.display_results()

    experiment_results[exp_name] = {
        "objective": model1a.results.obj_val,
        "var_vals": model1a.results.var_vals,
        "dual_vals": model1a.results.dual_vals,
        "cost_structure": exp_prices
    }

#########################
# plot the electricity prices, power import/export, and PV production for each experiment

for exp_name, results in experiment_results.items():
    hours = range(len(results['cost_structure']))
    
    prices = results['cost_structure']
    P_imp = [results['var_vals'][('P_imp', t)] for t in hours]
    P_exp = [results['var_vals'][('P_exp', t)] for t in hours]
    P_pv  = [results['var_vals'][('P_PV', t)] for t in hours]

    plt.figure(figsize=(15, 10))
    plt.suptitle(f'Experiment: {exp_name}', fontsize=16)

    # 1. PV Production (shared plot)
    plt.subplot(3, 1, 1)
    plt.bar(hours, P_pv, color = 'Orange', width=0.3, label='PV Production (kW)', alpha=0.9)
    plt.xlabel('Hour')
    plt.ylabel('Power (kW)')
    plt.title('PV Production')
    plt.grid()
    plt.legend()

    # 2. Electricity Prices, Power Import & Export
    plt.subplot(3, 1, 2)
    plt.step(hours, prices, color='green', label='Electricity Price (DKK/kWh)', linewidth=2, where='post')
    plt.bar(hours, P_imp, width=0.3, label='Power Import (kW)', alpha=0.9)
    plt.bar(hours, P_exp, width=0.3, label='Power Export (kW)', alpha=0.9)
    plt.xlabel('Hour')
    plt.ylabel('Power (kW) / Prices (DKK/kWh)')
    plt.title('Electricity Prices, Power Import and Export Over 24 Hours')
    plt.grid()
    plt.legend()

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

exp_names = list(experiment_results.keys())
costs = [experiment_results[exp]['objective'] for exp in exp_names]

plt.figure(figsize=(8, 5))
plt.bar(exp_names, costs, color = 'steelblue')
plt.ylabel('Procurement Cost (DKK)')
plt.title('Procurement Cost by Different Cost Structures')
plt.grid(axis='y', alpha=0.3)
plt.show()
