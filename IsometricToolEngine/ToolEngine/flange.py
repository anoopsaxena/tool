import csv
import os
#from fractions import Fraction
from pmsisod import calculate_matsubcode, parse_fraction 

       

# 11-June added for cclass","materials" PMSISOH->class    PMSISOH->materials

def parse_pmsisoh_data(file_path):
    """
    Parse PMSISOH CSV to extract required fields using `isono` as the key.
    """
    pmsisoh_data = {}
    with open(file_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        # Ensure the required columns exist
        required_columns = ["isono", "class", "materials"]
        for col in required_columns:
            if col not in reader.fieldnames:
                print(f"Error: Missing column '{col}' in PMSISOH CSV file.")
                return pmsisoh_data  # Return an empty dictionary

        for row in reader:
            isono = row.get("isono", "").strip()
            if isono:
                pmsisoh_data[isono] = {
                    "class": row.get("class", "").strip(),
                    "materials": row.get("materials", "").strip(),
                }
    #print("pmsisoh_data ",pmsisoh_data)             
    return pmsisoh_data

def enrich_data(merged_data, pmsisoh_data):
    """
    Enrich the PMSSPL data with additional fields: progpaint and clineno.
    """
    enriched_data = []

    # Process each record
    for row in merged_data:
        # key = (row["isono"], row["spoolno"])
        key = row["isono"]
        #print("pmsisoh_data ",pmsisoh_data)
        if key in pmsisoh_data:
            row["cclass"] = pmsisoh_data[key].get("class", "")
            row["materials"] = pmsisoh_data[key].get("materials", "")

        # Append enriched row
        enriched_data.append(row)

    #return enriched_data
    return remove_duplicates(enriched_data, key_fields=["isono", "flangeno"])

def remove_duplicates(data, key_fields):
    """
    Remove duplicate records based on a combination of unique key fields.
    """
    seen_keys = set()
    unique_data = []
    for row in data:
        key = tuple(row[field] for field in key_fields)
        if key not in seen_keys:
            seen_keys.add(key)
            unique_data.append(row)
    return unique_data  
    
def parse_bolt_file(file_path):
    bolt_data = []
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) >= 7:
                
                bolt_lsize = parse_fraction(row[5].strip())
                bolt_ssize = row[7].strip()
                #bolt_matsubcode = f"{bolt_lsize} {bolt_ssize}"   #need to be changed  11-June
                matsubcode = calculate_matsubcode(row[5].strip())
                
                bolt_data.append({
                    "isono": row[0].strip(),
                    "flangeno":row[2].strip(),                    
                    #"bolt_matcode" : row[8].strip(),
                    #"bolt_matsubcode":parse_fraction(row[5].strip()),    #bolt_lssize 7 Space followed by bolt_ssize
                    #"bolt_matsubcode": matsubcode,  #changed 11-June
                    #"bolt_mat_source":"P",
                    "bolt_number":row[6].strip(),
                    "sheetno": row[1].strip(),
                    "inchdia":parse_fraction(row[4].strip()),
                    "flange_lsize":parse_fraction(row[4].strip()),
                    "bolt_ssize": bolt_ssize,
                    "bolt_lsize": bolt_lsize,
                    "tightening_method":"Manual",     #11-June added
                })
    return bolt_data

def find_file_by_partial_name(folder, partial_name):
    # for file in os.listdir(folder):  #  looks in the immediate folder

    print(f"Searching for '{partial_name}' in folder: {folder}")
    for root, _, files in os.walk(folder):
        for file in files:
            print(f"Checking file: {file}")
            if partial_name.lower() in file.lower():
                print(f"File found: {os.path.join(root, file)}")
                return os.path.join(root, file)
    print(f"No file found with partial name '{partial_name}' in folder: {folder}")
    return None


# Process  file and write to CSV.
 
def process_pmsbolt_files(extracted_folders, output_csv,output_pcf_csv):
  
    all_data = []
    pmsisoh_data = parse_pmsisoh_data(output_pcf_csv)
    print("pmsisoh_data ### ",pmsisoh_data)

    for folder in extracted_folders:
        bolt_file = find_file_by_partial_name(folder, "Bolt.txt")

        if not bolt_file :
            print(f"Missing required files in {folder}")
            continue

        # Parse files
        bolt_data = parse_bolt_file(bolt_file)

        # Debug: Print data
        print("bolt_data : ", bolt_data)

        all_data.extend(bolt_data)
        
        enriched_data = enrich_data(all_data, pmsisoh_data)

    # Write enriched data to CSV
    write_csv(output_csv, enriched_data)

    # Write data to CSV
    #write_csv(output_csv, all_data)

    
def write_csv(output_file, data):
    columns = [
        "isono","flangeno","spoolno","cclass","materials","status","fluid_service","flange_matcode",
        "flange_matsubcode","flange_mat_source","bolt_matcode","bolt_matsubcode","bolt_mat_source",
        "bolt_number","gasket_matcode","gasket_matsubcode",
        "gasket_mat_source","adjacent_flange_matcode","adjacent_flange_matsubcode","adjacent_flange_mat_source",
        "equipment_mat_code","equipment_mat_subcode","equipment_mat_source","tightening_method","required_torque_value",
        "deleted","delete_date","deleted_by","delete_reason","sheetno","inchdia","rating","flange_ssize","flange_lsize",
        "bolt_ssize","bolt_lsize","gasket_ssize","gasket_lsize","adjacent_flange_ssize","adjacent_flange_lsize","equipment_ssize",
        "equipment_lsize"
    ]
    with open(output_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(data)
