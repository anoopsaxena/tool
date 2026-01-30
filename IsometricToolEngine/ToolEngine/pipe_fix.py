import os
import csv
from datetime import datetime
from fractions import Fraction
from collections import defaultdict



def normalize_spoolno(spoolno):
    """
    Normalize the spool number based on the given conditions:
    1) If spool number is blank, update it to 'F01'.
    2) If spool number has an exact match with 'SP0', change it to 'F01'.
    3) If spool number is exactly '', change it to 'F01'.
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
    

def parse_cutlist_file(cutlist_path):
    """
    Parse the Cutlist.txt file and store multiple rows per (isono, spoolno) key.
    """
    cutlist_data = defaultdict(list)  # Use a list to hold multiple rows for the same key

    with open(cutlist_path, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) < 10:  # Ensure sufficient columns
                continue

            isono = row[0].strip()
            spoolno = normalize_spoolno(row[3].strip())
            #print("normal pipe###",spoolno)
            cutlist_data[(isono, spoolno)].append({
                "matcode": row[6].strip(),
                "matsubcode": row[7].strip(),
                "qty": float(row[5].strip()) / 1000,  # Convert quantity to float and divide by 1000
                "sheetno": row[1].strip(),  # Sheet Number
                "itemno": row[4].strip(),  # Cut Pipe Piece Number
                "cmaterialclass": row[9].strip(),  # Piping Class
                "cmaterialdescription": row[8].strip(),  # Material Description
            })
    return cutlist_data


def calculate_matsubcode(col10):
    """
    Process and format the matsubcode field. Converts fractions and handles special cases.
    """
    def parse_fraction(value):
        try:
            if '.' in value and '/' in value:
                parts = value.split('.')
                whole_number = float(parts[0]) if parts[0] else 0
                fraction_part = float(Fraction(parts[1]))
                return whole_number + fraction_part
            elif '/' in value:
                return float(Fraction(value))
            else:
                # Convert value to float or integer
                number = float(value)
                return int(number) if number.is_integer() else number
        except ValueError:
            return value.strip()

    if 'X' in col10:
        parts = col10.split('X')
        processed_parts = [str(parse_fraction(part)) for part in parts]
        return f"{processed_parts[0]:<10}{processed_parts[1]}"
    else:
        parsed_value = parse_fraction(col10)
        # Convert float to integer if possible
        if isinstance(parsed_value, float) and parsed_value.is_integer():
            parsed_value = int(parsed_value)
        return f"{parsed_value:<10}"


def parse_mat_file_for_pipe(mat_file_path, cutlist_path, pmsisoh_data):
    """
    Parse the Mat.txt file to extract PIPE parts and merge data from Cutlist.txt and PMSISOH.
    """
    # Load Cutlist data
    cutlist_data = parse_cutlist_file(cutlist_path)

    pipe_data = []
    processed_spoolnos = set()  # To track processed (isono, spoolno) pairs
    today = datetime.now().strftime("%Y-%m-%d")

    with open(mat_file_path, 'r') as file:
        for line in file:
            isono = line[140:210].strip()
            spoolno = normalize_spoolno(line[235:245].strip())
            #print("spoolnoPart2 ###",spoolno)
            part = line[375:405].strip()

            if part.upper() != "PIPE":
                continue

            key = (isono, spoolno)

            # Skip if already processed to prevent duplicates
            if key in processed_spoolnos:
                continue

            processed_spoolnos.add(key)  # Mark as processed for this iteration
            matching_pmsisoh = next(
                        (item for item in pmsisoh_data if item["isono"] == isono),
                            {}
                        )
            if key in cutlist_data:
                for cutlist_entry in cutlist_data[key]:  # Iterate over cutlist data
                    pipe_data.append({
                        "area": matching_pmsisoh.get("area", ""),
                        "isono": isono,
                        "spoolno": spoolno,
                        "matcode": cutlist_entry["matcode"],
                        "matsubcode": calculate_matsubcode(cutlist_entry["matsubcode"]).strip(),
                        "qty": cutlist_entry["qty"],
                        "paint": matching_pmsisoh.get("paint", ""),
                        "source": "P",
                        "part": "PIPE",
                        "sheetno": cutlist_entry["sheetno"],
                        "itemno": cutlist_entry["itemno"],
                        "clineno": matching_pmsisoh.get("clineno", ""),
                        "cmaterialclass": cutlist_entry["cmaterialclass"],
                        "cmaterialdescription": cutlist_entry["cmaterialdescription"],
                        "lupdate": today,
                        "part": "PIPE",
                        "discipline": "FAB",
                        "paint": "N",
                    })
    print("pipe_data ###",pipe_data)                
    return pipe_data

def write_pipe_csv(output_file, pipe_data):
    """
    Write the processed PIPE data to a CSV file.
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
        writer.writerows(pipe_data)

def process_pipe_files(extracted_folders, output_csv, pmsisoh_data):
    """
    Process extracted folders to parse Mat.txt and generate a CSV for PIPE parts.
    """
    all_pipe_data = []

    for folder in extracted_folders:
        mat_file = find_file_by_partial_name(folder, "Mat.txt")
        cutlist_file = find_file_by_partial_name(folder, "Cutlist.txt")

        if not mat_file or not cutlist_file:
            print(f"Missing Mat.txt or Cutlist.txt in {folder}. Skipping...")
            continue

        try:
            pipe_data = parse_mat_file_for_pipe(mat_file, cutlist_file, pmsisoh_data)
            all_pipe_data.extend(pipe_data)
        except Exception as e:
            print(f"Error processing PIPE data in {folder}: {e}")

    # Write the PIPE data to CSV
    write_pipe_csv(output_csv, all_pipe_data)

def find_file_by_partial_name(folder, partial_name):
    """
    Find a file by partial name in the specified folder, handling nested directories.
    """
    for root, _, files in os.walk(folder):
        for file in files:
            if partial_name.lower() in file.lower():
                return os.path.join(root, file)
    return None
