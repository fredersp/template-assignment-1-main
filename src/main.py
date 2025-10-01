"""
Placeholder for main function to execute the model runner. This function creates a single/multiple instance of the Runner class, prepares input data,
and runs a single/multiple simulation.

Suggested structure:
- Import necessary modules and functions.
- Define a main function to encapsulate the workflow (e.g. Create an instance of your the Runner class, Run a single simulation or multiple simulations, Save results and generate plots if necessary.)
- Prepare input data for a single simulation or multiple simulations.
- Execute main function when the script is run directly.
"""
import numpy as np
import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

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
daily_balance_rhs1a = usa_data1a[0]['load_preferences'][0]['min_total_energy_per_day_hour_equivalent']

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


##########################
# Question 1b
##########################

app_data1b = data._load_data_file('question_1b', 'appliance_params.json')
bus_data1b = data._load_data_file('question_1b', 'bus_params.json')
con_data1b = data._load_data_file('question_1b', 'consumer_params.json')
DER_data1b = data._load_data_file('question_1b', 'DER_production.json')
usa_data1b = data._load_data_file('question_1b', 'usage_preferences.json') 

variables1b = ['P_PV', 'P_imp', 'P_exp']
el_prices1b = bus_data1b[0]['energy_price_DKK_per_kWh']
imp_tariff1b = bus_data1b[0]['import_tariff_DKK/kWh']
upper_power_PV_rhs1b = np.array(DER_data1b[0]['hourly_profile_ratio']) * app_data1b['DER'][0]['max_power_kW']
upper_power_PV_rhs1b = upper_power_PV_rhs1b.tolist()
upper_power_rhs1b = [bus_data1b[0]['max_import_kW'], bus_data1b[0]['max_export_kW']]
hourly_balance_rhs1b = usa_data1b[0]['load_preferences'][0]['hourly_profile_ratio']
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

# Now you can access results like:
# experiment_results['base']['objective']
# experiment_results['high']['var_vals']

# plots visualizing the results





