# Project Name

This repository contains the implementation of **Group 30**’s solution for Assignment 1 in the course **46750 - Optimization in Modern Power Systems (Fall 2025)**.  
It includes the optimization models, data processing, and visual outputs used in the submitted assignment.

**Group members**  
- s201163 — Frederik Tvede  
- s203684 — Frederik Springer Krehan

## Table of Contents
- Installation  
- Data Overview  
- Scripts Overview  
- Example Usage

## Installation

The code is submitted together with the written PDF assignment.  
Alternatively, it can be downloaded from GitHub:

https://github.com/fredersp/46750-assignment-1-fall-2025.git

Further refer to the requirements.txt for used packages and libraries. 

## Data Overview
All data has been provided by the course teaching team and is located in the `data/` directory.  
Each subfolder corresponds to a specific assignment question.  
Question **2b** uses the same dataset as **1c**.

data/
├── question_1a/
│   ├── appliance_params.json
│   ├── bus_params.json
│   ├── consumer_params.json
│   ├── DER_production.json
│   └── usage_preferences.json
├── question_1b/
│   ├── appliance_params.json
│   ├── bus_params.json
│   ├── consumer_params.json
│   ├── DER_production.json
│   └── usage_preferences.json
└── question_1c/
    ├── appliance_params.json
    ├── bus_params.json
    ├── consumer_params.json
    ├── DER_production.json
    └── usage_preferences.json


## Scripts Overview
The project code is located in the `src/` directory:

src/
├── data_ops/
│   └── data_loader.py  *Class for loading data from the JSON files*
├── opt_model/
│   ├── opt_model.py    *Classes for input data and the optimization models for question 1a, 1b and 1c*
│   └── opt_model_2.py  *Classes input data and the optimization model for question 2b*
├── main_1a.py          *Results of optimization problem, scenario analysis and plots for question 1a*
├── main_1b.py          *Results of optimization problem, scenario analysis and plots for question 1b*
├── main_1c.py          *Results of optimization problem, scenario analysis and plots for question 1c*   
└── main_2b.py          *Results of optimization problem, scenario analysis and plots for question 2b*


## Example Usage

To run a specific assignment solution, open the corresponding main script and execute it.  
For example:

- Run `main_1a.py` to generate results and plots for **Question 1a**  
- Run `main_2b.py` to generate results and plots for **Question 2b**

Each script will:
- Load the relevant JSON data  
- Solve the optimization problem  
- Run scenario analyses  
- Produce plots and outputs for both the main problem and scenario variations
