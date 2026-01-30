import csv
import os
from collections import defaultdict
from fractions import Fraction
from datetime import datetime

# Helper functions
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
            return float(value)
    except (ValueError, ZeroDivisionError) as e:
        print(f"Warning: Invalid nominal size value '{value}' encountered. Error: {e}")
        return 0


def determine_spool_type(row):
    """
    Determine the spool_type based on conditions.
    """
    nojoint = int(row.get("nojoint", 0))
    nfieldinchdia = float(row.get("nfieldinchdia", 0))
    inchdia = float(row.get("inchdia", 0))
    spoolno = row.get("spoolno", "").strip()

    if nojoint > 0:
        return "SHOP"
    elif nfieldinchdia > 0 and inchdia == 0 and nojoint == 0:
        return "FIELD RUN"
    elif spoolno.startswith("F") and spoolno not in ["FI", "FV"]:
        return "ERECTION"
    elif spoolno.startswith("FI"):
        return "INSTRUMENT"
    elif spoolno.startswith("FV"):
        return "VALVE"
    else:
        return ""  # Default case


def normalize_spoolno(spoolno):
    """
    Normalize the spool number based on the given conditions:
    1) If spool number is blank, update it to 'F01'.
    2) If spool number has an exact match with 'SP0', change it to 'F01'.
    3) If spool number is exactly 'SP000', change it to 'F01'.
    4) All other spool numbers remain unchanged.
    """
    if not spoolno or spoolno.strip() == "":  # Condition 1: Blank spool number
        return "F01"
    elif spoolno.strip().upper() == "SP0":  # Condition 2: Exact match with 'SP0'
        return "F01"
    elif spoolno.strip().upper() == "SP000":  # Condition 3: Exactly 'SP000'
        return "F01"
    else:  # Return the cleaned spool number if no condition matches
        return spoolno.strip()

    

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

def parse_mat_file(file_path):
    mat_data = []
    fields = [
        (140, 210),  # Isometric No.
        (235, 245),  # Spool No.
        (215, 235),  # Piping Class
    ]
    with open(file_path, 'r') as file:
        for line in file:
            isono = line[fields[0][0]:fields[0][1]].strip()
            spoolno = normalize_spoolno(line[fields[1][0]:fields[1][1]].strip()) 
            #print(" spoolno### ",spoolno)
            #spoolno = line[fields[1][0]:fields[1][1]].strip()
            cclass = line[fields[2][0]:fields[2][1]].strip()
            mat_data.append({"isono": isono, "spoolno": spoolno, "cclass": cclass})
    return mat_data

def parse_mtc_file(file_path):
    mtc_data = []
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) >= 7:
                mtc_data.append({
                    "isono": row[0].strip(),
                    "spoolno": normalize_spoolno(row[2].strip()),
                    #"spoolno": row[2].strip(),
                    "surfarea": row[5].strip(),
                    "inchmtr": row[4].strip(),
                    "lenmtr": row[3].strip(),
                    "cspoolvolume": row[6].strip(),
                })
    return mtc_data

def parse_weld_file(file_path):
    weld_data = defaultdict(lambda: {"inchdia": 0, "nfieldinchdia": 0, "nojoint": 0})
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) >= 8:
                key = (row[0].strip(), row[4].strip())  # isono + spoolno
                nominal_size = convert_nominal_size(row[6].strip())
                if row[7].strip() == "S":  # Weld category
                    weld_data[key]["inchdia"] += nominal_size
                    weld_data[key]["nojoint"] += 1
                elif row[7].strip() == "F":
                    weld_data[key]["nfieldinchdia"] += nominal_size
    return weld_data


def merge_data_with_weld(mat_data, mtc_data, weld_data):
    merged_data = []
    seen_keys = set()

    for mat_row in mat_data:
        key = (mat_row["isono"], mat_row["spoolno"])
        if key in seen_keys:
            continue  # Skip duplicates
        seen_keys.add(key)

        weld_info = weld_data.get(key, {"inchdia": 0, "nfieldinchdia": 0, "nojoint": 0})
        matching_mtc_rows = [
            mtc_row for mtc_row in mtc_data
            if mtc_row["isono"] == mat_row["isono"] and mtc_row["spoolno"] == mat_row["spoolno"]
        ]

        if matching_mtc_rows:
            for mtc_row in matching_mtc_rows:
                merged_data.append({**mat_row, **mtc_row, **weld_info})
        else:
            merged_data.append({**mat_row, **weld_info, "surfarea": "", "inchmtr": "", "lenmtr": "", "cspoolvolume": ""})
    #print(f"Merging data for key: {key}, Weld Info: {weld_info}")
        
    return merged_data



def write_csv(output_file, data):
    columns = [
        "isono","spoolno","action","activity","binno","bscode","cubicft","crevno","fabrevno","inchdia",
        "nshopinchdia","nfieldinchdia","insul","ninsulationthickness","loadoutno","lupdate","nojoint",
        "owner","paint","paintrel","presser","priority","progcode","proglo","progndt","progpaint","progpct1","progpct2",
        "progpwht","rework","splrelnote","splweight","spoolhold","status","statusdt1","statusdt2","statusdt3",
        "statusdt4","step","surfarea","system","targetdt","testpackdt","testpackno","flag","clineno","cclass",
        "rffno","inchmtr","lenmtr","modelbase","cpreviousspoolname","cspoolvolume","cspoolservice","dcreated",
        "ccreatedby","dmodified","cmodifiedby","cprojectcode","spool_type","deleted","deleted_by","delete_date","delete_reason"
    ]
    with open(output_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(data)

def process_pmsspl_files(extracted_folders, output_csv, output_pcf_csv, output_pmsisod_csv):
    """
    Process PMSSPL files, enrich data with progpaint and clineno, and write to CSV.
    """
    all_data = []

    # Load PMSISOH and PMSISOD data
    pmsisoh_data = parse_pmsisoh_data(output_pcf_csv)
    pmsisod_data = parse_pmsisod_csv(output_pmsisod_csv)

    for folder in extracted_folders:
        mat_file = find_file_by_partial_name(folder, "Mat.txt")
        mtc_file = find_file_by_partial_name(folder, "Mtc.txt")
        weld_file = find_file_by_partial_name(folder, "Weld.txt")

        if not mat_file or not mtc_file or not weld_file:
            print(f"Missing required files in {folder}")
            continue

        # Parse files
        mat_data = parse_mat_file(mat_file)
        mtc_data = parse_mtc_file(mtc_file)
        new_weld_data = parse_weld_file(weld_file)

        # Debug: Print new weld data
        #print("New Weld Data: ", new_weld_data)

        # Merge only the current folder's weld data
        merged_data = merge_data_with_weld(mat_data, mtc_data, new_weld_data)
        all_data.extend(merged_data)

    # Enrich the merged data with additional fields
    enriched_data = enrich_pmsspl_data(all_data, pmsisoh_data, pmsisod_data)

    # Write enriched data to CSV
    write_csv(output_csv, enriched_data)




    
def parse_pmsisod_csv(file_path):
    """
    Parse PMSISOD CSV to extract matsubcode data.
    """
    pmsisod_data = []
    with open(file_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            pmsisod_data.append({
                "isono": row.get("isono", "").strip(),
                "spoolno": row.get("spoolno", "").strip(),
                "matsubcode": row.get("matsubcode", "").strip(),
            })
    return pmsisod_data    
def enrich_pmsspl_data(merged_data, pmsisoh_data, pmsisod_data):
    """
    Enrich the PMSSPL data with additional fields: progpaint and clineno.
    """
    enriched_data = []

    # Process each record
    for row in merged_data:
        # key = (row["isono"], row["spoolno"])
        key = row["isono"]
        # Add clineno from PMSISOH
        #print("pmsisoh_data ",pmsisoh_data)
        if key in pmsisoh_data:
            row["insul"] = pmsisoh_data[key].get("insul", "")
            row["ninsulationthickness"] = pmsisoh_data[key].get("ninsulationthickness", "")
            #print("ninsulationthickness:: ",row["ninsulationthickness"])
            row["paint"] = pmsisoh_data[key].get("paint", "")
            row["clineno"] = pmsisoh_data[key].get("clineno", "")
            row["status"] = "00"
            today = datetime.now().strftime("%Y-%m-%d")  # Today's date 
            row["statusdt1"] = today

        # Calculate progpaint for spool components
        # spoolno starts with "SP".
        # matsubcode values are only retrieved for rows where both isono and spoolno match the current row.
        # Extracts the first 10 characters from the matsubcode string.
        # Removes any leading or trailing spaces.
        #
        if row["spoolno"].startswith("SP"):
            matsubcodes = [
                entry["matsubcode"][:10].strip()
                for entry in pmsisod_data
                if entry["isono"] == row["isono"] and entry["spoolno"] == row["spoolno"]
            ]
            #print ("anoop:::: ####", matsubcodes)
            row["progpaint"] = max(map(float, matsubcodes), default=0) if matsubcodes else ""
            #priority column shows joint size. Which is not required. 25-12-2004
            row["priority"] = max(map(float, matsubcodes), default=0) if matsubcodes else ""
        
        # Determine spool_type
        row["spool_type"] = determine_spool_type(row)
        
        # Append enriched row
        enriched_data.append(row)

    # Remove duplicates based on isono + spoolno
    return remove_duplicates(enriched_data, key_fields=["isono", "spoolno"])


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
    
def pluggedin_with_pmsisoh(merged_data, pmsisoh_data):
   
    enriched_data = []
    for row in merged_data:
        key = (row["isono"], row["spoolno"])
        pmsisoh_row = pmsisoh_data.get(key, {})

        # Enrich row with PMSISOH fields
        row["insul"] = pmsisoh_row.get("insul", "")
        row["ninsulationthickness"] = pmsisoh_row.get("ninsulationthickness", "")
        row["paint"] = pmsisoh_row.get("paint", "")
        row["progpaint"] = derive_progpaint(row.get("spoolno", ""))
        row["clineno"] = pmsisoh_row.get("clineno", "")
        enriched_data.append(row)
    return enriched_data

def parse_pmsisoh_data(file_path):
    """
    Parse PMSISOH CSV to extract required fields using `isono` as the key.
    """
    pmsisoh_data = {}
    with open(file_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        # Ensure the required columns exist
        required_columns = ["isono", "insul", "ninsulationthickness", "paint", "clineno"]
        for col in required_columns:
            if col not in reader.fieldnames:
                print(f"Error: Missing column '{col}' in PMSISOH CSV file.")
                return pmsisoh_data  # Return an empty dictionary

        for row in reader:
            isono = row.get("isono", "").strip()
            if isono:
                pmsisoh_data[isono] = {
                    "insul": row.get("insul", "").strip(),
                    "ninsulationthickness": row.get("ninsulationthickness", "").strip(),
                    "paint": row.get("paint", "").strip(),
                    "clineno": row.get("clineno", "").strip(),
                }
    #print("pmsisoh_data 30Nov",pmsisoh_data)             
    return pmsisoh_data

def parse_pmsisoh_data1(file_path):
    """
    Parse the PMSISOH CSV file to extract mappings for PMSISOH fields.
    """
    pmsisoh_data = {}
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Ensure required columns exist in the input file
                if "isono" in row in row:
                    key = (row["isono"].strip())
                    pmsisoh_data[key] = {
                        "insul": row.get("insul", "").strip(),
                        "ninsulationthickness": row.get("ninsulationthickness", "").strip(),
                        "paint": row.get("paint", "").strip(),
                        "clineno": row.get("clineno", "").strip(),
                    }
    except Exception as e:
        print(f"Error parsing PMSISOH data from {file_path}: {e}")
        
    #print("pmsisoh_data ",pmsisoh_data)    
    return pmsisoh_data


def derive_progpaint(spoolno):
    """
    Derive progpaint based on spool number.
    """
    if spoolno.startswith("SP"):
        try:
            size = int(spoolno[2:])
            if size < 50:
                return "Small"
            elif size < 100:
                return "Medium"
            else:
                return "Large"
        except ValueError:
            pass
    return "Unknown"   
