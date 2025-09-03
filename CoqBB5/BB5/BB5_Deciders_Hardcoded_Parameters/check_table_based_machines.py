#!/usr/bin/env python3
"""
Script to check that all machines listed in BB5_table_based_machines.csv
and BB5_normal_form_table_based_machines.csv appear in BB5_verified_enumeration.csv 
with their respective deciders ("TABLE_BASED" and "NORMAL_FORM_TABLE_BASED").
"""

import csv
import sys
from pathlib import Path

def read_machines_from_csv(filepath):
    """Read all machines from a CSV file."""
    machines = set()
    try:
        with open(filepath, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                machines.add(row['machine'])
        print(f"Read {len(machines)} machines from {filepath}")
        return machines
    except FileNotFoundError:
        print(f"Error: File {filepath} not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        sys.exit(1)

def check_machines_in_verified_enumeration(machines_by_decider, verified_enum_filepath):
    """
    Check which machines appear in verified_enumeration.csv with their expected deciders.
    
    Args:
        machines_by_decider: dict mapping decider names to sets of machines
        verified_enum_filepath: path to the verified enumeration file
    
    Returns:
        tuple of (found_machines_by_decider, missing_machines_by_decider)
    """
    found_machines_by_decider = {}
    missing_machines_by_decider = {}
    
    # Initialize results dictionaries
    for decider, machines in machines_by_decider.items():
        found_machines_by_decider[decider] = set()
        missing_machines_by_decider[decider] = machines.copy()
    
    try:
        with open(verified_enum_filepath, 'r') as file:
            reader = csv.DictReader(file)
            line_count = 0
            
            for row in reader:
                line_count += 1
                if line_count % 1000000 == 0:  # Progress indicator for large file
                    print(f"Processed {line_count:,} lines...")
                
                machine = row['machine']
                decider = row['decider']
                
                # Check if this machine is in any of our expected lists with the right decider
                if decider in machines_by_decider and machine in machines_by_decider[decider]:
                    found_machines_by_decider[decider].add(machine)
                    missing_machines_by_decider[decider].discard(machine)
            
            print(f"Finished processing {line_count:,} total lines")
            
    except FileNotFoundError:
        print(f"Error: File {verified_enum_filepath} not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading {verified_enum_filepath}: {e}")
        sys.exit(1)
    
    return found_machines_by_decider, missing_machines_by_decider

def main():
    # Define file paths
    script_dir = Path(__file__).parent
    table_based_filepath = script_dir / "BB5_table_based_machines.csv"
    normal_form_filepath = script_dir / "BB5_normal_form_table_based_machines.csv"
    verified_enum_filepath = script_dir.parent / "BB5_Extraction" / "BB5_verified_enumeration.csv"
    
    print("Checking table-based and normal-form table-based machines in verified enumeration...")
    print(f"Table-based machines file: {table_based_filepath}")
    print(f"Normal-form table-based machines file: {normal_form_filepath}")
    print(f"Verified enumeration file: {verified_enum_filepath}")
    print()
    
    # Read machines from both files
    table_based_machines = read_machines_from_csv(table_based_filepath)
    normal_form_machines = read_machines_from_csv(normal_form_filepath)
    
    # Create mapping of deciders to their expected machines
    machines_by_decider = {
        'TABLE_BASED': table_based_machines,
        'NORMAL_FORM_TABLE_BASED': normal_form_machines
    }
    
    # Check which machines are found in verified enumeration with correct deciders
    print("Scanning verified enumeration file (this may take a while for large files)...")
    found_machines_by_decider, missing_machines_by_decider = check_machines_in_verified_enumeration(
        machines_by_decider, verified_enum_filepath
    )
    
    # Report results
    print("\n" + "="*80)
    print("RESULTS:")
    print("="*80)
    
    total_expected = 0
    total_found = 0
    total_missing = 0
    has_missing = False
    
    for decider in ['TABLE_BASED', 'NORMAL_FORM_TABLE_BASED']:
        expected = len(machines_by_decider[decider])
        found = len(found_machines_by_decider[decider])
        missing = len(missing_machines_by_decider[decider])
        
        print(f"\n{decider}:")
        print(f"  Expected machines: {expected}")
        print(f"  Found in verified enumeration: {found}")
        print(f"  Missing from verified enumeration: {missing}")
        
        total_expected += expected
        total_found += found
        total_missing += missing
        
        if missing > 0:
            has_missing = True
    
    print(f"\nTOTAL SUMMARY:")
    print(f"  Total expected machines: {total_expected}")
    print(f"  Total found in verified enumeration: {total_found}")
    print(f"  Total missing from verified enumeration: {total_missing}")
    
    if has_missing:
        print("\n" + "!"*80)
        print("WARNING: Some machines are missing or don't have the correct decider:")
        print("!"*80)
        
        for decider in ['TABLE_BASED', 'NORMAL_FORM_TABLE_BASED']:
            missing_machines = missing_machines_by_decider[decider]
            if missing_machines:
                print(f"\nMissing {decider} machines ({len(missing_machines)}):")
                for machine in sorted(missing_machines):
                    print(f"  {machine}")
        
        return 1
    else:
        print("\n" + "✓"*80)
        print("SUCCESS: All machines found in verified enumeration with correct deciders!")
        print("✓"*80)
        return 0

if __name__ == "__main__":
    sys.exit(main())
