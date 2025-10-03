from pathlib import Path
import numpy as np
import pandas as pd
import gurobipy as gp
from gurobipy import GRB




class Expando(object):

    pass


class InputData2b:

    def __init__(self,
                 variables: list,
                 el_prices: list[float],
                 imp_tariff: float,
                 exp_tariff: float,
                 upper_power_PV_rhs: list[float],
                 upper_power_rhs: list[float],
                 hourly_balance_rhs: list[float],
                 hourly_balance_sense: str,
                 battery_charge_efficiency: float,
                 battery_discharge_efficiency: float,
                 battery_initial_soc_ratio: float,
                 battery_min_soc_ratio: float,
                 max_charge_ratio: float,
                 max_discharge_ratio: float,
                 lifetime: float,
                 capex: int):
        
        self.variables = variables
        self.el_prices = el_prices
        self.imp_tariff = imp_tariff
        self.exp_tariff = exp_tariff
        self.upper_power_PV_rhs = upper_power_PV_rhs
        self.upper_power_rhs = upper_power_rhs
        self.hourly_balance_rhs = hourly_balance_rhs
        self.hourly_balance_sense = hourly_balance_sense
        self.battery_charge_efficiency = battery_charge_efficiency
        self.battery_discharge_efficiency = battery_discharge_efficiency
        self.battery_initial_soc_ratio = battery_initial_soc_ratio
        self.battery_min_soc_ratio = battery_min_soc_ratio
        self.max_charge_ratio = max_charge_ratio
        self.max_discharge_ratio = max_discharge_ratio
        self.lifetime = lifetime
        self.capex = capex
       




class OptModel2b():

    def __init__(self, input_data: InputData2b, name: str, hours: int = 24):
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
        self.cap_bat = self.model.addVar(name="Cap_bat")

    def _build_constraints(self):

        self.upper_power_PV = [ self.model.addLConstr(
            self.variables[0][t], GRB.LESS_EQUAL, self.data.upper_power_PV_rhs[t]
            )   
            for t in self.hours
        ]

        # Upper power constraints P_imp and P_exp
        self.upper_power = [ self.model.addLConstr(
            self.variables[v][t], GRB.LESS_EQUAL, self.data.upper_power_rhs[v-1]
             ) 
            for v in range(1, len(self.data.variables)-3) for t in self.hours
        ]
        # Hourly balance constraints
        self.hourly_balance = [ self.model.addLConstr(
            self.variables[0][t] + self.variables[1][t] - self.variables[2][t] - self.variables[3][t] + self.variables[4][t], self.data.hourly_balance_sense, self.data.hourly_balance_rhs[t]
            ) for t in self.hours
        ]

        # Maximum state of charge constraint
        self.SOC_max = [ self.model.addLConstr(
            self.variables[5][t], GRB.LESS_EQUAL, self.cap_bat
            )   
            for t in self.hours
        ]

        # Minimum state of charge constraint
        self.SOC_min = [ self.model.addLConstr(
            self.variables[5][t], GRB.GREATER_EQUAL, self.data.battery_min_soc_ratio * self.cap_bat
            )
            for t in self.hours
        ]

        # Intial state of charge
        self.SOC_init = self.model.addLConstr(
            self.variables[5][0], GRB.EQUAL, self.data.battery_initial_soc_ratio * self.cap_bat
        )

        ### Dual variable testing
        
        # Final state of charge
        #self.SOC_end = self.model.addLConstr(
        #    3, GRB.EQUAL, self.variables[5][23] + self.variables[3][23] * self.data.battery_charge_efficiency - self.variables[4][23] / self.data.battery_discharge_efficiency
        #)

        # Final state of charge
        self.SOC_end = self.model.addLConstr(
            self.variables[5][0], GRB.EQUAL, self.variables[5][23] + self.variables[3][23] * self.data.battery_charge_efficiency - self.variables[4][23] / self.data.battery_discharge_efficiency
        )


        # Battery charge max
        self.charge_max = [ self.model.addLConstr(
            self.variables[3][t], GRB.LESS_EQUAL, self.data.max_charge_ratio * self.cap_bat
            ) for t in self.hours
        ]

        
        # Battery discharge max
        self.discharge_max = [ self.model.addLConstr(
            self.variables[4][t], GRB.LESS_EQUAL, self.data.max_discharge_ratio * self.cap_bat
            ) for t in self.hours
        ]

        #SOC for every hour except 00 and 23
        self.SOC = [self.model.addLConstr(
            self.variables[5][t], GRB.EQUAL, self.variables[5][t-1] + self.variables[3][t-1] * self.data.battery_charge_efficiency - self.variables[4][t-1] / self.data.battery_discharge_efficiency
        ) for t in self.hours[1:24]
        ]

        ### All variables are automtically set to be greater than or equal to zero

    def _build_objective(self):
        self.model.setObjective(
        - self.data.capex * self.cap_bat + self.data.lifetime * gp.quicksum(self.variables[2][t] * (self.data.el_prices[t] - self.data.exp_tariff) - self.variables[1][t] * (self.data.el_prices[t] + self.data.imp_tariff) for t in self.hours),
        GRB.MAXIMIZE)


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
            'SOC_status': [self.SOC[i].Pi for i in range(len(self.SOC))],
            'SOC_max': [self.SOC_max[i].Pi for i in range(len(self.SOC_max))]
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


