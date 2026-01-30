import os
import pandas as pd
from sqlalchemy import create_engine, text
import logging
from sqlalchemy import text

# Database connection string
POSTGRESQL_URI = "postgresql+psycopg2://postgres:sa@localhost:5432/isometricChecker"

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# Logger utility functions
def log_info(message):
    logging.info(message)

def log_error(message):
    logging.error(message)

# Validate CSV file existence and non-empty status
def validate_csv_file(csv_file):
    if not os.path.exists(csv_file):
        log_error(f"Error: File {csv_file} does not exist.")
        return False
    if os.path.getsize(csv_file) == 0:
        log_error(f"Error: File {csv_file} is empty.")
        return False
    return True

# Generate table schema dynamically based on DataFrame dtypes
#DataFrame not in the below mapping, the default SQL type is 'TEXT'.

def generate_table_schema(df):
    column_definitions = []
    
    for col in df.columns:
        # Check sample values to determine data type
        non_null_values = df[col].dropna().astype(str)
        
        if non_null_values.empty:
            dtype = "TEXT"  # Default to TEXT if column has no data
        else:
            sample_value = non_null_values.sample(n=1).values[0]
            if sample_value.replace('.', '', 1).isdigit():
                dtype = "DOUBLE PRECISION" if "." in sample_value else "BIGINT"
            else:
                dtype = "TEXT"
        
        column_definitions.append(f'"{col}" {dtype}')  # Add quotes for safety
    return ", ".join(column_definitions)


# Create table and insert CSV data into PostgreSQL

def validate_and_clean_data(df):
    """
    Ensure data integrity before inserting into the database.
    Only convert numeric-like values while preserving text columns.
    """
    for col in df.columns:
        # Convert only numeric columns safely, keeping text as is
        if df[col].dtype in ['int64', 'float64']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            df[col] = df[col].astype(str)  # Preserve text
    return df


# Check for table existance in the database.



def table_exists(table_name, db_engine):
    """
    Check if a table already exists in the database.
    """
    query = text(f"""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = :table_name
    );
    """)
    with db_engine.connect() as conn:
        result = conn.execute(query, {"table_name": table_name}).scalar()
    return result

def csvFile_to_postgresql(csv_file, table_name, db_engine):
    try:
        # Read CSV file into a DataFrame
        df = pd.read_csv(csv_file)
        
        # Validate and clean data
        df = validate_and_clean_data(df)
        
        # Check if the table exists
        if not table_exists(table_name, db_engine):
            # Generate table schema based on DataFrame structure
            column_definitions = generate_table_schema(df)
            create_table_query = f"""
            CREATE TABLE {table_name} (
                {column_definitions}
            );
            """
            with db_engine.connect() as conn:
                conn.execute(text(create_table_query))
                log_info(f"Table {table_name} created successfully.")
        else:
            log_info(f"Table {table_name} already exists. Skipping creation.")
        
        # Append data to the database
        # Append data to the database
        # if_exists='replace' option in  pandas.to_sql to replace the table, before inserting new data:
        #df.to_sql(table_name, con=db_engine, if_exists='replace', index=False)
        #We can use "append" clause to append instead of replacing the exisiting data.
        
        try:
            df.to_sql(table_name, con=db_engine, if_exists='replace', index=False)
            logging.info(f"Data successfully appended to table {table_name}.")
        except Exception as e:
            logging.error(f"Error inserting data into table {table_name}: {e}")

        
        #df.to_sql(table_name, con=db_engine, if_exists='append', index=False)
        #log_info(f"Data from {csv_file} appended to {table_name}.")
    except Exception as e:
        log_error(f"Error processing {csv_file}: {e}")



# Main script to process multiple CSV files
def main():
    csv_files = [
        "D:/ismometricFiles/FeedFiles/Output_PMSJNTH.csv",
        "D:/ismometricFiles/FeedFiles/Output_PMSISOH.csv",
        "D:/ismometricFiles/FeedFiles/Output_PMSSPL.csv",
        "D:/ismometricFiles/FeedFiles/Output_PMSISOD.csv",
        "D:/ismometricFiles/FeedFiles/Output_PMSMAT.csv",
    ]
    table_names = [
        "pmsjnth",
        "pmsisoh",
        "pmsspl",
        "pmsisod",
        "pmsmat",
    ]
    
    # Create PostgreSQL engine
    #engine = create_engine(POSTGRESQL_URI)
    engine = create_engine(POSTGRESQL_URI, echo=True)  # Enable SQL logging

    
    # Loop through files and process each one
    for csv_file, table_name in zip(csv_files, table_names):
        if validate_csv_file(csv_file):
            csvFile_to_postgresql(csv_file, table_name, engine)
        else:
            log_error(f"Skipping {csv_file} due to validation failure.")

# Run the script
if __name__ == "__main__":
    main()
