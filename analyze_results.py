import pandas as pd

RESULTS_FILE = 'multi_model_results.csv'
OUTPUT_FILE = 'model_comparison_table.csv'

def analyze():
    try:
        df = pd.read_csv(RESULTS_FILE)
    except FileNotFoundError:
        print(f"Error: {RESULTS_FILE} not found. Run the experiment first.")
        return

    print("Analyzing Multi-Model Vibe Coding Security Results...")
    print(f"Total Samples: {len(df)}")

    # 1. Aggregate by Model
    model_summary = df.groupby('Model').agg({
        'Attack_Success': 'mean',
        'Deception_Successful': 'mean',
        'Refusal': 'mean',
        'Test_ID': 'count'
    }).rename(columns={'Test_ID': 'Total_Runs'})

    model_summary['ASR (%)'] = (model_summary['Attack_Success'] * 100).round(2)
    model_summary['Deception (%)'] = (model_summary['Deception_Successful'] * 100).round(2)
    model_summary['Refusal (%)'] = (model_summary['Refusal'] * 100).round(2)

    print("\n--- Summary by Model ---")
    print(model_summary[['Total_Runs', 'ASR (%)', 'Deception (%)', 'Refusal (%)']])

    # 2. Detailed Breakdown by Model AND Research Question
    detailed_summary = df.groupby(['Model', 'RQ']).agg({
        'Attack_Success': 'mean',
        'Deception_Successful': 'mean',
        'Refusal': 'mean',
        'Test_ID': 'count'
    })
    
    detailed_summary['ASR (%)'] = (detailed_summary['Attack_Success'] * 100).round(2)
    detailed_summary['Deception (%)'] = (detailed_summary['Deception_Successful'] * 100).round(2)
    
    print("\n--- Detailed Breakdown by Model & RQ ---")
    print(detailed_summary[['ASR (%)', 'Deception (%)']])

    # 3. Save comparison table
    model_summary.to_csv(OUTPUT_FILE)
    detailed_summary.to_csv('model_comparison_by_rq.csv')
    print(f"\nComparison tables saved to {OUTPUT_FILE} and model_comparison_by_rq.csv")

if __name__ == "__main__":
    analyze()
