import pandas as pd
import csv
from _ast import And


pmsjnth_csv = "D:/ismometricFiles/temp_PMSJNTH.csv"
pilewall_xlsx = "D:/ismometricFiles/referenceFiles/Pipe Wall Thickness Table (REV-00).xlsx"

def main():
    enrich_pmsjnth_with_pilewall(pmsjnth_csv, pilewall_xlsx)
 
    
def enrich_pmsjnth_with_pilewall(pmsjnth_csv, pilewall_xlsx):
    """
    Enrich PMSJNTH.csv by mapping and updating the Thickness and Schedule columns
    based on Wall Thickness and Schedule from pilewall.xlsx.
    """
    # Step 1: Load the data
    pmsjnth_df = pd.read_csv(pmsjnth_csv)
    pilewall_df = pd.read_excel(pilewall_xlsx, sheet_name='Reference')

    # Step 2: Normalize column names for consistency
    pilewall_df.columns = pilewall_df.columns.str.strip().str.lower().str.replace(' ', '_')
    pmsjnth_df.columns = pmsjnth_df.columns.str.strip().str.lower()

    # Step 3: Normalize key columns in both DataFrames
    pilewall_df['service_class'] = pilewall_df['service_class'].str.strip().str.lower()
    pilewall_df['nominal_pipe_size'] = pilewall_df['nominal_pipe_size'].astype(str).str.strip()

    # Preserve original case of `class` for output
    pmsjnth_df['class_original'] = pmsjnth_df['class']
    pmsjnth_df['class'] = pmsjnth_df['class'].str.strip().str.lower()
    pmsjnth_df['inchdia'] = pmsjnth_df['inchdia'].astype(str).str.strip()

    # Step 4: Merge data for Thickness (Wall Thickness)
    thickness_merged_df = pd.merge(
        pmsjnth_df,
        pilewall_df[['service_class', 'nominal_pipe_size', 'wall_thickness']],
        how='left',
        left_on=['class', 'inchdia'],
        right_on=['service_class', 'nominal_pipe_size']
    )
    thickness_merged_df['thickness'] = thickness_merged_df['wall_thickness']
    thickness_merged_df = thickness_merged_df.drop(columns=['service_class', 'nominal_pipe_size', 'wall_thickness'])

    # Step 5: Merge data for Schedule
    schedule_merged_df = pd.merge(
        thickness_merged_df,
        pilewall_df[['service_class', 'nominal_pipe_size', 'schedule']],
        how='left',
        left_on=['class', 'inchdia'],
        right_on=['service_class', 'nominal_pipe_size']
    )
    print("merge schedule_merged_df ",schedule_merged_df)
    # Correct column assignment
    schedule_merged_df['schedule'] = schedule_merged_df['schedule_y']  # Use the correct column
    schedule_merged_df = schedule_merged_df.drop(columns=['schedule_y', 'service_class', 'nominal_pipe_size', 'schedule_x'])

    # Restore the original case of `class`
    schedule_merged_df['class'] = schedule_merged_df['class_original']
    schedule_merged_df = schedule_merged_df.drop(columns=['class_original'])

    # Step 6: Save the enriched DataFrame
    enriched_csv_path = pmsjnth_csv.replace('.csv', '_enriched33.csv')
    schedule_merged_df.to_csv(enriched_csv_path, index=False)
    print(f"Enriched data saved to: {enriched_csv_path}")

    return enriched_csv_path






    
if __name__ == "__main__":
    main()
    
    