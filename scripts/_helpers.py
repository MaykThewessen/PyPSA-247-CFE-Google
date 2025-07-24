# SPDX-FileCopyrightText: 2017-2023 The PyPSA-Eur Authors
#
# SPDX-License-Identifier: MIT

import pypsa, numpy as np, pandas as pd
from pathlib import Path
import yaml
import difflib


def load_yaml(file_path):
    with open(file_path, "r") as file:
        return yaml.safe_load(file)


def compare_yaml(file1, file2):
    yaml1 = load_yaml("path/to/file1.yaml")
    yaml2 = load_yaml("path/to/file2.yaml")

    yaml1_lines = yaml.dump(yaml1).splitlines()
    yaml2_lines = yaml.dump(yaml2).splitlines()

    diff = difflib.unified_diff(
        yaml1_lines, yaml2_lines, lineterm="", fromfile=file1, tofile=file2
    )

    for line in diff:
        print(line)


# compare_yaml("file1.yaml", "file2.yaml")


def override_component_attrs():
    # from https://github.com/PyPSA/pypsa-eur-sec/blob/93eb86eec87d34832ebc061697e289eabb38c105/scripts/solve_network.py
    # Use regular dict instead of pypsa.descriptors.Dict (deprecated in newer versions)
    # Create a temporary network to access component_attrs
    temp_network = pypsa.Network()
    override_component_attrs = {
        k: v.copy() for k, v in temp_network.component_attrs.items()
    }
    # Add new attributes to Link component with proper DataFrame structure
    # Each row needs all columns: ['type', 'unit', 'default', 'description', 'status']
    
    new_attrs = {
        "bus2": ["string", np.nan, np.nan, "2nd bus", "Input (optional)"],
        "bus3": ["string", np.nan, np.nan, "3rd bus", "Input (optional)"],
        "bus4": ["string", np.nan, np.nan, "4th bus", "Input (optional)"],
        "efficiency2": ["static or series", "per unit", 1.0, "2nd bus efficiency", "Input (optional)"],
        "efficiency3": ["static or series", "per unit", 1.0, "3rd bus efficiency", "Input (optional)"],
        "efficiency4": ["static or series", "per unit", 1.0, "4th bus efficiency", "Input (optional)"],
        "p2": ["series", "MW", 0.0, "2nd bus output", "Output"],
        "p3": ["series", "MW", 0.0, "3rd bus output", "Output"],
        "p4": ["series", "MW", 0.0, "4th bus output", "Output"]
    }
    
    for attr_name, attr_values in new_attrs.items():
        override_component_attrs["Link"].loc[attr_name] = attr_values

    return override_component_attrs


def mock_snakemake(rulename, **wildcards):
    """
    This function is expected to be executed from the 'scripts'-directory of '
    the snakemake project. It returns a mock snakemake object for testing.

    If a rule has wildcards, you have to specify them in **wildcards.

    Parameters
    ----------
    rulename: str
        name of the rule for which the snakemake object should be generated
    **wildcards:
        keyword arguments fixing the wildcards. Only necessary if wildcards are
        needed.
    """
    import os

    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent
    current_dir = Path.cwd().resolve()
    
    # Handle being called from either scripts directory or project root
    if current_dir == script_dir:
        # Called from scripts directory
        os.chdir(script_dir.parent)
    elif current_dir == project_root:
        # Called from project root - this is fine, no need to change directory
        pass
    else:
        # Called from somewhere else - try to navigate to project root
        os.chdir(project_root)
    
    # Load config while in parent directory
    config_file = "config.yaml"
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
    else:
        config = {}
    
    class MockSnakemake:
        def __init__(self, wildcards, config):
            self.config = config
            self.wildcards = wildcards
            # Mock input/output files based on rule (relative to project root)
            if rulename == "summarise_network":
                # Use existing input files for testing
                year = wildcards.get('year', '2030')
                time_sampling = "1H"  # or "3H" based on config
                self.input = {
                    "network": f"../input/elec_s_37_lv1.0__{time_sampling}-B-solar+p3_{year}.nc",
                    "grid_cfe": f"../results/grid_cfe/{wildcards.get('zone', 'DE')}/grid_cfe_{wildcards.get('palette', 'p3')}_{wildcards.get('policy', 'ref')}_{wildcards.get('participation', '0')}.csv"
                }
                self.output = [f"../results/summaries/{wildcards.get('zone', 'DE')}/summary_{wildcards.get('palette', 'p3')}_{wildcards.get('policy', 'ref')}_{wildcards.get('participation', '0')}.yaml"]
            else:
                self.input = {}
                self.output = []
            
            self.log = []
            
    # Return to original directory
    os.chdir(current_dir)
    return MockSnakemake(wildcards, config)
