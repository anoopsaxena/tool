import psycopg2
import logging

# Configure logging
logging.basicConfig(
    filename=r'D:\ismometricFiles\IsometricToolEngine\logs\statusNotify.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def update_isometric_status():
    """Update isometric_tracker table after batch file execution."""
    conn = None
    cur = None
    try:
        logging.info("Connecting to database for status update...")
        conn = psycopg2.connect(
            dbname="document-manage",
            user="postgres",
            password="sa",
            #host="localhost",
            host="192.168.22.54",
            port="5432"
        )
        cur = conn.cursor()

        # Fetch records to update
        #WHERE received_date IN (CURRENT_DATE, CURRENT_DATE - INTERVAL '1 day')
        cur.execute("""
            SELECT DISTINCT document_no, revision, status
            FROM public.isometric_tracker            
            WHERE received_date > '2025-05-31'
            AND REVISION NOT LIKE '%M%'
            AND document_no NOT LIKE '%-NM-%'
            AND notified = 'true'
        """)
        isometrics = cur.fetchall()
        logging.info(f"Raw isometrics fetched: {isometrics}")  # Debug log

        if not isometrics:
            logging.info("No pending isometrics found for today for status update...")
            print("No pending isometrics found for today.")
            return

        # Extract document numbers
        document_nos = [iso[0] for iso in isometrics]
        logging.info(f"Unique documents to update: {document_nos}")  # Debug log

        # Construct the IN clause manually
        # Escape single quotes in document_nos and format as a comma-separated list
        quoted_doc_nos = [f"'{doc.replace('\'', '\'\'')}'" for doc in document_nos]
        in_clause = ",".join(quoted_doc_nos)

        # Update using the IN clause  received_date IN (CURRENT_DATE, CURRENT_DATE - INTERVAL '1 day')
        query = f"""
            UPDATE public.isometric_tracker
            SET tool_status = 'Completed',
                status = 'Processed'
            WHERE document_no IN ({in_clause})
            AND received_date > '2025-05-31'
            AND REVISION NOT LIKE '%M%'
            AND document_no not like '%-NM-%'
            AND notified IS TRUE
        """
        cur.execute(query)
        conn.commit()
        logging.info(f"Updated statuses for documents: {document_nos}")
        print(f"Updated status for {len(document_nos)} documents.")

    except Exception as e:
        logging.error(f"Database error during status update: {e}")
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            logging.info("Database connection closed.")

if __name__ == "__main__":
    update_isometric_status()