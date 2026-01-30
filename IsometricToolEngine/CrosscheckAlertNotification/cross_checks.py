import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text
import logging

# Database connection
POSTGRESQL_URI = "postgresql+psycopg2://postgres:sa@localhost:5432/isometricChecker"
engine = create_engine(POSTGRESQL_URI)

def table_has_data(table_name, engine):
    query = f"SELECT COUNT(*) FROM {table_name};"
    with engine.connect() as conn:
        result = conn.execute(text(query)).scalar()
    return result > 0

def run_cross_checks():
    tables = ["pmsisoh", "pmsspl", "pmsisod", "pmsjnth", "pmsmat"]
    
    for table in tables:
        if not table_has_data(table, engine):
            logging.warning(f"Skipping cross-checks: Table {table} is empty!")
            return  # Stop execution if required tables are empty
  
    queries = {
        "ISOs without Spools": """
            SELECT distinct ISONO FROM pmsisoh
            WHERE ISONO NOT IN (SELECT ISONO FROM pmsspl);
        """,
        "ISOs without MTO": """
            SELECT distinct isono FROM pmsisoh
            WHERE isono NOT IN (SELECT isono FROM pmsisod);
        """,
        "ISOs without Joints": """
            SELECT distinct isono FROM pmsisoh
            WHERE isono NOT IN (SELECT isono FROM pmsjnth);
        """,
        "Spools without ISO": """
            SELECT distinct isono FROM pmsspl
            WHERE isono NOT IN (SELECT isono FROM pmsisoh);
        """,
        "Spools without MTO": """
            SELECT ISONO, SPOOLNO FROM pmsspl
            WHERE (ISONO, SPOOLNO) NOT IN (SELECT ISONO, SPOOLNO FROM pmsisod);
        """,
        "Spools without Joints": """
            SELECT isono, spoolno FROM pmsspl
            WHERE (isono, spoolno) NOT IN (SELECT isono, sspoolno FROM pmsjnth)
            AND SPOOLNO <> 'F01';
        """,
        "MTO without ISO": """
            SELECT distinct isono FROM pmsisod
            WHERE isono NOT IN (SELECT isono FROM pmsisoh);
        """,
        "MTO without Spools": """
            SELECT distinct isono, spoolno FROM PMSISOD
            WHERE (isono, spoolno) NOT IN (SELECT isono, spoolno FROM PMSSPL);
        """,
        "MTO without Joints": """
            SELECT distinct isono, spoolno FROM PMSISOD
            WHERE (isono, spoolno) NOT IN (SELECT isono, sspoolno FROM PMSJNTH)
            AND SPOOLNO <> 'F01';
        """,
        "MTO without Material": """
            SELECT SOURCE, MATCODE, MATSUBCODE FROM PMSISOD
            WHERE (SOURCE, MATCODE, MATSUBCODE) NOT IN (SELECT SOURCE, MATCODE, MATSUBCODE FROM PMSMAT);
        """,
        "Joints without ISO": """
            SELECT distinct isono FROM pmsjnth
            WHERE isono NOT IN (SELECT isono FROM pmsisoh);
        """,
        "Joints without Spools": """
            SELECT distinct isono, sspoolno FROM PMSJNTH
            WHERE (isono, sspoolno) NOT IN (SELECT isono, spoolno FROM PMSSPL);
        """,
        "Joints without Material_PREVIOUSMATERIAL": """
            SELECT CPREVIOUSMATERIAL FROM pmsjnth
            WHERE CPREVIOUSMATERIAL NOT IN (SELECT CPREVIOUSMATERIAL FROM pmsisod);
        """,
        "Joints without Material_Next": """
            SELECT CNEXTMATERIAL FROM pmsjnth
            WHERE CNEXTMATERIAL NOT IN (SELECT CNEXTMATERIAL FROM pmsisod);
        """,
}

    # Execute each query and log results
    for check_name, query in queries.items():
        with engine.connect() as conn:
            # Use the Connection object with pd.read_sql
            result = pd.read_sql(query, conn)
            if not result.empty:
                result.to_csv(f"logs/{check_name.replace(' ', '_')}.csv", index=False)
                print(f"Discrepancies found for {check_name}. Results saved to logs.")
            else:
                print(f"No discrepancies found for {check_name}.")

if __name__ == "__main__":
    run_cross_checks()