import os
import csv
import re
from pmsisod import calculate_matsubcode, parse_fraction


def parse_mat_file(file_path):
    """
    Parse the Mat.txt file and ensure matcode is trimmed and validated.
    """
    mat_data = []
    fields = [
        (290, 355),  # Ident Code (matcode)
        (445, 745),  # Material Description (matdesc2, matdesc1)
        (245, 290),  # Size (Col10)
        (370, 374),  # Unit (Col13)
        (375, 405),  # Commodity Code (part, Col14)
    ]

    with open(file_path, 'r') as file:
        for line_no, line in enumerate(file, start=1):
            try:
                # Extract matcode and trim spaces
                matcode = line[fields[0][0]:fields[0][1]].strip()
                
                # Skip invalid matcodes
                if not matcode or matcode.upper() == "SPOOL-TAG":
                    #print(f"Skipping invalid matcode at line {line_no}")
                    continue

                # Debugging: Print extracted matcode
                print(f"Line {line_no} - Matcode: [{matcode}]")

                # Extract other fields
                matdesc1 = line[fields[1][0]:fields[1][1]].strip()  # Material Description
                matdesc2 = matdesc1  # Same as Material Description
                
                size = line[fields[2][0]:fields[2][1]].strip()
                #print("size ###",size)
                unit_raw = line[fields[3][0]:fields[3][1]].strip()
                commodity = line[fields[4][0]:fields[4][1]].strip()
                part = line[fields[4][0]:fields[4][1]].strip()  # Commodity Code (Col14)
                
                #matcattype = line[fields[4][0]:fields[4][1]].strip()  # Commodity Code (Col14)

                # Extract  the value of matcattype based on the part value.
                if part.upper() == "PIPE":
                    matcattypeCond = "PIPE"
                elif part.upper() == "FITTINGS":
                    matcattypeCond = "FITTING"
                else:
                    matcattypeCond = " "  # Blank for other part
  
                # Use calculate_matsubcode() to process size
                matsubcode = calculate_matsubcode(size)
                #print("matsubcode#####",matsubcode)
                if "X" in size:
                    # Handle cases like "3/4X1/2" or "130X3/4"
                    left, right = size.split("X")
                    lsize = str(parse_fraction(left.strip()))
                    ssize = str(parse_fraction(right.strip()))
                elif "/" in size:
                    # Handle single fraction like "3/4"
                    lsize = str(parse_fraction(size))
                    ssize = "0"
                else:
                    # Handle simple numbers like "130"
                    lsize = size.strip()
                    ssize = "0"

                # Debugging: Print the size, lsize, ssize, and matsubcode
                print(f"Line {line_no} - size: {size}, lsize: {lsize}, ssize: {ssize}, matsubcode: {matsubcode},Matcode: [{matcode} ")

                
            # Added for ssize if part = 'BOLTS' and 'Length' is in matdesc2
            # Finds the first numeric value followed by mm
                
                if part.upper() == "BOLTS" and "Length" in matdesc2:
                    try:
                    # Use regex to extract any numeric value followed by "mm"
                        match = re.search(r"(\d+)\s*mm", matdesc2)
                        if match:
                            ssize = match.group(1)  # Extracted length
                        else:
                            ssize = 0
                            print(f"No length found in matdesc2: {matdesc2}")
                    except Exception as e:
                        print(f"Error extracting length from matdesc2: {matdesc2}, Error: {e}")
                        
            
            
            
            
                # if part.upper() == "BOLTS" and "Length =" in matdesc2:
                #     try:
                #     # Extract the length value from matdesc2
                #         length_start = matdesc2.index("Length =") + len("Length =")
                #         length_end = matdesc2.index("mm", length_start)
                #         extracted_length = matdesc2[length_start:length_end].strip()
                #         ssize = extracted_length  # Update ssize with the extracted length
                #     except ValueError:
                #         print(f"Error extracting length from matdesc2: {matdesc2}")
                
            # Populate unit based on Col13 and Col14
                if commodity.strip().upper() == "PIPE":
                    unit = "M"
                else:
                    unit = "EA"


                # Append parsed data
                mat_data.append({
                    "matcode": matcode,
                    "matdesc2": matdesc2,
                    "matsubcode": matsubcode.strip(),
                    "lsize": lsize,
                    "matdesc1": matdesc1,
                    "part": commodity,
                    "ssize": ssize,
                    "unit": unit,
                    "source": "P",
                    "matrevno": 0,
                    "rec": 0,
                    "acode": None,
                    "action": None,
                    "area": None,
                    "class": None,
                    "disc": None,
                    "estcode": None,
                    "insured": None,
                    "lupdate": None,
                    "matallow": None,
                    "npcccode": None,
                    "owner": None,
                    "qaqcinsp": None,
                    "qtybom": None,
                    "qtybomo": None,
                    "remarks": None,
                    "revdate": None,
                    "schedule": None,
                    "schedule2": None,
                    "sno": None,
                    "uprice": None,
                    "weight": None,
                    "weightage": None,
                    "rating": None,
                    "matcat": None,
                    "matcattype": matcattypeCond,
                    "manufcode": None,
                    "image": None,
                    "status": None,
                    "lactive": "TRUE",
                    "dcreated": None,
                    "ccreatedby": None,
                    "dmodified": None,
                    "cmodifiedby": None,
                    "ndepreciationrate": None,
                    "docno": None,
                    "cattachedfile": None,
                    "ladditionalpayment": None,
                    "cntr": None,
                    "cimagebinary": None,
                    "cimagebinary_content_type": None,
                    "cmaterialcategory": None,
                    "cfilebase64": None,
                    "cfilebase_64_content_type": None,
                    "cfileextension": None,
                    "cfilename": None,
                    "cprojectcode": None,
                    "type": None,
                    "grade": None,
                    "commodity": None,
                    "uprice": "",  # Default
                })
            except Exception as e:
                print(f"Error on line {line_no}: {e} - {line.strip()}")
    return mat_data


def write_pmsmat_csv(output_file, mat_data):
    """
    Write processed Mat data to PMSMAT.csv.
    """
    columns = [
        "matcode","matdesc2","source","matsubcode","matrevno","rec","acode","action","area","class","disc",
        "estcode","insured","lsize","lupdate","matallow","matdesc1","npcccode","owner","part","qaqcinsp",
        "qtybom","qtybomo","remarks","revdate","schedule","schedule2","sno","ssize","unit","uprice","weight",
        "weightage","rating","matcat","matcattype","manufcode","image","status","lactive","dcreated","ccreatedby",
        "dmodified","cmodifiedby","ndepreciationrate","docno","cattachedfile","ladditionalpayment","cntr","cimagebinary",
        "cimagebinary_content_type","cmaterialcategory","cfilebase64","cfilebase_64_content_type","cfileextension",
        "cfilename","cprojectcode","type","grade","commodity"

    ]
    # Remove duplicate records based on unique keys (matcode + matsubcode)
    unique_data = remove_duplicates(mat_data, key_fields=["matcode", "matsubcode"])

    with open(output_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(unique_data)


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


def process_pmsmat_files(extracted_folders, output_csv):
    """
    Process extracted folders to parse Mat.txt and generate PMSMAT.csv.
    """
    all_mat_data = []

    for folder in extracted_folders:
        mat_file = find_file_by_partial_name(folder, "Mat.txt")
        if not mat_file:
            print(f"Missing Mat.txt in {folder}. Skipping...")
            continue

        try:
            mat_data = parse_mat_file(mat_file)
            all_mat_data.extend(mat_data)
        except Exception as e:
            print(f"Error processing Mat.txt in {folder}: {e}")

    # Write all data to the output CSV
    write_pmsmat_csv(output_csv, all_mat_data)


def find_file_by_partial_name(folder, partial_name):
    """
    Find a file by partial name in the specified folder, handling nested directories.
    """
    #print(f"Searching for '{partial_name}' in folder: {folder}")
    for root, _, files in os.walk(folder):
        for file in files:
            print(f"Checking file: {file}")
            if partial_name.lower() in file.lower():
                print(f"File found: {os.path.join(root, file)}")
                return os.path.join(root, file)
    print(f"No file found with partial name '{partial_name}' in folder: {folder}")
    return None
