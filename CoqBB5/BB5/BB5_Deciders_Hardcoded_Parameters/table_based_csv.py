#!/usr/bin/env python3
import os
import re
import csv
from typing import List, Tuple, Optional

def mxdys_to_bbchallenge(s):
    """ 
    >>> mxdys_to_bbchallenge("BR1 DL0 CR1 AR0 DR0 BR0 EL1 HR1 BL1 CL0")
    1RB0LD_1RC0RA_0RD0RB_1LE---_1LB0LC
    """
    to_ret = ""
    for i, t in enumerate(s.split(" ")):
        if "H" in t:
            to_ret += "---"
        else:
            to_ret += t[::-1]

        if i % 2 == 1:
            to_ret += "_"

    return to_ret[:-1]

def parse_makeTM_line(line: str) -> Optional[Tuple[str, str, Optional[int], Optional[int]]]:
    """
    Parse a line containing makeTM definition and extract components.
    
    Returns:
        Tuple of (tm_definition, decider_type, param1, param2) or None if no match
    """
    # Pattern to match makeTM lines with various decider types
    # Pattern for (makeTM ... ,TYPE param1 param2) - two parameters
    pattern_two_params = r'\(makeTM\s+([^,]+),\s*(\w+)\s+(\d+)\s+(\d+)\)'
    # Pattern for (makeTM ... ,TYPE param1) - one parameter
    pattern_one_param = r'\(makeTM\s+([^,]+),\s*(\w+)\s+(\d+)\)'
    # Pattern for (makeTM ... ,TYPE) - no parameters
    pattern_no_params = r'\(makeTM\s+([^,]+),\s*(\w+)\)'
    
    # Try pattern with two parameters first
    match = re.search(pattern_two_params, line)
    if match:
        tm_def = match.group(1).strip()
        decider_type = match.group(2)
        param1 = int(match.group(3))
        param2 = int(match.group(4))
        return (mxdys_to_bbchallenge(tm_def), decider_type, param1, param2)
    
    # Try pattern with one parameter
    match = re.search(pattern_one_param, line)
    if match:
        tm_def = match.group(1).strip()
        decider_type = match.group(2)
        param1 = int(match.group(3))
        return (mxdys_to_bbchallenge(tm_def), decider_type, param1, None)
    
    # Try pattern without parameters
    match = re.search(pattern_no_params, line)
    if match:
        tm_def = match.group(1).strip()
        decider_type = match.group(2)
        return (mxdys_to_bbchallenge(tm_def), decider_type, None, None)
    
    return None

def parse_coq_file(filepath: str) -> List[Tuple[str, str, Optional[int], Optional[int]]]:
    """
    Parse a Coq file and extract all makeTM definitions.
    
    Returns:
        List of tuples (tm_definition, decider_type, param1, param2)
    """
    results = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
            
            # Handle multi-line patterns for Verifier files
            if 'Verifier_FAR' in filepath:
                results.extend(parse_verifier_far_file(content))
            elif 'Verifier_WFAR' in filepath:
                results.extend(parse_verifier_wfar_file(content))
            else:
                # Original single-line parsing for other files
                for line in content.split('\n'):
                    line = line.strip()
                    if 'makeTM' in line:
                        parsed = parse_makeTM_line(line)
                        if parsed:
                            results.append(parsed)
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
    
    return results

def parse_verifier_far_file(content: str) -> List[Tuple[str, str, Optional[int], Optional[int]]]:
    """
    Parse Verifier FAR file with multi-line makeTM definitions.
    """
    results = []
    
    # Pattern to match multi-line makeTM with DNV, being more flexible with the nested structure
    # (makeTM ... , DNV ... (DFA_from_list (...)))::
    pattern = r'\(makeTM\s+([^,]+),\s*DNV\s+\d+\s+\(DFA_from_list\s+.*?\)\)\)::'
    
    matches = re.finditer(pattern, content, re.DOTALL)
    for match in matches:
        tm_def = match.group(1).strip()
        # Remove newlines and extra spaces
        tm_def = re.sub(r'\s+', ' ', tm_def)
        results.append((mxdys_to_bbchallenge(tm_def), 'FAR', None, None))
    
    return results

def parse_verifier_wfar_file(content: str) -> List[Tuple[str, str, Optional[int], Optional[int]]]:
    """
    Parse Verifier WFAR file with multi-line makeTM definitions.
    """
    results = []
    
    # Pattern to match multi-line makeTM with WA
    # (makeTM ... , WA ...)
    pattern = r'\(makeTM\s+([^,]+),\s*WA\s+.*?\)\)'
    
    matches = re.finditer(pattern, content, re.DOTALL)
    for match in matches:
        tm_def = match.group(1).strip()
        # Remove newlines and extra spaces
        tm_def = re.sub(r'\s+', ' ', tm_def)
        results.append((mxdys_to_bbchallenge(tm_def), 'WFAR', None, None))
    
    return results

def parse_sporadic_machines_file(filepath: str) -> List[Tuple[str, str, Optional[int], Optional[int]]]:
    """
    Parse BB5_Sporadic_Machines.v file with Definition statements.
    """
    results = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
            
            # Pattern to match Definition statements with makeTM
            # Definition Name := makeTM ...
            pattern = r'Definition\s+(?:Finned\d+|Skelet\d+)\s*:=\s*makeTM\s+([^.]+)\.'
            
            matches = re.finditer(pattern, content)
            for match in matches:
                tm_def = match.group(1).strip()
                # Remove newlines and extra spaces
                tm_def = re.sub(r'\s+', ' ', tm_def)
                results.append((mxdys_to_bbchallenge(tm_def), 'SPORADIC_MACHINE', None, None))
                
    except Exception as e:
        print(f"Error reading sporadic machines file {filepath}: {e}")
    
    return results

def main():
    # Directory containing the Coq files
    hardcoded_dir = "."
    
    if not os.path.exists(hardcoded_dir):
        print(f"Directory {hardcoded_dir} not found!")
        return
    
    # Find all .v files in the directory
    coq_files = []
    for filename in os.listdir(hardcoded_dir):
        if filename.endswith('.v'):
            coq_files.append(os.path.join(hardcoded_dir, filename))
    
    # Also check for the sporadic machines file in the parent directory
    sporadic_file = "../BB5_Sporadic_Machines.v"
    if os.path.exists(sporadic_file):
        coq_files.append(sporadic_file)
    
    if not coq_files:
        print(f"No .v files found in {hardcoded_dir}")
        return
    
    print(f"Found {len(coq_files)} Coq files to process:")
    for f in coq_files:
        print(f"  - {os.path.basename(f)}")
    print()
    
    # Collect all results
    all_results = []
    
    # Process each file
    for filepath in coq_files:
        filename = os.path.basename(filepath)
        print(f"Processing {filename}...")
        
        # Special handling for sporadic machines
        if "BB5_Sporadic_Machines.v" in filename:
            results = parse_sporadic_machines_file(filepath)
        else:
            results = parse_coq_file(filepath)
        
        print(f"  Found {len(results)} Turing machines")
        
        # Add results to the global list
        all_results.extend(results)
        
        # Show first few examples from this file
        if results:
            print("  Examples:")
            for i, (tm_def, decider_type, param1, param2) in enumerate(results[:3]):
                if param1 is not None and param2 is not None:
                    print(f"    \"{tm_def}\", \"{decider_type}\", {param1}, {param2}")
                else:
                    print(f"    \"{tm_def}\", \"{decider_type}\"")
        print()
    
    # Write results to CSV
    csv_filename = "turing_machines.csv"
    print(f"Writing {len(all_results)} total machines to {csv_filename}...")
    
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow(['TM_Definition', 'Decider_Type', 'Param1', 'Param2'])
        
        # Write data
        for tm_def, decider_type, param1, param2 in all_results:
            writer.writerow([tm_def, decider_type, param1 if param1 is not None else '', param2 if param2 is not None else ''])
    
    print(f"CSV file created successfully!")
    print(f"Total machines processed: {len(all_results)}")
    
    # Summary by decider type
    decider_counts = {}
    for _, decider_type, _, _ in all_results:
        decider_counts[decider_type] = decider_counts.get(decider_type, 0) + 1
    
    print("\nSummary by decider type:")
    for decider_type, count in sorted(decider_counts.items()):
        print(f"  {decider_type}: {count} machines")

if __name__ == "__main__":
    main()
