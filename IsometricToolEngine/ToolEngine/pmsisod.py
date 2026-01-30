import os
import csv
from datetime import datetime
from collections import defaultdict
from fractions import Fraction
from utils.NotificationScript import send_email_notification
# this script for non-pipe functionality.


# conditions:
#     1) If spool number is blank, update it to 'F01'.
#     2) If spool number has an exact match with 'SP0', change it to 'F01'.
#     3) If spool number is exactly 'SP000', change it to 'F01'.
#     4) All other spool numbers remain unchanged.

def normalize_spoolno(spoolno):
    
    if not spoolno or spoolno.strip() == "":  # Condition 1
        return "F01"
    elif spoolno.strip().upper() == "SP0":  # Condition 2
        return "F01"
    elif spoolno.strip().upper() == "SP000":  # Condition 3
        return "F01"
    else:  # Return if no condition matches
        return spoolno.strip()



# added for fix lsize issue::24-may
def parse_fraction(value):
    try:
        # Handle mixed fractions like "1.1/2" (meaning 1 and 1/2)
        if '.' in value and '/' in value:
            parts = value.split('.')
            whole_number = int(parts[0]) if parts[0] else 0
            fraction = Fraction(parts[1])
            return whole_number + float(fraction)
        elif '/' in value:
            # Handle simple fractions like "3/4"
            return float(Fraction(value))
        else:
            # Convert value to float or integer
            number = float(value)
            return int(number) if number.is_integer() else number
    except (ValueError, ZeroDivisionError):
        return value.strip()

#    If col10 has a value like "138X10", populate "138       10" (10 characters for the first value, followed by the second).
#    - If col10 has a value like "3/4X1/2", populate "0.75      0.50" (10 characters for the first value, followed by the second).
#    - If col10 has a value like "1.1/8", calculate the correct fraction value and format it.
#    - If col10 has a simple fraction like "3/4", convert it to "0.75".
#    - If col10 has a simple number like "130", keep it as is, padded to 10 characters.
#

def calculate_matsubcode(col10):
    if 'X' in col10:
        # Handle cases like "138X10" or "3/4X1/2"
        parts = col10.split('X')  # Split on 'X'
        processed_parts = []
        for i, part in enumerate(parts):
            # Parse and format each part
            parsed_value = parse_fraction(part)
            if isinstance(parsed_value, float) and parsed_value.is_integer():
                parsed_value = int(parsed_value)  # Convert floats with .0 to integers
            processed_parts.append(str(parsed_value))  # Keep as string

        # Ensure 10 characters for the first value
        return f"{processed_parts[0]:<10}{processed_parts[1]}"
    else:
        # Handle single values
        parsed_value = parse_fraction(col10)
        if isinstance(parsed_value, float) and parsed_value.is_integer():
            parsed_value = int(parsed_value)  # Convert floats with .0 to integers
        return f"{parsed_value:<10}"



# def calculate_matsubcode(col10):
#
#     def parse_fraction(value):
#         try:
#             if '.' in value and '/' in value:
#                     parts = value.split('.')
#                     whole_number = float(parts[0]) if parts[0] else 0
#                     fraction_part = float(Fraction(parts[1]))
#                     return whole_number + fraction_part
#             elif '/' in value:
#                 return float(Fraction(value))
#             else:
#             # Convert value to float or integer
#                 number = float(value)
#                 return int(number) if number.is_integer() else number
#         except ValueError:
#             return value.strip()
#     if 'X' in col10:
#         # Handle cases like "138X10" or "3/4X1/2"
#         parts = col10.split('X')  # Split on 'X'
#         processed_parts = []
#         for i, part in enumerate(parts):
#             # Parse and format each part
#             parsed_value = parse_fraction(part)
#             if isinstance(parsed_value, float) and parsed_value.is_integer():
#                 parsed_value = int(parsed_value)  # Convert floats with .0 to integers
#             processed_parts.append(str(parsed_value))  # Keep as string
#
#         # Ensure 10 characters for the first value
#         return f"{processed_parts[0]:<10}{processed_parts[1]}"
#     else:
#         # Handle single values
#         parsed_value = parse_fraction(col10)
#         if isinstance(parsed_value, float) and parsed_value.is_integer():
#             parsed_value = int(parsed_value)  # Convert floats with .0 to integers
#         return f"{parsed_value:<10}"

#14-Dec:: start

# Seprate the script
#14 dec :: end
#mat file parsing and extraction of required fields.

def parse_mat_file_for_pmsisod(file_path):
   
    mat_data = []
    fields = [
        (40, 80),    # area
        (140, 210),  # isono
        (290, 355),  # Ident Code (matcode)
        (245, 290),  # Size (matsubcode)
        (375, 405),  # Commodity Code (part)
        (355, 370),   #qty now
        (445, 745),  # cmaterialdescription
        (215, 235),  # cmaterialclass
        (235, 245),  # spoolno
        (405, 415),  # Category (discipline)
    ]

    today = datetime.now().strftime("%Y-%m-%d")  # Today's date for 'lupdate'

    with open(file_path, 'r') as file:
        for line in file:
            matcode = line[fields[2][0]:fields[2][1]].strip()  # Ident Code
            print("matcode in isod### ",matcode)
            if matcode.upper() == "SPOOL-TAG":
                continue  # Skip SPOOL-TAG records
            # skip the records that do not have a matcode in the metadata file.   :: 19Jan2026
            if not matcode:
                print(f"We don't have matcode in {file_path}")
                continue
            
            col10 = line[fields[3][0]:fields[3][1]].strip()  # Size
            matsubcode = calculate_matsubcode(col10)
            #print("matsubcode 11 ##",matsubcode)
            
            part = line[fields[4][0]:fields[4][1]].strip()  # Commodity Code
            #print(" part ###",part)
            if part.upper() == "PIPE":
                continue  # Skip PIPE records
            
            qty = line[fields[5][0]:fields[5][1]].strip()  # Quantity
            cmaterialdescription = line[fields[6][0]:fields[6][1]].strip()  # Material Description
            #TBC chnage:: anoop ::22 Dec
            #TBC if cmaterialdescription "90 Elb" do the 
            #part assign to "Elbow"
            
            cmaterialclass = line[fields[7][0]:fields[7][1]].strip()  # Piping Class
            spoolno = normalize_spoolno(line[fields[8][0]:fields[8][1]].strip())  # Apply normalization
            #print("spoolno ###",spoolno)
            discipline = line[fields[9][0]:fields[9][1]].strip()  # Category (discipline)
            trimmed_area = line[fields[0][0]:fields[0][1]].strip()
            if len(trimmed_area) > 7:
                        trimmed_area = trimmed_area[:7]
            #requirement for pipe support
            if part.upper() == "PIPE SUPPORTS" :
                trace = "S"
            else:
                trace = ""      # default Value
               
            
                    
            mat_data.append({
                "area": trimmed_area,  # Design Area
                "isono": line[fields[1][0]:fields[1][1]].strip(),  # Isometric No.
                "lupdate": today,
                "matcode": matcode,
                "matsubcode": matsubcode.strip(),
                "paint": "",  # Placeholder; will be linked later
                "part": part,
                "qty": qty,
                "source": "P",  #default Value
                "spoolno": spoolno,
                "trace": trace, 
                "discipline": discipline,
                "clineno": "",  # Placeholder; 
                "sheetno": "",  # Placeholder; 
                "itemno": "",  # Placeholder; calculated field
                "cmaterialclass": cmaterialclass,
                "cmaterialdescription": cmaterialdescription,
            })
    #print("mat_data ###",mat_data)        
    return mat_data


def assign_additional_fields(mat_data, pmsisoh_data, pmsjnth_data):
    enriched_data = []

    grouped_data = defaultdict(list)
    for row in mat_data:
        grouped_data[row["isono"]].append(row)

    for isono, rows in grouped_data.items():
        # Sort rows by any criteria if necessary (e.g., by `spoolno` or `matcode`)
        # rows.sort(key=lambda x: x['spoolno'])  # Uncomment if sorting by spoolno is required

        # Assign sequential ItemNo for each row in the group
        for index, row in enumerate(rows, start=1):
            row["itemno"] = index

            # Find matching PMSISOH data for the current row
            matching_pmsisoh = next(
                (item for item in pmsisoh_data if item["isono"] == row["isono"]),
                {}
            )

            # Find matching PMSJNTH data for the current row
            matching_pmsjnth = next(
                (item for item in pmsjnth_data if item["isono"] == row["isono"] and item["sspoolno"] == row["spoolno"]),
                {}
            )

            # Add additional fields from PMSISOH
            row["paint"] = matching_pmsisoh.get("paint", "")
            row["clineno"] = matching_pmsisoh.get("clineno", "")

            # Add additional fields from PMSJNTH
            #print("matching_pmsjnth sheetNum::",matching_pmsjnth.get("csheetnumber", ""))
            row["sheetno"] = matching_pmsjnth.get("csheetnumber", "")

            enriched_data.append(row)

    return enriched_data



def write_pmsisod_csv(output_file, enriched_data):
    """
    Write the enriched PMSISOD data to a CSV file.
    """
    columns = [
        "action","activity","area","bscode","chgflag","isono","crevno","cfabrevno",
        "lengthmto","lupdate","mark","matcode","matsubcode","matrevno","owner","paint",
        "part","prevqty","progcode","progpct1","qty","qtymto","remark","scontcode","source",
        "spoolno","status","step","subarea","targetdt","trace","discipline","clineno",
        "sheetno","itemno","dmrs","tagno","cmaterialclass","cmmsize","cinchsize","cmaterialdescription",
        "cvolume","cequipmentno","cattachedspool","dcreated","ccreatedby","dmodified","cmodifiedby",
        "docno","cprojectcode","deleted","deleted_by","delete_date","delete_reason"

    ]

    with open(output_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(enriched_data)

#Process extracted folders to parse Mat.txt and generate PMSISOD.csv.
def process_pmsisod_files(extracted_folders, output_csv, pmsisoh_data, pmsjnth_data):
    
    all_mat_data = []
    subject = "Notification for missing metadata File.!!!"
    body = """
    <html>
        <body>
            <p> Dear Team,</p>
            <p>Feed file (Mat.txt) is missing.</p>
            
            <p> Thanks, </p>
            <p> Talisman Team </p>
        </body>
    </html>
    """
    
    # added file specific validation :: 13-May
    for folder in extracted_folders:
        mat_file = find_file_by_partial_name(folder, "Mat.txt")
        if not mat_file:
            print(f"Missing Mat.txt in {folder}. Skipping...")
            send_email_notification(subject, body)
            continue

        try:
            mat_data = parse_mat_file_for_pmsisod(mat_file)
            all_mat_data.extend(mat_data)
        except Exception as e:
            print(f"Error processing Mat.txt in {folder}: {e}")

    # Assign additional fields based on PMSISOH and PMSJNTH mappings
    enriched_data = assign_additional_fields(all_mat_data, pmsisoh_data, pmsjnth_data)

    # Write all enriched data to the output CSV
    write_pmsisod_csv(output_csv, enriched_data)

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
