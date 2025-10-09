##########################
# Question 1b
##########################

import numpy as np
import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from data_ops.data_loader import DataLoader
from opt_model.opt_model import OptModel1b, InputData1b


data = DataLoader('.')

app_data1b = data._load_data_file('data/question_1b', 'appliance_params.json')
bus_data1b = data._load_data_file('data/question_1b', 'bus_params.json')
con_data1b = data._load_data_file('data/question_1b', 'consumer_params.json')
DER_data1b = data._load_data_file('data/question_1b', 'DER_production.json')
usa_data1b = data._load_data_file('data/question_1b', 'usage_preferences.json') 

variables1b = ['P_PV', 'P_imp', 'P_exp']
el_prices1b = bus_data1b[0]['energy_price_DKK_per_kWh']
imp_tariff1b = bus_data1b[0]['import_tariff_DKK/kWh']
upper_power_PV_rhs1b = np.array(DER_data1b[0]['hourly_profile_ratio']) * app_data1b['DER'][0]['max_power_kW']
upper_power_PV_rhs1b = upper_power_PV_rhs1b.tolist()
upper_power_rhs1b = [bus_data1b[0]['max_import_kW'], bus_data1b[0]['max_export_kW']]
hourly_balance_rhs1b = np.array(usa_data1b[0]['load_preferences'][0]['hourly_profile_ratio']) * app_data1b['load'][0]['max_load_kWh_per_hour']
hourly_balance_rhs1b = hourly_balance_rhs1b.tolist()
hourly_balance_sense1b = [GRB.EQUAL]


input_data1b = InputData1b(variables1b, 
                       el_prices1b, 
                       imp_tariff1b, 
                       upper_power_PV_rhs1b, 
                       upper_power_rhs1b, 
                       hourly_balance_rhs1b, 
                       hourly_balance_sense1b)
model1b = OptModel1b(input_data1b, 'Question 1b Model')
model1b.run()
model1b.display_results()


# EXPERIMENT SETUP
experiment = {
    'base': hourly_balance_rhs1b, 
    'high': [1.2 * val for val in hourly_balance_rhs1b], 
    'low': [0.8 * val for val in hourly_balance_rhs1b],
    'fixed': [np.mean(hourly_balance_rhs1b)] * len(hourly_balance_rhs1b)
}

# SENSITIVITY ANALYSIS
experiment_results = {}

for exp_name, exp_rhs in experiment.items():
    print(f"Running experiment: {exp_name}")
    input_data1b = InputData1b(
        variables1b, 
        el_prices1b, 
        imp_tariff1b, 
        upper_power_PV_rhs1b, 
        upper_power_rhs1b, 
        exp_rhs, 
        hourly_balance_sense1b
    )
    model1b = OptModel1b(input_data1b, f'Question 1b Model {exp_name}')
    model1b.run()
    model1b.display_results()
    # Store results
    experiment_results[exp_name] = {
        "objective": model1b.results.obj_val,
        "var_vals": model1b.results.var_vals,
        "dual_vals": model1b.results.dual_vals,
        "load_profile": exp_rhs
    }



# plots visualizing the results

for exp_name, results in experiment_results.items():
    hours = range(len(results['load_profile']))
    
    load = results['load_profile']
    P_imp = [results['var_vals'][('P_imp', t)] for t in hours]
    P_exp = -np.array([results['var_vals'][('P_exp', t)] for t in hours])
    P_pv  = [results['var_vals'][('P_PV', t)] for t in hours]
    prices = el_prices1b

    plt.figure(figsize=(15, 10))
    plt.suptitle(f'Experiment: {exp_name}', fontsize=16)

    # 1. Electricity Price + PV Production (shared plot)
    plt.subplot(3, 1, 1)
    hours_step = list(hours) + [hours[-1] + 1]
    load_step = list(load) + [load[-1]]
    plt.step(hours_step, load_step, label='Hourly Load Profile [kW]', linewidth=2, where='post', color='blue')
    plt.bar(hours, P_pv, color = 'orange', width=0.95, label='PV Production (kW)', alpha=0.9, align='edge')
    plt.xlabel('Hour')
    plt.ylabel('Power [kW]')
    plt.title('Hourly Load Profile and PV Production')
    plt.xlim(0, 24)
    plt.grid()
    plt.legend()

    # 2. Power Import & Export
    plt.subplot(3, 1, 2)
    prices_step = list(prices) + [prices[-1]]
    plt.step(hours_step, prices_step, color = 'green', label = 'Electricity Prices (DKK/kWh)', where='post', linewidth=2)
    plt.bar(hours, P_imp, width=0.95, label='Power Import (kW)', alpha=0.9, color='skyblue', align='edge')
    plt.bar(hours, P_exp, width=0.95, label='Power Export (kW)', alpha=0.9, color='grey', align='edge')
    plt.xlabel('Hour')
    plt.ylabel('Power [kW] / Price [DKK/kWh]')
    plt.title('Electricity Prices,Power Import and Export Over 24 Hours')
    plt.xlim(0, 24)
    plt.grid()
    plt.legend()

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()





