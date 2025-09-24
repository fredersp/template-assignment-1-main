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

from data_ops.data_loader import DataLoader
from opt_model.opt_model import OptModel, InputData


data = DataLoader('data')


app_data = data._load_data_file('question_1a', 'appliance_params.json')
bus_data = data._load_data_file('question_1a', 'bus_params.json')
con_data = data._load_data_file('question_1a', 'consumer_params.json')
DER_data = data._load_data_file('question_1a', 'DER_production.json')
usa_data = data._load_data_file('question_1a', 'usage_preference.json')

variables = ['P_PV', 'P_imp', 'P_exp']
el_prices = bus_data[0]['energy_price_DKK_per_kWh']
imp_tariff = bus_data[0]['import_tariff_DKK/kWh']
upper_power_PV_rhs = np.array(DER_data[0]['hourly_profile_ratio']) * app_data['DER'][0]['max_power_kW']
upper_power_PV_rhs = upper_power_PV_rhs.tolist()
upper_power_rhs = [bus_data[0]['max_import_kW'], bus_data[0]['max_export_kW']]
hourly_balance_rhs = [app_data['load'][0]['max_load_kWh_per_hour'], 0]
hourly_balance_sense = [GRB.LESS_EQUAL, GRB.GREATER_EQUAL]

input_data = InputData(variables, 
                       el_prices, 
                       imp_tariff, 
                       upper_power_PV_rhs, 
                       upper_power_rhs, 
                       hourly_balance_rhs, 
                       hourly_balance_sense)



model = OptModel(input_data, 'TestModel')
model.run()
model.display_results()










