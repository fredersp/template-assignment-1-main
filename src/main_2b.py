##########################
# Question 2b
##########################

import numpy as np
import gurobipy as gp
from gurobipy import GRB
import pandas as pd
#import matplotlib.pyplot as plt
#import seaborn as sns

from data_ops.data_loader import DataLoader
from opt_model.opt_model_2 import OptModel2b, InputData2b


data = DataLoader('data')

app_data2b = data._load_data_file('question_1c', 'appliance_params.json')
bus_data2b = data._load_data_file('question_1c', 'bus_params.json')
con_data2b = data._load_data_file('question_1c', 'consumer_params.json')
DER_data2b = data._load_data_file('question_1c', 'DER_production.json')
usa_data2b = data._load_data_file('question_1c', 'usage_preferences.json') 

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

