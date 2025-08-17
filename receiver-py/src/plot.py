import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
from pathlib import Path
import numpy as np


class BenchmarkPlotter:
    """Creates visualizations from benchmark CSV results"""
    
    def __init__(self, csv_file: str):
        self.df = pd.read_csv(csv_file)
        self.setup_style()
    
    def setup_style(self):
        """Setup plotting style"""
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 10
    
    def plot_success_rates(self, save_path: str = None):
        """Plot success rates by algorithm, BER, and message length"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Success Rates Comparison: CRC vs Hamming', fontsize=16, fontweight='bold')
        
        # Success rate by BER
        success_by_ber = self.df.groupby(['algorithm', 'ber_target'])['successful'].mean().reset_index()
        pivot_ber = success_by_ber.pivot(index='ber_target', columns='algorithm', values='successful')
        
        axes[0, 0].plot(pivot_ber.index, pivot_ber['crc'], 'o-', label='CRC-32', linewidth=2, markersize=6)
        axes[0, 0].plot(pivot_ber.index, pivot_ber['hamming'], 's-', label='Hamming(7,4)', linewidth=2, markersize=6)
        axes[0, 0].set_xlabel('Bit Error Rate (BER)')
        axes[0, 0].set_ylabel('Success Rate')
        axes[0, 0].set_title('Success Rate vs BER')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].set_ylim(0, 1.05)
        
        # Success rate by message length
        success_by_length = self.df.groupby(['algorithm', 'message_length'])['successful'].mean().reset_index()
        pivot_length = success_by_length.pivot(index='message_length', columns='algorithm', values='successful')
        
        axes[0, 1].plot(pivot_length.index, pivot_length['crc'], 'o-', label='CRC-32', linewidth=2, markersize=6)
        axes[0, 1].plot(pivot_length.index, pivot_length['hamming'], 's-', label='Hamming(7,4)', linewidth=2, markersize=6)
        axes[0, 1].set_xlabel('Message Length (characters)')
        axes[0, 1].set_ylabel('Success Rate')
        axes[0, 1].set_title('Success Rate vs Message Length')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].set_ylim(0, 1.05)
        
        # Correct recovery rate by BER
        recovery_by_ber = self.df.groupby(['algorithm', 'ber_target'])['recovered_correctly'].mean().reset_index()
        pivot_recovery = recovery_by_ber.pivot(index='ber_target', columns='algorithm', values='recovered_correctly')
        
        axes[1, 0].plot(pivot_recovery.index, pivot_recovery['crc'], 'o-', label='CRC-32', linewidth=2, markersize=6)
        axes[1, 0].plot(pivot_recovery.index, pivot_recovery['hamming'], 's-', label='Hamming(7,4)', linewidth=2, markersize=6)
        axes[1, 0].set_xlabel('Bit Error Rate (BER)')
        axes[1, 0].set_ylabel('Correct Recovery Rate')
        axes[1, 0].set_title('Correct Message Recovery vs BER')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].set_ylim(0, 1.05)
        
        # Heatmap of success rates
        heatmap_data = self.df.groupby(['algorithm', 'ber_target', 'message_length'])['successful'].mean().reset_index()
        
        for i, algo in enumerate(['crc', 'hamming']):
            algo_data = heatmap_data[heatmap_data['algorithm'] == algo]
            pivot_heatmap = algo_data.pivot(index='ber_target', columns='message_length', values='successful')
            
            im = axes[1, 1].imshow(pivot_heatmap.values, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
            axes[1, 1].set_xticks(range(len(pivot_heatmap.columns)))
            axes[1, 1].set_xticklabels(pivot_heatmap.columns)
            axes[1, 1].set_yticks(range(len(pivot_heatmap.index)))
            axes[1, 1].set_yticklabels([f'{x:.3f}' for x in pivot_heatmap.index])
            axes[1, 1].set_xlabel('Message Length')
            axes[1, 1].set_ylabel('BER')
            axes[1, 1].set_title(f'Success Rate Heatmap - {algo.upper()}')
            
            # Add colorbar
            cbar = plt.colorbar(im, ax=axes[1, 1], shrink=0.8)
            cbar.set_label('Success Rate')
            break  # Show only first algorithm for space
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_overhead_analysis(self, save_path: str = None):
        """Plot overhead analysis"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Overhead Analysis: CRC vs Hamming', fontsize=16, fontweight='bold')
        
        # Overhead ratio by message length
        overhead_by_length = self.df.groupby(['algorithm', 'message_length'])['overhead_ratio'].mean().reset_index()
        pivot_overhead = overhead_by_length.pivot(index='message_length', columns='algorithm', values='overhead_ratio')
        
        axes[0, 0].plot(pivot_overhead.index, pivot_overhead['crc'], 'o-', label='CRC-32', linewidth=2, markersize=6)
        axes[0, 0].plot(pivot_overhead.index, pivot_overhead['hamming'], 's-', label='Hamming(7,4)', linewidth=2, markersize=6)
        axes[0, 0].set_xlabel('Message Length (characters)')
        axes[0, 0].set_ylabel('Overhead Ratio (overhead/data bits)')
        axes[0, 0].set_title('Overhead Ratio vs Message Length')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # Absolute overhead bits
        overhead_bits_by_length = self.df.groupby(['algorithm', 'message_length'])['overhead_bits'].mean().reset_index()
        pivot_bits = overhead_bits_by_length.pivot(index='message_length', columns='algorithm', values='overhead_bits')
        
        axes[0, 1].plot(pivot_bits.index, pivot_bits['crc'], 'o-', label='CRC-32', linewidth=2, markersize=6)
        axes[0, 1].plot(pivot_bits.index, pivot_bits['hamming'], 's-', label='Hamming(7,4)', linewidth=2, markersize=6)
        axes[0, 1].set_xlabel('Message Length (characters)')
        axes[0, 1].set_ylabel('Overhead Bits')
        axes[0, 1].set_title('Absolute Overhead vs Message Length')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # Efficiency vs Success Rate scatter
        for i, algo in enumerate(['crc', 'hamming']):
            algo_data = self.df[self.df['algorithm'] == algo]
            
            axes[1, 0].scatter(algo_data['overhead_ratio'], algo_data['successful'], 
                             alpha=0.6, label=f'{algo.upper()}', s=30)
        
        axes[1, 0].set_xlabel('Overhead Ratio')
        axes[1, 0].set_ylabel('Success Rate')
        axes[1, 0].set_title('Efficiency vs Success Rate')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        # Processing time comparison
        time_by_algo = self.df.groupby(['algorithm', 'message_length'])['total_time_ms'].mean().reset_index()
        pivot_time = time_by_algo.pivot(index='message_length', columns='algorithm', values='total_time_ms')
        
        axes[1, 1].plot(pivot_time.index, pivot_time['crc'], 'o-', label='CRC-32', linewidth=2, markersize=6)
        axes[1, 1].plot(pivot_time.index, pivot_time['hamming'], 's-', label='Hamming(7,4)', linewidth=2, markersize=6)
        axes[1, 1].set_xlabel('Message Length (characters)')
        axes[1, 1].set_ylabel('Processing Time (ms)')
        axes[1, 1].set_title('Processing Time vs Message Length')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_error_correction_analysis(self, save_path: str = None):
        """Plot Hamming error correction analysis"""
        hamming_data = self.df[self.df['algorithm'] == 'hamming'].copy()
        
        if hamming_data.empty:
            print("No Hamming data found for error correction analysis")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Hamming Error Correction Analysis', fontsize=16, fontweight='bold')
        
        # Corrections vs errors injected
        axes[0, 0].scatter(hamming_data['errors_injected'], hamming_data['errors_corrected'], 
                          alpha=0.6, s=30)
        axes[0, 0].plot([0, hamming_data['errors_injected'].max()], 
                       [0, hamming_data['errors_injected'].max()], 'r--', alpha=0.5, label='Perfect correction')
        axes[0, 0].set_xlabel('Errors Injected')
        axes[0, 0].set_ylabel('Errors Corrected')
        axes[0, 0].set_title('Error Correction Capability')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # Correction rate by BER
        hamming_data['correction_rate'] = hamming_data['errors_corrected'] / np.maximum(hamming_data['errors_injected'], 1)
        correction_by_ber = hamming_data.groupby('ber_target')['correction_rate'].mean().reset_index()
        
        axes[0, 1].plot(correction_by_ber['ber_target'], correction_by_ber['correction_rate'], 
                       'o-', linewidth=2, markersize=6)
        axes[0, 1].set_xlabel('Bit Error Rate (BER)')
        axes[0, 1].set_ylabel('Correction Rate (corrected/injected)')
        axes[0, 1].set_title('Correction Rate vs BER')
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].set_ylim(0, 1.05)
        
        # Distribution of errors corrected
        axes[1, 0].hist(hamming_data['errors_corrected'], bins=20, alpha=0.7, edgecolor='black')
        axes[1, 0].set_xlabel('Number of Errors Corrected')
        axes[1, 0].set_ylabel('Frequency')
        axes[1, 0].set_title('Distribution of Errors Corrected')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Success rate vs number of errors
        success_by_errors = hamming_data.groupby('errors_injected')['successful'].mean().reset_index()
        
        axes[1, 1].plot(success_by_errors['errors_injected'], success_by_errors['successful'], 
                       'o-', linewidth=2, markersize=6)
        axes[1, 1].set_xlabel('Number of Errors Injected')
        axes[1, 1].set_ylabel('Success Rate')
        axes[1, 1].set_title('Success Rate vs Errors Injected')
        axes[1, 1].grid(True, alpha=0.3)
        axes[1, 1].set_ylim(0, 1.05)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def create_summary_table(self):
        """Create summary statistics table"""
        summary_stats = []
        
        for algo in ['crc', 'hamming']:
            algo_data = self.df[self.df['algorithm'] == algo]
            
            stats = {
                'Algorithm': algo.upper(),
                'Total Tests': len(algo_data),
                'Success Rate (%)': f"{algo_data['successful'].mean() * 100:.1f}",
                'Correct Recovery (%)': f"{algo_data['recovered_correctly'].mean() * 100:.1f}",
                'Avg Overhead Ratio': f"{algo_data['overhead_ratio'].mean():.3f}",
                'Avg Processing Time (ms)': f"{algo_data['total_time_ms'].mean():.2f}",
                'Min BER Tested': f"{algo_data['ber_target'].min():.3f}",
                'Max BER Tested': f"{algo_data['ber_target'].max():.3f}",
            }
            
            if algo == 'hamming':
                stats['Total Corrections'] = int(algo_data['errors_corrected'].sum())
                stats['Avg Corrections per Test'] = f"{algo_data['errors_corrected'].mean():.2f}"
            
            summary_stats.append(stats)
        
        summary_df = pd.DataFrame(summary_stats)
        
        print("\n" + "="*80)
        print("BENCHMARK SUMMARY TABLE")
        print("="*80)
        print(summary_df.to_string(index=False))
        print("="*80)
        
        return summary_df
    
    def save_all_plots(self, output_dir: str = "plots"):
        """Save all plots to directory"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print(f"Saving plots to {output_path}/")
        
        self.plot_success_rates(output_path / "success_rates.png")
        self.plot_overhead_analysis(output_path / "overhead_analysis.png")
        self.plot_error_correction_analysis(output_path / "error_correction.png")
        
        # Save summary table
        summary_df = self.create_summary_table()
        summary_df.to_csv(output_path / "summary_table.csv", index=False)
        
        print(f"All plots saved to {output_path}/")


def main():
    """Main plotting execution"""
    parser = argparse.ArgumentParser(description='Plot benchmark results')
    parser.add_argument('csv_file', help='CSV file with benchmark results')
    parser.add_argument('--output-dir', default='plots', help='Output directory for plots')
    parser.add_argument('--show-individual', action='store_true', help='Show individual plots')
    
    args = parser.parse_args()
    
    if not Path(args.csv_file).exists():
        print(f"Error: CSV file {args.csv_file} not found!")
        return
    
    plotter = BenchmarkPlotter(args.csv_file)
    
    # Create summary table
    plotter.create_summary_table()
    
    if args.show_individual:
        # Show individual plots
        plotter.plot_success_rates()
        plotter.plot_overhead_analysis()
        plotter.plot_error_correction_analysis()
    
    # Save all plots
    plotter.save_all_plots(args.output_dir)


if __name__ == "__main__":
    main()