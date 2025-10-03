from pathlib import Path
import numpy as np
import pandas as pd
import gurobipy as gp
from gurobipy import GRB


#from src.data_ops import data_loader



class Expando(object):

    pass




class InputData1a:

    def __init__(self,
                 variables: list,
                 el_prices: list[float],
                 imp_tariff: float,
                 upper_power_PV_rhs: list[float],
                 upper_power_rhs: list[float],
                 hourly_balance_rhs: list[float],
                 hourly_balance_sense: list[str],
                 daily_balance_rhs: float):
        
        self.variables = variables
        self.el_prices = el_prices
        self.imp_tariff = imp_tariff
        self.upper_power_PV_rhs = upper_power_PV_rhs
        self.upper_power_rhs = upper_power_rhs
        self.hourly_balance_rhs = hourly_balance_rhs
        self.hourly_balance_sense = hourly_balance_sense
        self.daily_balance_rhs = daily_balance_rhs

        


class OptModel1a():

    def __init__(self, input_data: InputData1a, name: str, hours: int = 24):
        self.data = input_data
        self.name = name
        self.hours = range(hours)
        self.results = Expando()
        self._build_model()

    def _build_variables(self):
        self.variables = [
        [self.model.addVar(name=f"{v}_{t}") for t in self.hours]
        for v in self.data.variables
    ]

    def _build_constraints(self):

        self.upper_power_PV = [ self.model.addLConstr(
            self.variables[0][t], GRB.LESS_EQUAL, self.data.upper_power_PV_rhs[t]
            )   
            for t in self.hours
        ]

        # Upper power constraints P_imp and P_exp
        self.upper_power = [ self.model.addLConstr(
            self.variables[v][t], GRB.LESS_EQUAL, self.data.upper_power_rhs[v]
             ) 
            for v in range(1, len(self.data.variables)-1) for t in self.hours
        ]
        # Hourly balance constraints
        self.hourly_balance = [ self.model.addLConstr(
            self.variables[0][t] + self.variables[1][t] - self.variables[2][t], self.data.hourly_balance_sense[j], self.data.hourly_balance_rhs[j]
            ) for t in self.hours for j in range(len(self.data.hourly_balance_rhs))

        ]

        # Daily balance constraint
        self.daily_balance = self.model.addLConstr(
            gp.quicksum(self.variables[0][t] + self.variables[1][t] - self.variables[2][t]  for t in self.hours), GRB.GREATER_EQUAL, self.data.daily_balance_rhs
        )

        ### All variables are automtically set to be greater than or equal to zero



    def _build_objective(self):
        self.model.setObjective(
            gp.quicksum(self.variables[1][t] * (self.data.el_prices[t] + self.data.imp_tariff) for t in self.hours),
        GRB.MINIMIZE)


    def _build_model(self):
        self.model = gp.Model(self.name)
        self._build_variables()
        self._build_constraints()
        self._build_objective()
        self.model.update()
    
    
    def _save_results(self):
        self.results.obj_val = self.model.ObjVal
        self.results.var_vals = {(self.data.variables[v], t): self.variables[v][t].x
                         for v in range(len(self.data.variables)) for t in self.hours}
        # please return the dual values for all constraints
        self.results.dual_vals = {
            'upper_power': [self.upper_power[i].Pi for i in range(len(self.upper_power))],
            'hourly_balance': [self.hourly_balance[i].Pi for i in range(len(self.hourly_balance))],
            'daily_balance': self.daily_balance.Pi
        }

    def run(self):
        self.model.optimize()
        if self.model.status == GRB.OPTIMAL:
            self._save_results()
        else:
            raise ValueError("No optimal solution found for {self.model.name}")
        
    def display_results(self):
        print()
        print("-------------------   RESULTS  -------------------")
        print("Optimal objective value:")
        print(self.results.obj_val)
        print("Optimal variable values:")
        print(self.results.var_vals)
        print("Optimal dual values:")
        print(self.results.dual_vals)


class InputData1b:

    def __init__(self,
                 variables: list,
                 el_prices: list[float],
                 imp_tariff: float,
                 upper_power_PV_rhs: list[float],
                 upper_power_rhs: list[float],
                 hourly_balance_rhs: list[float],
                 hourly_balance_sense: str):
        
        self.variables = variables
        self.el_prices = el_prices
        self.imp_tariff = imp_tariff
        self.upper_power_PV_rhs = upper_power_PV_rhs
        self.upper_power_rhs = upper_power_rhs
        self.hourly_balance_rhs = hourly_balance_rhs
        self.hourly_balance_sense = hourly_balance_sense
       




class OptModel1b():

    def __init__(self, input_data: InputData1b, name: str, hours: int = 24):
        self.data = input_data
        self.name = name
        self.hours = range(hours)
        self.results = Expando()
        self._build_model()

    def _build_variables(self):
        self.variables = [
        [self.model.addVar(name=f"{v}_{t}") for t in self.hours]
        for v in self.data.variables
    ]

    def _build_constraints(self):

        self.upper_power_PV = [ self.model.addLConstr(
            self.variables[0][t], GRB.LESS_EQUAL, self.data.upper_power_PV_rhs[t]
            )   
            for t in self.hours
        ]

        # Upper power constraints P_imp and P_exp
        self.upper_power = [ self.model.addLConstr(
            self.variables[v][t], GRB.LESS_EQUAL, self.data.upper_power_rhs[v]
             ) 
            for v in range(1, len(self.data.variables)-1) for t in self.hours
        ]
        # Hourly balance constraints
        self.hourly_balance = [ self.model.addLConstr(
            self.variables[0][t] + self.variables[1][t] - self.variables[2][t], self.data.hourly_balance_sense, self.data.hourly_balance_rhs[t]
            ) for t in self.hours
        ]


        ### All variables are automtically set to be greater than or equal to zero



    def _build_objective(self):
        self.model.setObjective(
            gp.quicksum(self.variables[1][t] * (self.data.el_prices[t] + self.data.imp_tariff) for t in self.hours),
        GRB.MINIMIZE)


    def _build_model(self):
        self.model = gp.Model(self.name)
        self._build_variables()
        self._build_constraints()
        self._build_objective()
        self.model.update()
    
    
    def _save_results(self):
        self.results.obj_val = self.model.ObjVal
        self.results.var_vals = {(self.data.variables[v], t): self.variables[v][t].x
                         for v in range(len(self.data.variables)) for t in self.hours}
        # please return the dual values for all constraints
        self.results.dual_vals = {
            'upper_power': [self.upper_power[i].Pi for i in range(len(self.upper_power))],
            'hourly_balance': [self.hourly_balance[i].Pi for i in range(len(self.hourly_balance))],
        }

    def run(self):
        self.model.optimize()
        if self.model.status == GRB.OPTIMAL:
            self._save_results()
        else:
            raise ValueError("No optimal solution found for {self.model.name}")
        
    def display_results(self):
        print()
        print("-------------------   RESULTS  -------------------")
        print("Optimal objective value:")
        print(self.results.obj_val)
        print("Optimal variable values:")
        print(self.results.var_vals)
        print("Optimal dual values:")
        print(self.results.dual_vals)





class InputData1c:

    def __init__(self,
                 variables: list,
                 el_prices: list[float],
                 imp_tariff: float,
                 upper_power_PV_rhs: list[float],
                 upper_power_rhs: list[float],
                 hourly_balance_rhs: list[float],
                 hourly_balance_sense: str,
                 battery_capacity: float,
                 battery_charge_efficiency: float,
                 battery_discharge_efficiency: float,
                 battery_initial_soc: float,
                 battery_min_soc: float,
                 max_charge: float,
                 max_discharge: float):
        
        self.variables = variables
        self.el_prices = el_prices
        self.imp_tariff = imp_tariff
        self.upper_power_PV_rhs = upper_power_PV_rhs
        self.upper_power_rhs = upper_power_rhs
        self.hourly_balance_rhs = hourly_balance_rhs
        self.hourly_balance_sense = hourly_balance_sense
        self.battery_capacity = battery_capacity
        self.battery_charge_efficiency = battery_charge_efficiency
        self.battery_discharge_efficiency = battery_discharge_efficiency
        self.battery_initial_soc = battery_initial_soc
        self.battery_min_soc = battery_min_soc
        self.max_charge = max_charge
        self.max_discharge = max_discharge
       




class OptModel1c():

    def __init__(self, input_data: InputData1b, name: str, hours: int = 24):
        self.data = input_data
        self.name = name
        self.hours = range(hours)
        self.results = Expando()
        self._build_model()

    def _build_variables(self):
        self.variables = [
        [self.model.addVar(name=f"{v}_{t}") for t in self.hours]
        for v in self.data.variables
    ]

    def _build_constraints(self):

        self.upper_power_PV = [ self.model.addLConstr(
            self.variables[0][t], GRB.LESS_EQUAL, self.data.upper_power_PV_rhs[t]
            )   
            for t in self.hours
        ]

        # Upper power constraints P_imp and P_exp
        self.upper_power = [ self.model.addLConstr(
            self.variables[v][t], GRB.LESS_EQUAL, self.data.upper_power_rhs[v]
             ) 
            for v in range(1, len(self.data.variables)-4) for t in self.hours
        ]
        # Hourly balance constraints
        self.hourly_balance = [ self.model.addLConstr(
            self.variables[0][t] + self.variables[1][t] - self.variables[2][t] - self.variables[3][t] + self.variables[4][t], self.data.hourly_balance_sense, self.data.hourly_balance_rhs[t]
            ) for t in self.hours
        ]

        # Maximum state of charge constraint
        self.SOC_max = [ self.model.addLConstr(
            self.variables[5][t], GRB.LESS_EQUAL, self.data.battery_capacity
            )   
            for t in self.hours
        ]

        # Minimum state of charge constraint
        self.SOC_min = [ self.model.addLConstr(
            self.variables[5][t], GRB.GREATER_EQUAL, self.data.battery_min_soc 
            )
            for t in self.hours
        ]

        # Intial state of charge
        self.SOC_init = self.model.addLConstr(
            self.variables[5][0], GRB.EQUAL, self.data.battery_initial_soc
        )

        # Final state of charge
        self.SOC_end = self.model.addLConstr(
            self.variables[5][23], GRB.EQUAL, self.data.battery_initial_soc
        )

        # Battery charge max
        self.charge_max = [ self.model.addLConstr(
            self.variables[3][t], GRB.LESS_EQUAL, self.data.max_charge
            ) for t in self.hours
        ]

        
        # Battery discharge max
        self.discharge_max = [ self.model.addLConstr(
            self.variables[4][t], GRB.LESS_EQUAL, self.data.max_discharge
            ) for t in self.hours
        ]

        #SOC for every hour except 00 and 23
        self.SOC = [self.model.addLConstr(
            self.variables[5][t], GRB.EQUAL, self.variables[5][t-1] + self.variables[3][t] * self.data.battery_charge_efficiency - self.variables[4][t] / self.data.battery_discharge_efficiency
        ) for t in self.hours[1:24]
        ]

        ### All variables are automtically set to be greater than or equal to zero



    def _build_objective(self):
        self.model.setObjective(
            gp.quicksum(self.variables[1][t] * (self.data.el_prices[t] + self.data.imp_tariff) for t in self.hours),
        GRB.MINIMIZE)


    def _build_model(self):
        self.model = gp.Model(self.name)
        self._build_variables()
        self._build_constraints()
        self._build_objective()
        self.model.update()
    
    
    def _save_results(self):
        self.results.obj_val = self.model.ObjVal
        self.results.var_vals = {(self.data.variables[v], t): self.variables[v][t].x
                         for v in range(len(self.data.variables)) for t in self.hours}
        # please return the dual values for all constraints
        self.results.dual_vals = {
            'upper_power': [self.upper_power[i].Pi for i in range(len(self.upper_power))],
            'hourly_balance': [self.hourly_balance[i].Pi for i in range(len(self.hourly_balance))],
            'SOC_status': [self.SOC[i].Pi for i in range(len(self.SOC))]
        }

    def run(self):
        self.model.optimize()
        if self.model.status == GRB.OPTIMAL:
            self._save_results()
        else:
            raise ValueError("No optimal solution found for {self.model.name}")
        
    def display_results(self):
        print()
        print("-------------------   RESULTS  -------------------")
        print("Optimal objective value:")
        print(self.results.obj_val)
        print("Optimal variable values:")
        print(self.results.var_vals)
        print("Optimal dual values:")
        print(self.results.dual_vals)
