from pathlib import Path
import numpy as np
import pandas as pd
import gurobipy as gp
from gurobipy import GRB


#from src.data_ops import data_loader



class Expando(object):

    pass




class InputData:

    def __init__(self,
                 variables: list,
                 el_prices: list[float],
                 imp_tariff: float,
                 upper_power_PV_rhs: list[float],
                 upper_power_rhs: list[float],
                 hourly_balance_rhs: list[float],
                 hourly_balance_sense: list[str]):
        
        self.variables = variables
        self.el_prices = el_prices
        self.imp_tariff = imp_tariff
        self.upper_power_PV_rhs = upper_power_PV_rhs
        self.upper_power_rhs = upper_power_rhs
        self.hourly_balance_rhs = hourly_balance_rhs
        self.hourly_balance_sense = hourly_balance_sense

        


class OptModel():

    def __init__(self, input_data: InputData, name: str, hours: int = 24):
        self.data = input_data
        self.name = name
        self.hours = range(hours)
        self.results = Expando()
        self._build_model()

    def _build_variables(self):
        self.variables = [
            self.model.addVar(name=f"{v}_{t}") for v in self.data.variables for t in self.hours
        ]

    def _build_constraints(self):

        self.upper_power_PV = [ self.model.addLConstr(
            self.variables(0,t), GRB.LESS_EQUAL, self.data.upper_power_PV_rhs[t]
            ) for t in self.hours
        ]

        # Upper power constraints P_imp and P_exp
        self.upper_power = [ self.model.addLConstr(
            self.variables[v,t], GRB.LESS_EQUAL, self.data.upper_power_rhs[v]
             ) 
            for v in range(1, len(self.data.variables)-1) for t in self.hours
        ]
        # Hourly balance constraints
        self.hourly_balance = [ self.model.addLConstr(
            self.variables[0, t] + self.variables[1, t] - self.variables[2, t], self.hourly_balance_sense[j], self.hourly_balance_rhs[j]
            ) for t in self.hours for j in range(len(self.data.hourly_balance_rhs))

        ]

        # Daily balance constraint
        self.daily_balance = self.model.addLConstr(
            gp.quicksum(self.variables[0, t] + self.variables[1, t] - self.variables[2, t] for t in self.hours), GRB.GREATER_EQUAL, 0
        )


    def _build_objective(self):
        self.model.setObjective(
            gp.quicksum(self.variables[0, t] * (self.data.el_prices[t] + self.data.imp_tariff) for t in self.hours),
        GRB.minimize)


    def _build_model(self):
        self.model = gp.Model(self.name)
        self._build_variables()
        self._build_constraints()
        self._build_objective()
        self.model.update()
    
    
    def _save_results(self):
        self.results.obj_val = self.model.ObjVal
        self.results.var_vals = {(v, t): self.variables[v, t].x for v in self.data.variables for t in self.hours}
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
        