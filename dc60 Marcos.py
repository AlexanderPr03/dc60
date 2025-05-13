import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from scipy.interpolate import griddata
import os
import time
from pathlib import Path

class DC60Calculator:
    def __init__(self, data_dir, output_dir=None):
        """
        Initialize the DC60 calculator.
        
        Parameters:
        -----------
        data_dir : str
            Directory containing the CSV/Excel data files
        output_dir : str, optional
            Directory to save output results
        """
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir) if output_dir else self.data_dir / "dc60_results"
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Parameters
        self.num_slices = 10
        self.grid_size = 20  # 20x20 grid of points per slice
        self.angles_of_attack = [0, 2, 4, 6, 8]  # example AoA values
        self.intake_radius = 0.5  # placeholder, set to your intake radius
        self.file_format = 'csv'  # Default file format (csv or xlsx)
        self.debug_mode = True  # Set to True to print additional debug information
        self.results = {}
        
    def load_data(self, slice_idx, aoa):
        """
        Load data from CSV or Excel files.
        
        Parameters:
        -----------
        slice_idx : int
            Index of the spanwise slice
        aoa : float
            Angle of attack
            
        Returns:
        --------
        dict
            Dictionary containing the flow field data
        """
        # Determine file extension based on format
        if self.file_format.lower() == 'excel' or self.file_format.lower() == 'xlsx':
            file_ext = '.xlsx'
            read_func = lambda f: pd.read_excel(f)
        else:
            file_ext = '.csv'
            # Based on the CSV format shown, there are no headers and we need to specify column names
            read_func = lambda f: pd.read_csv(f, header=None, 
                                              names=['X', 'Y', 'Z', 'Density', 'Static Pressure', 
                                                    'Flow Speed', 'Total Pressure'])
            
        # Construct filename based on slice and AoA
        # First try with the standard naming convention
        filename = f"slice_{slice_idx}_aoa_{aoa}{file_ext}"
        filepath = self.data_dir / filename
        
        # If that doesn't exist, try with "slice_csv_data" format for CSV
        if not filepath.exists() and file_ext == '.csv':
            filename = f"slice_csv_data{file_ext}"
            filepath = self.data_dir / filename
            print(f"Using generic filename: {filepath}")
            
        # Or try "slice_csv_data" format for Excel
        elif not filepath.exists() and file_ext == '.xlsx':
            filename = f"slice_csv_data{file_ext}"
            filepath = self.data_dir / filename
            print(f"Using generic filename: {filepath}")
            
        print(f"Loading data from {filepath}...")
        
        # Check if file exists
        if filepath.exists():
            try:
                # Read the file using pandas
                df = read_func(filepath)
                
                # Print column information for debugging
                print(f"Columns in file: {list(df.columns)}")
                
                # Map the columns based on what we saw in the data file
                flow_data = {
                    'x': df['X'].values,
                    'y': df['Y'].values,
                    'z': df['Z'].values,  # Adding Z coordinate
                    'total_pressure': df['Total Pressure'].values,
                    'static_pressure': df['Static Pressure'].values,
                    'density': df['Density'].values,
                    'flow_speed': df['Flow Speed'].values,
                }
                
                return flow_data
                
            except Exception as e:
                print(f"Error reading file: {e}")
                print(f"Error details: {str(e)}")
                print("Generating synthetic data instead...")
                return self._generate_synthetic_data()
        else:
            print(f"File not found: {filepath}")
            print("Generating synthetic data instead...")
            return self._generate_synthetic_data()
    
    def _generate_synthetic_data(self):
        """
        Generate synthetic flow field data for demonstration.
        
        Returns:
        --------
        dict
            Dictionary with synthetic flow field data
        """
        print("Generating synthetic flow field data for demonstration...")
        
        # Create a grid
        x = np.linspace(-5, 5, 100)
        y = np.linspace(-5, 5, 100)
        X, Y = np.meshgrid(x, y)
        
        # Generate synthetic flow field variables
        # Create a more complex pressure field with some distortion
        cx, cy = -1.5, 0.5  # Center of distortion
        total_pressure = 101325 + 2000*np.exp(-0.1*((X-cx)**2 + (Y-cy)**2))  # Base pressure field
        
        # Add some distortion patterns
        distortion = 500 * np.sin(0.5*X) * np.cos(0.7*Y)
        total_pressure += distortion
        
        # Generate other flow variables
        static_pressure = 101325 * np.ones_like(total_pressure)
        flow_speed = 100 + 10*np.sin(0.3*Y)  # Flow speed directly
        density = 1.225 * np.ones_like(total_pressure)  # Standard air density
        
        # Package the data
        flow_data = {
            'x': X.flatten(),
            'y': Y.flatten(),
            'total_pressure': total_pressure.flatten(),
            'static_pressure': static_pressure.flatten(),
            'density': density.flatten(),
            'flow_speed': flow_speed.flatten()
        }
        
        return flow_data
    
    def generate_grid_points(self, slice_idx):
        """
        Generate 20x20 grid of candidate intake centerpoints for a given slice.
        
        Parameters:
        -----------
        slice_idx : int
            Index of the spanwise slice
            
        Returns:
        --------
        numpy.ndarray
            Array of shape (400, 2) containing (x, y) coordinates
        """
        # Adjust these boundaries based on your specific geometry
        x_min, x_max = -4, 4
        y_min, y_max = -3, 1
        
        # Create the grid
        x = np.linspace(x_min, x_max, self.grid_size)
        y = np.linspace(y_min, y_max, self.grid_size)
        xx, yy = np.meshgrid(x, y)
        
        return np.column_stack([xx.flatten(), yy.flatten()])
    
    def extract_intake_cross_section(self, flow_data, center_point):
        """
        Extract flow data within the intake cross-section at a given centerpoint.
        
        Parameters:
        -----------
        flow_data : dict
            Dictionary containing the flow field data
        center_point : tuple
            (x, y) coordinates of the intake center
            
        Returns:
        --------
        dict
            Dictionary containing the flow data within the intake cross-section
        """
        x = flow_data['x']
        y = flow_data['y']
        
        # Calculate distance from each point to the center point
        distances = np.sqrt((x - center_point[0])**2 + (y - center_point[1])**2)
        
        # Select points within the intake radius
        mask = distances <= self.intake_radius
        
        # Check if we have enough points in the intake
        if sum(mask) < 5:  # Minimum number of points for meaningful calculations
            if self.debug_mode:
                print(f"Warning: Only {sum(mask)} points found in intake at position {center_point}")
            
            # If in debug mode and few points are found, increase the radius temporarily for debugging
            if self.debug_mode and sum(mask) < 3:
                temp_radius = self.intake_radius * 2
                temp_mask = distances <= temp_radius
                print(f"Debug: Expanded radius would include {sum(temp_mask)} points")
        
        # Extract data for points within the intake
        intake_data = {
            'x': x[mask],
            'y': y[mask],
            'total_pressure': flow_data['total_pressure'][mask],
            'static_pressure': flow_data['static_pressure'][mask],
            'flow_speed': flow_data['flow_speed'][mask],
            'density': flow_data['density'][mask],
            'distances': distances[mask],
            'angles': np.arctan2(y[mask] - center_point[1], x[mask] - center_point[0])
        }
        
        return intake_data
    
    def compute_dc60(self, intake_data):
        """
        Compute the DC60 distortion coefficient.
        
        Parameters:
        -----------
        intake_data : dict
            Dictionary containing the flow data within the intake cross-section
            
        Returns:
        --------
        float
            DC60 value
        """
        if len(intake_data['total_pressure']) == 0:
            return np.nan
        
        # Calculate average total pressure
        p_avg = np.mean(intake_data['total_pressure'])
        
        # Calculate dynamic pressure (q) - using flow_speed directly
        v_magnitude = intake_data['flow_speed']
        rho = np.mean(intake_data['density'])  # Use actual density from data
        q = 0.5 * rho * np.mean(v_magnitude)**2
        
        # Find the worst 60° sector
        angles = intake_data['angles']
        
        # Test different 60° windows (in radians)
        min_avg_pressure = float('inf')
        n_sectors = 36  # Divide the circle into 36 sectors for 10° resolution
        sector_width = np.deg2rad(60)
        
        for i in range(n_sectors):
            # Define the sector boundaries
            sector_start = i * (2*np.pi/n_sectors)
            sector_end = sector_start + sector_width
            
            # Find points in this sector
            # Handle wrap-around case (sector crosses 0°/360°)
            if sector_end > 2*np.pi:
                sector_mask = (angles >= sector_start) | (angles <= (sector_end - 2*np.pi))
            else:
                sector_mask = (angles >= sector_start) & (angles <= sector_end)
            
            if np.sum(sector_mask) > 0:
                # Calculate average pressure in this sector
                sector_avg_pressure = np.mean(intake_data['total_pressure'][sector_mask])
                
                # Update minimum if this sector has lower average pressure
                if sector_avg_pressure < min_avg_pressure:
                    min_avg_pressure = sector_avg_pressure
        
        # If no valid sector was found, return NaN
        if min_avg_pressure == float('inf'):
            return np.nan
            
        # Calculate DC60
        p_60 = min_avg_pressure
        
        # Protect against division by zero
        if q <= 0:
            return np.nan
            
        dc60 = (p_avg - p_60) / q
        
        return dc60
        
    def process_all_data(self):
        """
        Process all slices and angles of attack to compute DC60 values.
        """
        start_time = time.time()
        
        # Initialize results storage
        self.results = {
            aoa: {
                'slice': [],
                'x': [],
                'y': [],
                'dc60': []
            } for aoa in self.angles_of_attack
        }
        
        total_calculations = self.num_slices * self.grid_size**2 * len(self.angles_of_attack)
        completed = 0
        
        for aoa in self.angles_of_attack:
            print(f"\nProcessing angle of attack: {aoa}°")
            
            for slice_idx in range(self.num_slices):
                print(f"  Processing slice {slice_idx+1}/{self.num_slices}", end="\r")
                
                # Load flow field data for this slice and AoA
                flow_data = self.load_data(slice_idx, aoa)
                
                if self.debug_mode:
                    # Print some basic statistics about the loaded data
                    print(f"\n  Data statistics for slice {slice_idx}, AoA {aoa}:")
                    print(f"    Number of data points: {len(flow_data['x'])}")
                    print(f"    X range: [{min(flow_data['x']):.3f}, {max(flow_data['x']):.3f}]")
                    print(f"    Y range: [{min(flow_data['y']):.3f}, {max(flow_data['y']):.3f}]")
                    if 'z' in flow_data:
                        print(f"    Z range: [{min(flow_data['z']):.3f}, {max(flow_data['z']):.3f}]")
                    print(f"    Total pressure range: [{min(flow_data['total_pressure']):.3f}, {max(flow_data['total_pressure']):.3f}]")
                    print(f"    Flow speed range: [{min(flow_data['flow_speed']):.3f}, {max(flow_data['flow_speed']):.3f}]")
                
                # Generate grid points for this slice
                grid_points = self.generate_grid_points(slice_idx)
                
                if self.debug_mode:
                    print(f"    Generated {len(grid_points)} grid points for testing")
                    print(f"    Grid X range: [{min(grid_points[:,0]):.3f}, {max(grid_points[:,0]):.3f}]")
                    print(f"    Grid Y range: [{min(grid_points[:,1]):.3f}, {max(grid_points[:,1]):.3f}]")
                
                # Process each grid point
                valid_dc60_values = 0
                for i, point in enumerate(grid_points):
                    # Extract intake cross-section
                    intake_data = self.extract_intake_cross_section(flow_data, point)
                    
                    # Compute DC60
                    dc60 = self.compute_dc60(intake_data)
                    
                    # Count valid DC60 values
                    if not np.isnan(dc60):
                        valid_dc60_values += 1
                    
                    # Store results
                    self.results[aoa]['slice'].append(slice_idx)
                    self.results[aoa]['x'].append(point[0])
                    self.results[aoa]['y'].append(point[1])
                    self.results[aoa]['dc60'].append(dc60)
                    
                    # Update progress
                    completed += 1
                    if i % 50 == 0:
                        percent_complete = (completed / total_calculations) * 100
                        print(f"  Processing slice {slice_idx+1}/{self.num_slices} - {percent_complete:.1f}% complete", end="\r")
                
                if self.debug_mode:
                    print(f"\n  Valid DC60 values for slice {slice_idx}: {valid_dc60_values}/{len(grid_points)} points")
            
            print(f"  Processing slice {self.num_slices}/{self.num_slices} - 100.0% complete for AoA = {aoa}°")
                
        elapsed_time = time.time() - start_time
        print(f"\nProcessing complete in {elapsed_time:.2f} seconds")
    
    def save_results(self):
        """
        Save results to CSV files.
        """
        for aoa in self.angles_of_attack:
            # Convert to DataFrame
            df = pd.DataFrame({
                'slice': self.results[aoa]['slice'],
                'x': self.results[aoa]['x'],
                'y': self.results[aoa]['y'],
                'dc60': self.results[aoa]['dc60']
            })
            
            # Save to CSV
            output_file = self.output_dir / f"dc60_results_aoa_{aoa}.csv"
            df.to_csv(output_file, index=False)
            print(f"Results saved to {output_file}")
            
            # Also save as Excel if requested
            if self.file_format.lower() == 'excel' or self.file_format.lower() == 'xlsx':
                excel_file = self.output_dir / f"dc60_results_aoa_{aoa}.xlsx"
                df.to_excel(excel_file, index=False)
                print(f"Results saved to {excel_file}")
    
    def plot_results(self):
        """
        Create heatmap visualizations of DC60 results.
        """
        print("Generating visualizations...")
        
        for aoa in self.angles_of_attack:
            # Create a directory for the plots
            plot_dir = self.output_dir / f"plots_aoa_{aoa}"
            plot_dir.mkdir(exist_ok=True)
            
            # Get data for this AoA
            slice_values = np.array(self.results[aoa]['slice'])
            x_values = np.array(self.results[aoa]['x'])
            y_values = np.array(self.results[aoa]['y'])
            dc60_values = np.array(self.results[aoa]['dc60'])
            
            # Plot each slice
            for slice_idx in range(self.num_slices):
                # Extract data for this slice
                mask = slice_values == slice_idx
                x = x_values[mask]
                y = y_values[mask]
                dc60 = dc60_values[mask]
                
                # Skip if no valid data
                if len(x) == 0:
                    continue
                
                # Create grid for heatmap
                xi = np.linspace(min(x), max(x), 100)
                yi = np.linspace(min(y), max(y), 100)
                xi, yi = np.meshgrid(xi, yi)
                
                # Interpolate DC60 values onto the grid
                zi = griddata((x, y), dc60, (xi, yi), method='cubic', fill_value=np.nan)
                
                # Create the plot
                plt.figure(figsize=(10, 8))
                contour = plt.contourf(xi, yi, zi, 20, cmap='jet')
                plt.colorbar(contour, label='DC60')
                plt.scatter(x, y, c=dc60, s=10, cmap='jet', edgecolors='k', linewidths=0.5)
                
                # Find the minimum DC60 point
                valid_indices = ~np.isnan(dc60)
                if np.any(valid_indices):
                    min_idx = np.nanargmin(dc60)
                    plt.plot(x[min_idx], y[min_idx], 'r*', markersize=15, label=f'Min DC60: {dc60[min_idx]:.4f}')
                    plt.legend()
                
                plt.title(f'DC60 Distribution - Slice {slice_idx}, AoA {aoa}°')
                plt.xlabel('X Position')
                plt.ylabel('Y Position')
                plt.grid(True, alpha=0.3)
                
                # Save the plot
                plt.savefig(plot_dir / f'dc60_slice_{slice_idx}.png', dpi=200, bbox_inches='tight')
                plt.close()
                
            print(f"Plots saved for AoA = {aoa}°")
            
            # Create a summary plot with optimal points across all slices
            plt.figure(figsize=(12, 8))
            
            # Find optimal (minimum DC60) point for each slice
            optimal_points = []
            for slice_idx in range(self.num_slices):
                mask = slice_values == slice_idx
                if np.any(mask):
                    slice_dc60 = dc60_values[mask]
                    if not np.all(np.isnan(slice_dc60)):
                        min_idx = np.nanargmin(slice_dc60[mask])
                        optimal_points.append({
                            'slice': slice_idx,
                            'x': x_values[mask][min_idx],
                            'y': y_values[mask][min_idx],
                            'dc60': slice_dc60[min_idx]
                        })
            
            # Plot optimal points
            if optimal_points:
                opt_df = pd.DataFrame(optimal_points)
                plt.scatter(opt_df['x'], opt_df['y'], c=opt_df['dc60'], s=100, cmap='viridis', 
                           edgecolors='k', linewidths=1)
                plt.colorbar(label='DC60 Value')
                
                # Annotate points with slice number
                for _, row in opt_df.iterrows():
                    plt.annotate(f"Slice {int(row['slice'])}", 
                                (row['x'], row['y']),
                                xytext=(10, 5),
                                textcoords='offset points')
                
                plt.title(f'Optimal Intake Positions Across All Slices - AoA {aoa}°')
                plt.xlabel('X Position')
                plt.ylabel('Y Position')
                plt.grid(True, alpha=0.3)
                
                # Save summary plot
                plt.savefig(plot_dir / f'optimal_positions_summary.png', dpi=200, bbox_inches='tight')
                plt.close()
                
                # Save optimal points to CSV
                opt_df.to_csv(plot_dir / f'optimal_positions.csv', index=False)
                
            print(f"Summary plot saved for AoA = {aoa}°")
            
    def find_optimal_position(self):
        """
        Find the optimal intake position across all slices and AoA conditions.
        """
        print("\nAnalyzing optimal intake positions...")
        
        # Collect all results in a single dataframe
        all_results = []
        
        for aoa in self.angles_of_attack:
            for i in range(len(self.results[aoa]['slice'])):
                all_results.append({
                    'aoa': aoa,
                    'slice': self.results[aoa]['slice'][i],
                    'x': self.results[aoa]['x'][i],
                    'y': self.results[aoa]['y'][i],
                    'dc60': self.results[aoa]['dc60'][i]
                })
        
        # Convert to DataFrame
        df = pd.DataFrame(all_results)
        
        # Find optimal position for each AoA and slice
        optimal_positions = []
        
        for aoa in self.angles_of_attack:
            aoa_df = df[df['aoa'] == aoa]
            
            for slice_idx in range(self.num_slices):
                slice_df = aoa_df[aoa_df['slice'] == slice_idx]
                
                if not slice_df.empty:
                    # Find position with minimum dc60
                    min_idx = slice_df['dc60'].idxmin()
                    if not pd.isna(min_idx):
                        optimal_positions.append({
                            'aoa': aoa,
                            'slice': slice_idx,
                            'x': slice_df.loc[min_idx, 'x'],
                            'y': slice_df.loc[min_idx, 'y'],
                            'dc60': slice_df.loc[min_idx, 'dc60']
                        })
        
        # Convert to DataFrame
        optimal_df = pd.DataFrame(optimal_positions)
        
        if not optimal_df.empty:
            # Find overall optimal position (considering all AoAs and slices)
            overall_min_idx = optimal_df['dc60'].idxmin()
            overall_optimal = optimal_df.loc[overall_min_idx]
            
            print("\nOptimal Intake Positions Summary:")
            print("---------------------------------")
            print(f"Overall optimal position:")
            print(f"  Slice: {overall_optimal['slice']}")
            print(f"  AoA: {overall_optimal['aoa']}°")
            print(f"  Position: ({overall_optimal['x']:.3f}, {overall_optimal['y']:.3f})")
            print(f"  DC60 value: {overall_optimal['dc60']:.4f}")
            
            # Save optimal positions to file
            output_file = self.output_dir / "optimal_positions.csv"
            optimal_df.to_csv(output_file, index=False)
            print(f"\nOptimal positions saved to {output_file}")
            
            # Also save as Excel if requested
            if self.file_format.lower() == 'excel' or self.file_format.lower() == 'xlsx':
                excel_file = self.output_dir / "optimal_positions.xlsx"
                optimal_df.to_excel(excel_file, index=False)
                print(f"Optimal positions saved to {excel_file}")
                
            # Create visualization of optimal positions across AoAs
            self._plot_optimal_positions(optimal_df)
            
        else:
            print("No valid optimal positions found.")
            
    def _plot_optimal_positions(self, optimal_df):
        """
        Create visualizations showing optimal intake positions across AoAs.
        
        Parameters:
        -----------
        optimal_df : pandas.DataFrame
            DataFrame containing optimal positions
        """
        print("\nCreating optimal positions visualization...")
        
        try:
            # Create figure
            plt.figure(figsize=(12, 8))
            
            # Plot optimal positions by AoA
            for aoa in self.angles_of_attack:
                aoa_df = optimal_df[optimal_df['aoa'] == aoa]
                
                if not aoa_df.empty:
                    plt.scatter(aoa_df['x'], aoa_df['y'], label=f'AoA {aoa}°', s=100, alpha=0.7)
            
            plt.title('Optimal Intake Positions Across Different AoA Values')
            plt.xlabel('X Position')
            plt.ylabel('Y Position')
            plt.grid(True, alpha=0.3)
            plt.legend()
            
            # Save figure
            output_file = self.output_dir / "optimal_positions_by_aoa.png"
            plt.savefig(output_file, dpi=200, bbox_inches='tight')
            plt.close()
            
            print(f"Visualization saved to {output_file}")
            
            # Create a 3D visualization
            from mpl_toolkits.mplot3d import Axes3D
            
            fig = plt.figure(figsize=(12, 10))
            ax = fig.add_subplot(111, projection='3d')
            
            # Plot points by slice number (z-axis) and AoA (color)
            for aoa in self.angles_of_attack:
                aoa_df = optimal_df[optimal_df['aoa'] == aoa]
                
                if not aoa_df.empty:
                    ax.scatter(aoa_df['x'], aoa_df['y'], aoa_df['slice'], 
                              label=f'AoA {aoa}°', s=50, alpha=0.7)
            
            ax.set_title('Optimal Intake Positions in 3D (by Slice Number)')
            ax.set_xlabel('X Position')
            ax.set_ylabel('Y Position')
            ax.set_zlabel('Slice Number')
            ax.legend()
            
            # Save 3D visualization
            output_file_3d = self.output_dir / "optimal_positions_3d.png"
            plt.savefig(output_file_3d, dpi=200, bbox_inches='tight')
            plt.close()
            
            print(f"3D visualization saved to {output_file_3d}")
            
        except Exception as e:
            print(f"Error creating visualizations: {e}")

def main():
    """
    Main function to run the DC60 analysis.
    """
    import os
    
    # Get current working directory if it's not specified
    current_dir = os.getcwd()
    
    # Set paths - using current directory by default
    data_dir = current_dir  # You can change this to the specific path where your CSV files are
    output_dir = os.path.join(current_dir, "dc60_results")  # Results will be placed in a dc60_results subfolder
    
    print(f"Starting DC60 Analysis...")
    print(f"Data directory: {data_dir}")
    print(f"Output directory: {output_dir}")
    
    # Create calculator instance
    calculator = DC60Calculator(data_dir, output_dir)
    
    # Set file format (csv is default, uncomment the next line for excel)
    # calculator.file_format = 'excel'
    
    # Set parameters for the analysis based on your actual data
    calculator.num_slices = 1  # If you only have one slice file
    calculator.angles_of_attack = [0]  # If you only have data for AoA = 0
    calculator.intake_radius = 0.5  # Adjust this to match your actual intake radius
    
    # You may want to adjust grid size for placement points
    calculator.grid_size = 20  # 20x20 grid of candidate intake positions
    
    # Process all data
    calculator.process_all_data()
    
    # Save results
    calculator.save_results()
    
    # Generate plots
    calculator.plot_results()
    
    # Find optimal position
    calculator.find_optimal_position()
    
    print("Analysis complete!")

if __name__ == "__main__":
    main()