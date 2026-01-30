import os
import csv
import pandas as pd 
from fractions import Fraction
import fractions

#case: 
    # 1) If spool number is blank, change to F01.
    # 2) If spool number has an exact match with 'SP0' --> F01
    # 3) If spool number is exactly 'SP000' --> F01
    # 4) else remain unchanged.

def normalize_spoolno(spoolno):

    if not spoolno or spoolno.strip() == "":  # Condition 1: Blank spool number
        return "F01"
    elif spoolno.strip().upper() == "SP0":  # Condition 2: Exact match with 'SP0'
        return "F01"
    elif spoolno.strip().upper() == "SP000":  # Condition 3: Exactly 'SP000'
        return "F01"
    else:  # Return  if no condition matches
        return spoolno.strip()


# Handles fractions (e.g., "1/2"), mixed fractions (e.g., "1.1/2") and whole numbers.
def convert_nominal_size(value):
  
    try:
        if '/' in value:
            if '.' in value:
                # Case: Mixed fractions like "1.1/2"
                whole_part, fraction_part = value.split('.')
                numerator, denominator = fraction_part.split('/')
                return float(whole_part) + float(numerator) / float(denominator)
            else:
                # Case: Proper fractions like "1/2"
                numerator, denominator = value.split('/')
                return float(numerator) / float(denominator)
        else:
            # Case: Whole numbers
            result = float(value)
        return int(result) if result.is_integer() else result
        
    except (ValueError, ZeroDivisionError) as e:
        print(f"Warning: Invalid nominal size value '{value}' encountered. Error: {e}")
        return 0


#Parse the weld.txt file and enrich with materials, thickness, and schedule fields.

def parse_weld_file_for_pmsjnth(file_path, service_class_mapping):
    
    weld_data = []
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) >= 17:  # Ensure the row has all necessary columns
                isono = row[0].strip()  # Weld->Isometric No. (Col1)
                weld_class = row[9].strip().upper()  # Normalize to uppercase
                
                weldtype = f"{row[7].strip()}{row[8].strip()}"  # Weld->WELD CATEGORY (Col8) + Weld->WELD TYPE (Col9)
                
                # Updated logic for branchdia :: 29 Dec
                #weld_no = row[3].strip()  # Weld->WELD NO (Col4)
                weld_no = row[3].strip()   # Weld->WELD NO (Col4), pad to 3 digits
                if weld_no.isdigit() and len(weld_no) < 3:
                    weld_no = weld_no.zfill(3)
                else:
                    weld_no = weld_no
                #print("weld_no ",weld_no)
                nominal_size = row[6].strip()  # Weld->NOMINAL SIZE (Col7)
                #branchdia = nominal_size if weld_no.startswith("S") else "0"
                
                # Updated logic for inchdia
                
                if weld_no.startswith("S"):  
                    inchdia = "0"  # Set inchdia to 0
                    branchdia = str(convert_nominal_size(nominal_size))  
                else:  # If weld_no does not start with 'S'
                    inchdia = str(convert_nominal_size(nominal_size))  
                    branchdia = "0"  # Set branchdia to 0
                                
                #print("inchdia### ",inchdia)  
                #print("branchdia### ",branchdia)                  
                
                
                # Updated logic for inchdia
                # if weld_no.startswith("S"):
                #     inchdia = "0"
                # else:
                #     try:
                #         if '/' in nominal_size:  # Handle fraction sizes
                #             inchdia = str(float(fractions.Fraction(nominal_size)))
                #         else:
                #             inchdia = nominal_size  # Use as-is if not a fraction
                #     except ValueError:
                #         inchdia = "0"  # Default to 0 if conversion fails
                #
                #
                #
                #
                # if weldtype == "SP":  # If Weldtype is SP, set inchdia to 0
                #     inchdia = "0"
                # else:
                #     raw_inchdia = row[6].strip()  # Read the original value
                #     try:
                #         if '/' in raw_inchdia:  # Check if it's a fraction
                #             inchdia = str(float(fractions.Fraction(raw_inchdia)))  # Convert fraction to decimal
                #         else:
                #             inchdia = raw_inchdia  # Keep it as-is if it's not a fraction
                #     except ValueError:
                #         inchdia = "0"  # Default to 0 if conversion fails

                #print("inchdia### ", inchdia)
                #inchdia = row[6].strip()  # Trim spaces
                
                #29-12-2024 :: end
                spoolno = ""  # blank
               
                weldtype = f"{row[7].strip()}{row[8].strip()}"  # Weld->WELD CATEGORY (Col8) + Weld->WELD TYPE (Col9)
                #service_class = row[9].strip()  # Weld->PIPING CLASS (Col10)
                #branchdia = row[6].strip() if weldtype == "SP" else "0"
                weld_class = row[9].strip()  # Weld->PIPING CLASS (Col10)
                csheetnumber = row[1].strip()  # Weld->SHEET NO (Col2)
                cpreviousmaterial = row[13].strip()  # Weld->IDENT-UP (Col14)
                cnextmaterial = row[15].strip()  # Weld->IDENT-DOWN (Col16)
                #inchdia = "0" if weldtype == "SP" else row[6].strip()  # Weld->NOMINAL SIZE (Col7) if WeldType != SP
                #sspoolno = row[4].strip() 
                sspoolno = normalize_spoolno(row[4].strip())  # Weld->SPOOL NO (Col5)
                # print(" inchdia ###2 ",inchdia)
                weldrepno = ""  # Assuming blank or add logic if needed
                cpartnoa = row[14].strip()  # Weld->GROUP-UP (Col15)
                cpartnob = row[16].strip()  #     
                # Enrich with materials from the mapping
                materials = service_class_mapping.get(weld_class, " ")


                # Append the enriched row
                weld_data.append({
                    "isono": isono,
                    "spoolno": spoolno,
                    "weld_no": weld_no,
                    "branchdia": branchdia,
                    "class": weld_class,
                    "cfabrevno": "",  # Assuming blank or add logic if needed
                    "csheetnumber": csheetnumber,
                    "cpreviousmaterial": cpreviousmaterial,
                    "cnextmaterial": cnextmaterial,
                    "inchdia": inchdia,
                    "sspoolno": sspoolno,
                    "weldrepno": weldrepno,
                    "weldtype": weldtype,
                    "cpartnoa": cpartnoa,
                    "cpartnob": cpartnob,
                    "dim": "O",  #default value
                    "materials": materials, 
                    #"thickness": thickness,
                   # "schedule": schedule,
                })
    # perfact upto here  print("weld_data ###",weld_data)            
    return weld_data



def write_pmsjnth_csv(output_file, weld_data):
    """
    Write processed weld data to the PMSJNTH CSV file.
    """
    columns = [
        "isono","spoolno","weld_no","branchdia","class","cservice","crevno","cfabrevno","csheetnumber","cdiscipline","cpreviousclass",
        "cnextclass","cpreviousmaterial","cnextmaterial","cpreviousheatno","cnextheatno","cpreviousshedule","cnextschedule",
        "comments","dim","espoolno","fitupdt","fitupinsp","fituprep","fitupreq","fitupreqdt","harddt","hardinsp","hardness",
        "hardreq","hardreqdt","htdt","htinsp","htrep","htreq","htreqdt","inchdia",
        "thickness","materials","mpdt","mpinsp","mp_pt_rep","mpreq","mpreqdt","paintdate","paintinsp","paintrep",
        "paintreq","paintreqdt","pmidt","pmiinsp","pmirep","pmireq","pmireqdt","ptdt","ptinsp","pt_rep","ptreq","ptreqdt","pwht1",
        "pwht1dt","pwht1insp","pwhtreq","pwhtreqdt","pwht2","pwht2dt","pwht2insp","rework","reworkdt","reworkno","reworkrep",
        "rewrkreq","rewrkreqdt","rt1","rt1dt","rt1insp","rtreq","rtreqdt","rt2","rt2dt","rt2insp","rt2req","rt2reqdt","rt3","rt3dt","rt3insp",
        "rt3req","rt3reqdt","rtdone","rtpassed","rtr","schedule","sspoolno","utdt","utinsp","utrep",
        "utreq","utreqdt","visual","visualdt","visualinsp","visualreq","visreqdt","welddate","weldinsp","weldrepno",
        "weldtype","wps","celectrode1","celectrode2","celectrode3","celectrode4","fnrep","fndt","fninsp","fnreq","fnreqdt",
        "sortfld1","sortfld2","stagno","etagno","xcoord","ycoord","zcoord",
        "remarks","dcreated","ccreatedby","dmodified","cmodifiedby","lrt1passed","lmppassed","lrt2passed",
        "lrt3passed","lptpassed","lpmipassed","lfituppassed","lpaintpassed","lpwhtpassed","lpwht2passed","lhardpassed",
        "lhtpassed","lfnpassed","lutpassed","cpartnoa","cpartnob","cidenttypea","cidenttypeb","celectrodebatch1","celectrodebatch2",
        "celectrodebatch3","celectrodebatch4","lvisualpassed","npreheattemp","cjointstatus","cprojectcode","docno","cattachedfile",
        "cattachedfile_content_type","cleanliness_date","deleted","deleted_by","delete_date","delete_reason"

    ]
    # Remove duplicates based on unique keys: isono + spoolno + weld_no
    unique_data = remove_duplicates(weld_data, key_fields=["isono","spoolno", "weld_no"])
    # perfact for inchdia print(" unique_data ###",unique_data)  

    with open(output_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(unique_data)


#  Remove duplicate records based on the unique key fields.

def remove_duplicates(data, key_fields):
    
    seen_keys = set()
    unique_data = []
    for row in data:
        key = tuple(row[field] for field in key_fields)
        if key not in seen_keys:
            seen_keys.add(key)
            unique_data.append(row)
    return unique_data

# def load_service_class_to_material_mapping(pilewall_xlsx):
#     pilewall_data = pd.read_excel(pilewall_xlsx, sheet_name='Reference')
#     #pilewall_data = pd.read_excel(pilewall_xlsx)
#     # Create a dictionary mapping Service Class -> Material
#     mapping = dict(zip(pilewall_data["Service Class"], pilewall_data["Materials"]))
#
#     return mapping
#

#Service Class -> Nominal Pipe Size -> Thickness, Schedule
def load_service_class_to_mapping(pilewall_xlsx):
   
    # Read the reference file
    pilewall_data = pd.read_excel(pilewall_xlsx, sheet_name='Reference')

    # Create a nested dictionary
    mapping = dict(zip(pilewall_data["Service Class"], pilewall_data["Materials"]))

    #print("Mapping in load fun: ",mapping) 
    return mapping

    
def process_pmsjnth_files(extracted_folders, output_csv, pilewall_xlsx):
    """
    Process extracted folders to parse weld.txt and generate PMSJNTH CSV.
    """
    service_class_mapping = load_service_class_to_mapping(pilewall_xlsx)
    #print("Service Class Mapping Loaded::", service_class_mapping)
    
    all_weld_data = []

    for folder in extracted_folders:
        weld_file = find_file_by_partial_name(folder, "Weld.txt")
        if not weld_file:
            print(f"Missing Weld.txt in {folder}. Skipping...")
            continue

        try:
            weld_data = parse_weld_file_for_pmsjnth(weld_file, service_class_mapping)
            all_weld_data.extend(weld_data)
            #print("weld_no## ",weld_data) all good
            # perfact here for inchdia print("weld_data ###",weld_data)
        except Exception as e:
            print(f"Error processing Weld.txt in {folder}: {e}")

    # Write all data to the output CSV
    write_pmsjnth_csv(output_csv, all_weld_data)
    # Enrich pmsjnth.csv with pilewall.xlsx data
   # enrich_pmsjnth_with_pilewall(output_csv, pilewall_xlsx, output_csv)

    #print(f"Final enriched PMSJNTH.csv written to {output_csv}")


def find_file_by_partial_name(folder, partial_name):
    """
    Find a file by partial name in the specified folder, handling nested directories.
    """
    print(f"Searching for '{partial_name}' in folder: {folder}")
    for root, _, files in os.walk(folder):
        for file in files:
            #print(f"Checking file: {file}")
            if partial_name.lower() in file.lower():
                print(f"File found: {os.path.join(root, file)}")
                return os.path.join(root, file)
    print(f"No file found with partial name '{partial_name}' in folder: {folder}")
    return None


#enrich_pmsjnth_with_reference
def enrich_pmsjnth_with_pilewall(pmsjnth_csv, pilewall_xlsx):
    # Load data
    #pmsjnth_df = pd.read_csv(pmsjnth_csv)
    pmsjnth_df = pd.read_csv(pmsjnth_csv, dtype={'weld_no': str})
    # issue here for weld_no
    print("pmsjnth_df ###",pmsjnth_df)
    pilewall_df = pd.read_excel(pilewall_xlsx, sheet_name='Reference')

    # Normalize column names
    pilewall_df.columns = pilewall_df.columns.str.strip().str.lower().str.replace(' ', '_')
    pmsjnth_df.columns = pmsjnth_df.columns.str.strip().str.lower()
    
    

    # Normalize and align key columns
    pilewall_df['service_class'] = pilewall_df['service_class'].astype(str).str.strip().str.upper()
    pilewall_df['nominal_pipe_size'] = pilewall_df['nominal_pipe_size'].astype(str).apply(convert_nominal_size)

    pmsjnth_df['class'] = pmsjnth_df['class'].astype(str).str.strip().str.upper()
    pmsjnth_df['inchdia'] = pmsjnth_df['inchdia'].astype(str).apply(convert_nominal_size)

    # Debugging: Check normalized values
    #print("Normalized inchdia (pmsjnth_df):", pmsjnth_df['inchdia'].unique())
    #print("Normalized nominal_pipe_size (pilewall_df):", pilewall_df['nominal_pipe_size'].unique())

    # Merge for thickness
    thickness_merged_df = pd.merge(
        pmsjnth_df,
        pilewall_df[['service_class', 'nominal_pipe_size', 'wall_thickness']],
        how='left',
        left_on=['class', 'inchdia'],
        right_on=['service_class', 'nominal_pipe_size']
    )
    
     # Replace "-" with blank in wall_thickness  ::06May
    thickness_merged_df['wall_thickness'] = thickness_merged_df['wall_thickness'].replace('-', 0)
    # Replace NaN wall thickness with 0  ::28Jan
    thickness_merged_df['wall_thickness'] = thickness_merged_df['wall_thickness'].fillna(0)
    
    # Handle unmatched rows for thickness
    #unmatched_thickness = thickness_merged_df[thickness_merged_df['wall_thickness'].isna()]
    unmatched_thickness = thickness_merged_df[thickness_merged_df['wall_thickness'] == 0]
    print("Unmatched rows for thickness now fill with 0 instead blank:", unmatched_thickness[['class', 'inchdia']])

    thickness_merged_df['thickness'] = thickness_merged_df['wall_thickness']
    thickness_merged_df = thickness_merged_df.drop(columns=['service_class', 'nominal_pipe_size', 'wall_thickness'])

    # Merge for schedule
    schedule_merged_df = pd.merge(
        thickness_merged_df,
        pilewall_df[['service_class', 'nominal_pipe_size', 'schedule']],
        how='left',
        left_on=['class', 'inchdia'],
        right_on=['service_class', 'nominal_pipe_size'],
        indicator=True
    )

    # Handle unmatched rows for schedule
    unmatched_schedule = schedule_merged_df[schedule_merged_df['_merge'] != 'both']
    #debugger statement
    #print("Unmatched rows for schedule:", unmatched_schedule[['class', 'inchdia']])

    # Assign schedule and clean up
    schedule_merged_df['schedule'] = schedule_merged_df['schedule_y']
    schedule_merged_df = schedule_merged_df.drop(columns=['service_class', 'nominal_pipe_size', '_merge', 'schedule_x', 'schedule_y'])
    #pmsjnth_df['inchdia'] = pmsjnth_df['inchdia'].astype(str).apply(convert_nominal_size)

    desired_columns = [
        "isono", "spoolno", "weld_no", "branchdia", "class", "cservice", "crevno", "cfabrevno", "csheetnumber",
        "cdiscipline", "cpreviousclass", "cnextclass", "cpreviousmaterial", "cnextmaterial", "cpreviousheatno",
        "cnextheatno", "cpreviousshedule", "cnextschedule", "comments", "dim", "espoolno", "fitupdt", "fitupinsp",
        "fituprep", "fitupreq", "fitupreqdt", "harddt", "hardinsp", "hardness", "hardreq", "hardreqdt", "htdt",
        "htinsp", "htrep", "htreq", "htreqdt", "inchdia", "thickness", "materials", "mpdt", "mpinsp", "mp_pt_rep",
        "mpreq", "mpreqdt", "paintdate", "paintinsp", "paintrep", "paintreq", "paintreqdt", "pmidt", "pmiinsp",
        "pmirep", "pmireq", "pmireqdt", "ptdt", "ptinsp", "pt_rep", "ptreq", "ptreqdt", "pwht1", "pwht1dt", "pwht1insp",
        "pwhtreq", "pwhtreqdt", "pwht2", "pwht2dt", "pwht2insp", "rework", "reworkdt", "reworkno", "reworkrep",
        "rewrkreq", "rewrkreqdt", "rt1", "rt1dt", "rt1insp", "rtreq", "rtreqdt", "rt2", "rt2dt", "rt2insp", "rt2req",
        "rt2reqdt", "rt3", "rt3dt", "rt3insp", "rt3req", "rt3reqdt", "rtdone", "rtpassed", "rtr", "schedule", "sspoolno",
        "utdt", "utinsp", "utrep", "utreq", "utreqdt", "visual", "visualdt", "visualinsp", "visualreq", "visreqdt",
        "welddate", "weldinsp", "weldrepno", "weldtype", "wps", "celectrode1", "celectrode2", "celectrode3",
        "celectrode4", "fnrep", "fndt", "fninsp", "fnreq", "fnreqdt", "sortfld1", "sortfld2", "stagno", "etagno",
        "xcoord", "ycoord", "zcoord", "remarks", "dcreated", "ccreatedby", "dmodified", "cmodifiedby", "lrt1passed",
        "lmppassed", "lrt2passed", "lrt3passed", "lptpassed", "lpmipassed", "lfituppassed", "lpaintpassed", "lpwhtpassed",
        "lpwht2passed", "lhardpassed", "lhtpassed", "lfnpassed", "lutpassed", "cpartnoa", "cpartnob", "cidenttypea",
        "cidenttypeb", "celectrodebatch1", "celectrodebatch2", "celectrodebatch3", "celectrodebatch4",
        "lvisualpassed", "npreheattemp", "cjointstatus", "cprojectcode", "docno", "cattachedfile",
        "cattachedfile_content_type", "cleanliness_date", "deleted", "deleted_by", "delete_date", "delete_reason"
    ]
    #pmsjnth_df['inchdia'] = pmsjnth_df['inchdia'].astype(str).apply(convert_nominal_size)
    schedule_merged_df = schedule_merged_df.reindex(columns=desired_columns)
    
    # schedule_merged_df['inchdia'] = schedule_merged_df['inchdia'].apply(
    # lambda x: int(x) if isinstance(x, (int, float)) and x.is_integer() else x
    # )
    
    enriched_csv_path = "D:/ismometricFiles/FeedFiles/Output_PMSJNTH.csv"  
    
    schedule_merged_df.to_csv(enriched_csv_path, index=False)
    print(f"Enriched data saved to: {enriched_csv_path}")
    
    
       
    return enriched_csv_path

