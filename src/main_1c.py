##########################
# Question 1c
##########################

import numpy as np
import gurobipy as gp
from gurobipy import GRB
import pandas as pd
#import matplotlib.pyplot as plt
#import seaborn as sns

from data_ops.data_loader import DataLoader
from opt_model.opt_model import OptModel1c, InputData1c


data = DataLoader('data')

app_data1c = data._load_data_file('question_1c', 'appliance_params.json')
bus_data1c = data._load_data_file('question_1c', 'bus_params.json')
con_data1c = data._load_data_file('question_1c', 'consumer_params.json')
DER_data1c = data._load_data_file('question_1c', 'DER_production.json')
usa_data1c = data._load_data_file('question_1c', 'usage_preferences.json') 

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

# EXPERIMENT SETUP FOR COST STRUCTURE
experiment_cost = {
    'base': el_prices1c,
    'fixed': [np.mean(el_prices1c)] * len(el_prices1c),
    'no_day_tariff': [price - imp_tariff1c if 7 <= i <= 22 else price
                  for i, price in enumerate(el_prices1c)],
    'no_night_tariff': [price - imp_tariff1c if i < 7 or i > 22 else price
                  for i, price in enumerate(el_prices1c)],
}

# SCENARIO ANALYSIS FOR COST STRUCTURE
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
        "load_profile": exp_prices
    }
