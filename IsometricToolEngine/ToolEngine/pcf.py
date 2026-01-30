import csv
import os
import time
from datetime import datetime
import pandas as pd
import re

#Converts to date i/p to yyyy-mm-dd format.

def data_converter(date_input):
     
    date_formats = [
        "%Y-%m-%d",  # yyyy-mm-dd
        "%d-%m-%Y",  # dd-mm-yyyy
        "%m/%d/%Y",  # mm/dd/yyyy
        "%d/%m/%Y",  # dd/mm/yyyy
        "%B %d, %Y", # Month day, Year
        "%b %d, %Y", # Mon day, Year
     ]
    for date_format in date_formats:
        try:
            # Parse and format the date
            return datetime.strptime(date_input, date_format).strftime("%Y-%m-%d")
        except ValueError:
            continue
    
        raise ValueError(f"Date format for '{date_input}' is not recognized.")
     
# Define the mapping for PCF columns

mapping = {
    "isono": "ATTRIBUTE63",
    "action": None,
    "area": "ATTRIBUTE51",
    "av": None,
    "av_per": None,
    "bscode": None,
    "cccisono": None,
    "class": "PIPING-SPEC",
    "cservice": None,
    "critical": None,
    #"fabrevno": "REVISION",
    "fabrevno": "ATTRIBUTE120",
    "nnumberofsheets": None,
    "field1": None,
    "field2": None,
    "hard": None,
    "inchdia": None,
    "insul": "INSULATION-SPEC",
    "ninsulationthickness": "INSULATION-SPEC",
    "isohold": None,
    "isoweight": None,
    "clineno": "ATTRIBUTE60",
    "clinesize": "ATTRIBUTE61",
    "lupdate": None,
    "materials": None,
    "mp_pt": None,
    "mp_pt_per": None,
    "nojoint": None,
    "nospools": None,
    "owner": None,
    "paint": "PAINTING-SPEC",
    "pidno": "ATTRIBUTE41",
    "pidrev":None,
    "gadno":None,
    "presser":None,
    "pt":None,
    "pt_per":None,
    "pwht":None,
    "rcvdt":None,
    #"revdate":"ATTRIBUTE9",
    "revdate":"DATE-DMY",
    #"revno":"REVISION",
    "revno":"ATTRIBUTE120",
    "revstatus":None,
    "rt":None,
    "rt_per":None,
    "schedule":None,
    "sortfld1":None,
    "sortfld2":None,
    "subarea":None,
    "surfarea":None,
    "system":None,
    "testpackdt":None,
    "testpackno":None,
    "trandt":None,
    "ut":None,
    "ut_per":None,
    "wps":None,
    "testpack2":None,
    "inmtr":None,
    "sector":None,
    "unit":None,
    "discipline":None,
    "doctype":None,
    "docsubtype":None,
    "mtolevel":"ATTRIBUTE61",
    "fn_per":None,
    "docno":None,
    "cattachedfile":None,
    "cdesigntemperature":None,
    "coperatingpressure":"ATTRIBUTE40",
    "coperatingtemperature":"ATTRIBUTE39",
    "cdesignpressure":None,
    "dcreated":None,
    "ccreatedby":None,
    "dmodified":None,
    "cmodifiedby":None,
    "cprojectcode":None,
    "deleted":None,
    "deleted_by":None,
    "delete_date":None,
    "delete_reason":None,
    "package_name":None,  #   for package name mapping wrt ANS-NFS file
    "checked":None,
    "checked_by":None,
    "checked_date":None
}

# read the reference file for mapped Lv-3 field with SubContractor(PSM)
def load_reference_mapping(excel_path):
   
    mapping_data = pd.read_excel(excel_path)
    
    mapping_data.columns = mapping_data.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('(', '').str.replace(')', '')

    #print("Available normalized columns:(30Nov)", mapping_data.columns.tolist())
    
    # Will remove this part ... Match possible variations of required column names
    possible_lv3_names = ['lv_3', 'lv-3', 'level_3']
    possible_psm_names = ['subcontractor_psm', 'subcontractor_(psm)', 'psm']

    lv3_column = next((col for col in possible_lv3_names if col in mapping_data.columns), None)
    psm_column = next((col for col in possible_psm_names if col in mapping_data.columns), None)

    if not lv3_column or not psm_column:
        raise KeyError(f"Required columns missing. Found columns: {mapping_data.columns.tolist()}")

    # Use the matched column names
    return dict(zip(mapping_data[lv3_column], mapping_data[psm_column]))

# read another reference file for mapping from column Service Class to Materials
def load_pilewall_mapping(file_path):
    
    pilewall_data = pd.read_excel(file_path, sheet_name='Reference')
    mapping = dict(zip(pilewall_data["Service Class"], pilewall_data["Materials"]))
    return mapping

#mapping parsing here.
def parse_pcf(file_path, lv3_mapping, pilewall_mapping):
    print(" inside parse_pcf ::")
    data = {key: "" for key in mapping.keys()}
    recording = False
    first_pipeline_reference_found = False

    with open(file_path, 'r') as file:
        for line in file:
            if not first_pipeline_reference_found and "PIPELINE-REFERENCE" in line:
                recording = True
                first_pipeline_reference_found = True
                continue

            if recording and (not line.startswith(" ") or line.strip() == ""):
                break

            if recording:
                parts = line.split(maxsplit=1)
                if len(parts) == 2:
                    key, value = parts[0], parts[1].strip()
                    for csv_column, pcf_attribute in mapping.items():
                        if pcf_attribute == key:
                            data[csv_column] = value

    try:
        data["checked"] = False
        clinesize = float(data.get("clinesize", "0"))  # Get ATTRIBUTE61 value
        data["doctype"] = "LB" if clinesize >= 2 else "SB"
        
        today = datetime.now().strftime("%Y-%m-%d")  # Today's date 
        data["rcvdt"] = today
        
        # added for date converter ::02-02-2025
        data["revdate"] = data_converter(data["revdate"])
        #print("print revdate ####",data["revdate"])
       
        # Handle INSULATION-SPEC field
        insulation_spec = data.get("insul", "").strip()
        
        # Extract both numeric/alphabetic value and thickness from INSULATION-SPEC
        match = re.match(r"([A-Z0-9]+)\s*\(\s*(\d+)\s*mm\s*\)", insulation_spec, re.IGNORECASE)
        if match:
            # Group 1: Alphabetic or numeric value (e.g., 1, 5, A)
            # Group 2: Thickness value (e.g., 25, 50)
            data["insul"] = match.group(1)
            data["ninsulationthickness"] = match.group(2)
        elif insulation_spec.upper() == "UNDEFINED":
            # Handle UNDEFINED case
            data["insul"] = "N"
            data["ninsulationthickness"] = "0"
        else:
            # Default case for unknown or invalid formats
            data["insul"] = insulation_spec
            data["ninsulationthickness"] = "0"

        
        # update the field discipline based on the last char of AREA (U- Underground( UG ) else AboveGround AG)
        area = data.get("area", "").strip()
        if area and area[-1] == "U":
            data["discipline"] = "UG" 
        else:
            data["discipline"] = "AG"   

        # Post discipline we need to trim (first 7 characters only )the last char of AREA
        if len(area) > 7:
            area = area[:7]  
            data["area"] = area

        # Map PACKAGE_NAME based on AREA using lv3_mapping
        data["package_name"] = lv3_mapping.get(area, "NOT_FOUND")
        #print("package_name ::##", data["package_name"])
        
        # Enrich with material using pileWall mapping
        service_class = data.get("class", "").strip()
        #print(" service_class:: (30Nov)",service_class)
        #data["materials"] = pilewall_mapping.get(service_class, "Unknown")
        data["materials"] = pilewall_mapping.get(service_class, " ")
        #print(" data$$ :: " ,data["materials"])
    except ValueError:
        data["doctype"] = "SB"  # Default to "SB" if parsing fails
    #print("data ###",data)
    return data

#excel_path = "D:/ismometricFiles/referenceFiles/abs-nfs.xlsx"

def process_pcf_files(extracted_folders, output_csv, excel_path, pilewall_xlsx):
    """
    Process extracted folders, parse PCF files, and enrich with mappings from LV-3 and pileWall.xlsx.
    Ensure column order in the output CSV matches the order in all_data_rows.
    """
    print("Extracted folders: (30Nov)", extracted_folders)

    # Load mappings
    lv3_mapping = load_reference_mapping(excel_path)
    #print("LV-3 Mapping Loaded: (30Nov)", lv3_mapping)

    pilewall_mapping = load_pilewall_mapping(pilewall_xlsx)
    #print("PileWall Mapping Loaded:(30Nov)", pilewall_mapping)

    all_data_rows = []

    for folder in extracted_folders:
        print("Processing folder:", folder)
        for root, _, files in os.walk(folder):
            for file in files:
                if file.lower().endswith('.pcf'):                      # fix for issue .pcf, .PCF, .Pcf, .PcF
                    pcf_file_path = os.path.join(root, file)

                    # Parse and enrich the PCF file
                    data_row = parse_pcf(pcf_file_path, lv3_mapping, pilewall_mapping)
                    #print("data_row :: ##", data_row)
                    all_data_rows.append(data_row)

                        # Normalize INSULATION-SPEC
                    insul_value = data_row.get("insul", "").strip().upper()
                    match = re.match(r"([A-Z]+)\((\d+)\s*MM\)", insul_value)
                    if match:
                        data_row["insul"] = match.group(1)  # Extract leading characters (e.g., N, Y, etc.)
                        data_row["ninsulationthickness"] = match.group(2)  # Extract numeric thickness
                    elif insul_value == "UNDEFINED" or not insul_value:
                        data_row["insul"] = "N"
                        data_row["ninsulationthickness"] = "0"
                    else:
                        data_row["insul"] = insul_value  # Preserve the original value if no match
                        data_row["ninsulationthickness"] = data_row.get("ninsulationthickness", "0")  # Default to 0

                    # Normalize PAINTING-SPEC
                    paint_value = data_row.get("paint", "").strip().upper()
                    if paint_value == "UNDEFINED" or not paint_value:
                        data_row["paint"] = "N"  # Default to "N" if undefined or not available

        
        # Filter rows with specific class values
        ignore_classes = ['FRP', 'CIVIL-FRP-GENERIC', 'CIVIL-FRP', 'UG-PVC-GENERIC']
        all_data_rows = [row for row in all_data_rows if row.get("class", "").strip().upper() not in ignore_classes]    
        #print("all_data_rows###  ::",all_data_rows)    
    # Use the key order from the first row in all_data_rows for fieldnames
    if all_data_rows:
        fieldnames = list(all_data_rows[0].keys())  # Dynamically fetch the column order from the first row

        # Debug: Check final column order
        #print("Fieldnames for CSV:(30Nov)", fieldnames)

        # Write all data to the output CSV
        with open(output_csv, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_data_rows)

        print(f"PCF data successfully written to {output_csv}")
    else:
        print(f"No data rows found to write to {output_csv}.")

  

    #print(f"PCF data successfully written to {output_csv}")
