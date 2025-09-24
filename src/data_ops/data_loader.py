# -----------------------------
# Load Data
# -----------------------------
import json
import pandas as pd
from pathlib import Path
import pandas as pd



# Create a class that loads data from JSON files


class DataLoader:

    def __init__(self, input_path: str):
        # Convert to Path object and resolve absolute path 
        # Weird code, solve late if possible
        self.input_path = Path(input_path).resolve().parent.parent / input_path
        


    def _load_data_file(self, question_name: str, file_name: str):
        """
        Helper function to load a specific JSON file, and store it as a class attribute.
        
        Parameters:
        - question_name: Subdirectory under input_path
        - file_name: Name of the file (CSV or JSON)
        - attr_name: Attribute name to save the loaded dataframe under (e.g., 'load', 'pv')
        
        Returns:
        - pandas DataFrame
        """
        file_path = self.input_path / question_name / file_name
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Load JSON
        if file_path.suffix == '.json':
            with open(file_path, 'r') as f:
                data = json.load(f)
        

        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

        
        return data
    