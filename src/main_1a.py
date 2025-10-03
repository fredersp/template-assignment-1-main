
import numpy as np
import gurobipy as gp
from gurobipy import GRB
import pandas as pd
#import matplotlib.pyplot as plt
#import seaborn as sns

from data_ops.data_loader import DataLoader
from opt_model.opt_model import OptModel1a, InputData1a, OptModel1b, InputData1b


data = DataLoader('data')

#########################
# Question 1a
#########################

app_data1a = data._load_data_file('question_1a', 'appliance_params.json')
bus_data1a = data._load_data_file('question_1a', 'bus_params.json')
con_data1a = data._load_data_file('question_1a', 'consumer_params.json')
DER_data1a = data._load_data_file('question_1a', 'DER_production.json')
usa_data1a = data._load_data_file('question_1a', 'usage_preference.json')

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

