import pandas as pd
import numpy as np
from sklearn.neighbors import BallTree
import sys

def fill_missing_weather_data(file_path='final.csv'):
    """
    Fills missing weather data in the provided CSV file.

    The method finds the nearest geographical neighbor (using latitude and longitude)
    that has a *different* 'city' label and copies its weather data.
    """
    try:
        # Load the dataset
        df = pd.read_csv(file_path)
        print(f"Successfully loaded '{file_path}'.")
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        print("Please make sure the file is in the same directory as the script.")
        return
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return

    # --- 1. Identify Weather Columns ---
    # Based on your description, weather columns start from 'Ortalama Sıcaklık (°C)_Ocak'
    weather_column_prefixes = [
        'Ortalama Sıcaklık (°C)',
        'Ortalama En Yüksek Sıcaklık (°C)',
        'Ortalama En Düşük Sıcaklık (°C)',
        'Ortalama Güneşlenme Süresi (saat)',
        'Ortalama Yağışlı Gün Sayısı',
        'Aylık Toplam Yağış Miktarı Ortalaması (mm)'
    ]
    
    weather_columns = [col for col in df.columns if any(col.startswith(prefix) for prefix in weather_column_prefixes)]
    
    if not weather_columns:
        print("Error: Could not find any weather columns based on the specified prefixes.")
        print("Please check the column names in your file.")
        return

    # --- 2. Separate Data ---
    # Identify rows with *any* missing weather data in the identified columns
    missing_mask = df[weather_columns].isnull().any(axis=1)
    
    # Check if 'latitude', 'longitude', or 'city' are missing in the rows that need filling
    required_cols = ['latitude', 'longitude', 'city']
    if df.loc[missing_mask, required_cols].isnull().any().any():
        print("Warning: Some rows with missing weather data are also missing 'latitude', 'longitude', or 'city'.")
        print("These rows cannot be filled and will be skipped.")
        # Update the missing_mask to exclude rows missing essential lookup info
        missing_mask = missing_mask & df[required_cols].notnull().all(axis=1)

    df_missing = df[missing_mask].copy()
    df_complete = df[~missing_mask].copy()

    if df_missing.empty:
        print("No rows with missing weather data found. The file is already complete.")
        return
        
    if df_complete.empty:
        print("Error: No complete rows found to source data from. Cannot perform imputation.")
        return

    print(f"Found {len(df_missing)} rows with missing weather data to fill.")
    print(f"Using {len(df_complete)} rows as the data source.")

    # --- 3. Prepare for Nearest Neighbor Search ---
    # Convert lat/lon to radians for Haversine distance (used by BallTree)
    coords_complete = np.radians(df_complete[['latitude', 'longitude']].values)
    
    # Build BallTree for efficient geospatial search
    tree = BallTree(coords_complete, leaf_size=15, metric='haversine')

    # --- 4. Iterate and Impute ---
    imputed_count = 0
    not_found_count = 0

    # Create a new DataFrame for imputed rows to avoid modifying the one we iterate over
    df_imputed = df_missing.copy()
    
    # We need to iterate using the original DataFrame's index to modify df_imputed
    for index, row in df_missing.iterrows():
        # Get coordinates and city for the row with missing data
        current_city = row['city']
        current_coords_rad = np.radians([[row['latitude'], row['longitude']]])
        
        # Query the tree for neighbors. 
        # We ask for a few (e.g., 10) in case the closest ones have the same city label.
        # Ensure k is not larger than the number of available data points.
        k_neighbors = min(10, len(df_complete))
        distances, indices = tree.query(current_coords_rad, k=k_neighbors)
        
        found_donor = False
        # Iterate through the neighbors found (indices[0] contains the list of neighbor indices)
        for i in indices[0]:
            neighbor_row = df_complete.iloc[i]
            
            # Check if the city is different
            if neighbor_row['city'] != current_city:
                # Found a suitable donor. Copy all weather data.
                # The '# type: ignore' silences the false-positive linter warning.
                df_imputed.loc[index, weather_columns] = neighbor_row[weather_columns].values  # type: ignore
                imputed_count += 1
                found_donor = True
                break # Move to the next missing row
        
        if not found_donor:
            not_found_count += 1

    # --- 5. Combine and Save ---
    # Combine the newly imputed rows with the original complete rows
    df_final = pd.concat([df_complete, df_imputed]).sort_index()

    # Save to a new CSV file
    output_filename = 'final2.csv'
    df_final.to_csv(output_filename, index=False, encoding='utf-8-sig')

    print(f"\n--- Process Complete ---")
    print(f"Successfully imputed data for {imputed_count} rows.")
    if not_found_count > 0:
        print(f"Could not find a suitable neighbor for {not_found_count} rows (they remain unfilled).")
    print(f"New file saved as: {output_filename}")

# --- Main execution ---
if __name__ == "__main__":
    # You can change the file name here if needed
    input_file = 'final.csv' 
    
    # Or, allow passing it as a command-line argument
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        
    fill_missing_weather_data(file_path=input_file)