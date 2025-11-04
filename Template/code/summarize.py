import argparse
from summarizer import Summarizer

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--r2_threshold', type=float, default=0.3,
                       help='Minimum R^2 to consider a trend as one to report (default: 0.3)')
    parser.add_argument('--p_value_threshold', type=float, default=0.05,
                       help='Maximum p-value for significance (default: 0.05)')
    parser.add_argument('--extreme_threshold', type=float, default=2.0,
                       help='Z-score threshold for extremes (default: 2.0)')
    parser.add_argument('--input', required=True, 
                       help='Input weather data CSV path')
    parser.add_argument('--output', default='summary.txt', 
                       help='Output summary file')
    parser.add_argument('--station_name', default="unknown",
                        help='The weather station from whcih this data has been collected (default: unknown)')
    args = parser.parse_args()

    summarizer = Summarizer(args)

    # Generate summary
    print(f"Analyzing weather data from {args.input}...")
    summary = summarizer.generate_summary()
     # Save summary
    with open(args.output, 'w') as f:
        f.write(summary)
    
    print(f"\nGenerated Summary:")
    print("=" * 80)
    print(summary)
    print("=" * 80)
    print(f"\nSummary saved to {args.output}")

if __name__ == '__main__':
    main()