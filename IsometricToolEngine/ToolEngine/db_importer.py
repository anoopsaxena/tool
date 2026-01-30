import os
import psycopg2
import logging
from datetime import datetime
from psycopg2 import sql
import csv

FABS_DB_CONFIG = {
    'dbname': 'fab-manage-nfs-local',
    #'dbname': 'fab-manage-nfs-dev-1',
   # 'dbname': 'fab-manage-nfs-dev',
    'user': 'postgres',
    'password': 'sa',
    'host': 'localhost',
    #'host': '192.168.22.50',
    'port': '5432'
}

FEED_FOLDER = "D:\\ismometricFiles\\FeedFiles"
LOG_FOLDER = "D:\\ismometricFiles\\IsometricToolEngine\\logs" 
#LOAD_MODE = "APPEND"  # FULL = TRUNCATE + LOAD

MAPPING = {
    "Output_PMSISOH.csv": "staging.pmsisoh_u",
    "Output_PMSISOD.csv": "staging.pmsisod_u",
    "Output_PMSSPL.csv": "staging.pmsspl_u",
    "Output_PMSJNTH.csv": "staging.pmsjnth_u",
    "Output_FLANGE.csv": "staging.flange_u" # ,    "Output_PMSMAT.csv": "staging.pmsmat"   # added for local testing
    
}


if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)

#log_file = os.path.join(LOG_FOLDER, f"db_import_{datetime.now().strftime('%Y%m%d')}.log")

log_file = r'D:\ismometricFiles\IsometricToolEngine\logs\db_import.log'
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def get_db_connection():
    return psycopg2.connect(**FABS_DB_CONFIG)



def get_table_columns(cursor, table_name):
    schema, table = table_name.split('.')
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
    """, (schema, table))
    return [row[0] for row in cursor.fetchall()]


def get_csv_headers(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        header_line = f.readline().strip().replace('"', '')
        return [h.strip() for h in header_line.split(',')]


def load_pmsmat_upsert(file_path):
    conn = None
    cursor = None
    main_table = "public.pmsmat"
    print("file_path   ###",file_path)

    try:
        conn = get_db_connection()
        conn.autocommit = False
        cursor = conn.cursor()

        # Get CSV headers and validate required columns
        csv_columns = get_csv_headers(file_path)
        required_cols = ['matcode', 'source', 'matsubcode']
        missing = [col for col in required_cols if col not in csv_columns]
        if missing:
            raise ValueError(f"Missing required columns in pmsmat.csv: {missing}")

        # Only use the 3 key columns
        final_columns = required_cols

        # Prepare UPSERT SQL
        insert_sql = sql.SQL("""
            INSERT INTO {} (matcode, source, matsubcode)
            VALUES (%s, %s, %s)
            ON CONFLICT (matcode, source, matsubcode) DO NOTHING
        """).format(sql.Identifier(*main_table.split('.')))

        rows_inserted = 0

        # Read CSV and insert row by row
        import csv
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                values = (
                    row['matcode'].strip() if row['matcode'] else None,
                    row['source'].strip() if row['source'] else None,
                    row['matsubcode'].strip() if row['matsubcode'] else None
                )
                cursor.execute(insert_sql, values)
                if cursor.rowcount > 0:
                    rows_inserted += 1

        logging.info(f"Direct upsert completed for pmsmat.csv → {rows_inserted} new rows inserted (duplicates skipped)")
        conn.commit()

    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"Error during direct pmsmat upsert: {str(e)}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Reads the first column 'isono' from Output_PMSISOH.csv  and calls the PostgreSQL function fnIsoupdate(isono) for each value.
   
def call_fnIsoupdate_for_each_isono(isoh_csv_path):
    
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        logging.info("Starting fnIsoupdate() calls for each isono from Output_PMSISOH.csv")

        isonos = set()  # Use set to avoid duplicates
        with open(isoh_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if 'isono' not in reader.fieldnames:
                raise ValueError("Column 'isono' not found in Output_PMSISOH.csv")

            for row in reader:
                isono = row['isono'].strip()
                if isono:  # Skip empty
                    isonos.add(isono)

        logging.info(f"Found {len(isonos)} unique isono values. Calling fnIsoupdate...")

        updated_count = 0
        for isono in isonos:
            try:
                cursor.execute("SELECT fnIsoupdate(%s)", (isono,))
                # Optionally fetch result if function returns something
                # result = cursor.fetchone()
                updated_count += 1
            except Exception as e:
                logging.warning(f"fnIsoupdate failed for isono={isono}: {str(e)}")

        conn.commit()
        logging.info(f"SUCCESS: fnIsoupdate called for {updated_count} unique isono values.")

    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"Error during fnIsoupdate processing: {str(e)}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()







#call the  procedures in a sequence

def execute_supportdetails_procedures():
    conn = None
    cursor = None

    procedures = [
        "SELECT staging.build_supportdetails_staging(isono) FROM staging.new_isos_processed;",
        "SELECT staging.build_supportdetails_flags(isono) FROM staging.new_isos_processed;",
        "SELECT staging.build_supportdetails_soft_delete(isono) FROM staging.new_isos_processed;",
        "SELECT staging.build_supportdetails_delete(isono) FROM staging.new_isos_processed;"
    ]

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        logging.info("Starting execution of support details procedures...")

        for i, sql in enumerate(procedures, 1):
            proc_name = sql.split('.')[1].split('(')[0]
            logging.info(f"Executing procedure {i}/4: {proc_name}")
            cursor.execute(sql)
            # Fetch if needed, but assuming void/boolean return
            cursor.fetchall()

        conn.commit()
        logging.info("All support details procedures completed successfully.")

    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"Error executing support details procedures: {str(e)}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
#Truncates staging.new_isos_processed and load based on the new Transmittal from Output_PMSISOH.csv.    
def populate_new_isos_processed(isoh_csv_path):
  
    conn = None
    cursor = None
    BATCH_SIZE = 50
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        #  Truncate previous data
        cursor.execute("TRUNCATE TABLE staging.new_isos_processed;")

        # Read unique isono values from CSV
        #unique_isonos = set()
        isono_list = []
        with open(isoh_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if 'isono' not in reader.fieldnames:
                raise ValueError("Column 'isono' not found in Output_PMSISOH.csv")

            for row in reader:
                isono = row['isono'].strip()
                if isono:
                # unique_isonos.add(isono)
                    isono_list.append((isono,))

        if not isono_list:
            logging.info("No isono values found in CSV. Skipping staging table population.")
            conn.commit()
            return

        # instead Bulk insert of  isonos, will use batches.
        insert_sql = "INSERT INTO staging.new_isos_processed (isono) VALUES (%s)"
        total_inserted = 0
        
        for i in range(0, len(isono_list), BATCH_SIZE):
            batch = isono_list[i:i + BATCH_SIZE]
            cursor.executemany(insert_sql, batch)
            total_inserted += len(batch)

        logging.info(f"Populated staging.new_isos_processed with {total_inserted} isono values (inserted in batches of {BATCH_SIZE}).")
        print(f"Populated staging.new_isos_processed with {total_inserted}")
        conn.commit()

    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"Error populating staging.new_isos_processed: {str(e)}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def import_feed_files_to_fabs():
    logging.info("----- FABS CSV IMPORT STARTED -----")
    isoh_csv_path = os.path.join(FEED_FOLDER, "Output_PMSISOH.csv")
    # call function to upload data into pmsmat table before execute the load_csv_to_table
    file_path = os.path.join(FEED_FOLDER, "Output_PMSMAT.csv")
    
    load_pmsmat_upsert(file_path)

    for file_name, table_name in MAPPING.items():
        file_path = os.path.join(FEED_FOLDER, file_name)
        print("####",file_name)

        if not os.path.exists(file_path):
            logging.error(f"File not found: {file_path}")
            continue

        if os.path.getsize(file_path) == 0:
            logging.warning(f"File is empty: {file_path}")
            continue

        try:
            
            logging.info(f"Starting import: {file_name} -> {table_name}")
            # if file_name == "pmsmat.csv":
            #     load_pmsmat_upsert(file_path)
            # else:
            load_csv_to_table(file_path, table_name)          
            logging.info(f"SUCCESS: {file_name} imported into {table_name}")
            
            #--here we need tio call procedure
            # call the metjod load_isoh () here
            # After successful import of ISOH file, trigger fnIsoupdate calls
            # if file_name == "Output_PMSISOH.csv":
            #     call_fnIsoupdate_for_each_isono(isoh_csv_path)   
                
            if file_name == "Output_PMSISOH.csv":
                populate_new_isos_processed(isoh_csv_path)
                # callng procedure: commented as requested by Ehab ::05-Jan
                #execute_supportdetails_procedures()    
               
        except Exception as e:
            logging.exception(f"FAILED importing {file_name}: {str(e)}")
            raise

    logging.info("----- FABS CSV IMPORT COMPLETED -----")

isohfile = "FEED_FOLDER/Output_PMSISOH.csv"
    
def load_csv_to_table(file_path, table_name):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        db_columns = get_table_columns(cursor, table_name)
        csv_columns = get_csv_headers(file_path)

        missing_in_csv = [col for col in db_columns if col not in csv_columns]
        extra_in_csv = [col for col in csv_columns if col not in db_columns]

        if missing_in_csv:
            print(f"Missing columns in CSV (NULL will be inserted): {missing_in_csv}")
            logging.warning(f"Missing columns in CSV: {missing_in_csv}")

        if extra_in_csv:
            print(f"Extra columns in CSV (ignored): {extra_in_csv}")
            logging.warning(f"Extra columns in CSV: {extra_in_csv}")

        final_columns = [col for col in csv_columns if col in db_columns]

        # if LOAD_MODE == "FULL":
        #     cursor.execute(sql.SQL("TRUNCATE TABLE {} CASCADE;").format(
        #         sql.Identifier(*table_name.split('.'))
        #     ))

        copy_sql = sql.SQL("COPY {} ({}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE)").format(
            sql.Identifier(*table_name.split('.')),
            sql.SQL(', ').join(map(sql.Identifier, final_columns))
        )
        logging.info(f"Inserting data into {table_name}")
        with open(file_path, 'r', encoding='utf-8') as f:
            cursor.copy_expert(copy_sql, f)

        conn.commit()

    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"Error loading {file_path} into {table_name}: {str(e)}")
        raise

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# testing purpose only

def main():
    import_feed_files_to_fabs()
#
#
if __name__ == "__main__":
    main()
