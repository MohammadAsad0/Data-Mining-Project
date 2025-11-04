import pandas as pd
import numpy as np
from scipy import stats
import argparse
from datetime import datetime
import random


class DatasetAnalyzer:
    """Computes statistical aggregations grouped by variable type"""
    
    def __init__(self, variable_groups):
        self.variable_groups = variable_groups
    
    def analyze(self, df):
        """Main analysis pipeline - analyze by variable groups"""
        results = {
            'basic': self._compute_basic_info(df)
        }
        
        # Analyze each variable group
        for group_name, group_config in self.variable_groups.items():
            primary_col = group_config['primary']
            
            if primary_col in df.columns:
                results[group_name] = {
                    'summary': self._summarize_primary(df, primary_col),
                    'range': self._compute_range(df, group_config['supporting']),
                    'trend': self._detect_trend(df, primary_col),
                    'seasonal': self._compute_seasonal_patterns(df, primary_col),
                    'yearly': self._compute_yearly_comparisons(df, primary_col),
                    'extremes': self._identify_extremes(df, primary_col, group_config['supporting']),
                    'optional_features': self._analyze_optional_features(df, group_config['optional'])
                }
        
        # Cross-variable patterns
        results['patterns'] = self._detect_cross_variable_patterns(df, results)
        
        return results
    
    def _compute_basic_info(self, df):
        """Basic dataset information"""
        return {
            'start_date': df['date'].min(),
            'end_date': df['date'].max(),
            'n_years': (df['date'].max() - df['date'].min()).days / 365.25,
            'n_records': len(df),
            'station': df['station'].iloc[0] if 'station' in df.columns else 'Unknown Station'
        }
    
    def _summarize_primary(self, df, col):
        """Summary statistics for primary variable"""
        return {
            'mean': df[col].mean(),
            'std': df[col].std(),
            'min': df[col].min(),
            'max': df[col].max(),
            'coefficient_of_variation': df[col].std() / df[col].mean() if df[col].mean() != 0 else 0
        }
    
    def _compute_range(self, df, supporting_cols):
        """Compute range using supporting columns (e.g., temp_min, temp_max)"""
        if not supporting_cols:
            return None
        
        range_info = {}
        for col in supporting_cols:
            if col in df.columns:
                if 'min' in col.lower():
                    range_info['absolute_min'] = df[col].min()
                elif 'max' in col.lower():
                    range_info['absolute_max'] = df[col].max()
        
        return range_info if range_info else None
    
    def _detect_trend(self, df, col):
        """Detect trend over time"""
        df_copy = df.copy()
        df_copy['year_numeric'] = df_copy['date'].dt.year + df_copy['date'].dt.dayofyear / 365.25
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            df_copy['year_numeric'], 
            df_copy[col]
        )
        
        return {
            'slope': slope,
            'r_value': r_value,
            'r_squared': r_value ** 2,
            'p_value': p_value,
            'direction': 'increasing' if slope > 0 else 'decreasing'
        }
    
    def _compute_seasonal_patterns(self, df, col):
        """Compute seasonal averages"""
        def get_season(month):
            if month in [12, 1, 2]:
                return 'winter'
            elif month in [3, 4, 5]:
                return 'spring'
            elif month in [6, 7, 8]:
                return 'summer'
            else:
                return 'fall'
        
        df_copy = df.copy()
        df_copy['season'] = df_copy['date'].dt.month.apply(get_season)
        seasonal = df_copy.groupby('season')[col].mean()
        
        if len(seasonal) > 0:
            return {
                'summer': seasonal.get('summer', None),
                'winter': seasonal.get('winter', None),
                'spring': seasonal.get('spring', None),
                'fall': seasonal.get('fall', None),
                'range': seasonal.max() - seasonal.min()
            }
        return None
    
    def _compute_yearly_comparisons(self, df, col):
        """Compare years to find outliers"""
        yearly = df.groupby(df['date'].dt.year)[col].mean()
        
        if len(yearly) == 0:
            return None
        
        mean_val = yearly.mean()
        std_val = yearly.std()
        
        highest_year = yearly.idxmax()
        lowest_year = yearly.idxmin()
        
        return {
            'yearly_mean': mean_val,
            'yearly_std': std_val,
            'highest_year': highest_year,
            'highest_value': yearly[highest_year],
            'lowest_year': lowest_year,
            'lowest_value': yearly[lowest_year],
            'highest_zscore': (yearly[highest_year] - mean_val) / std_val if std_val > 0 else 0,
            'lowest_zscore': (yearly[lowest_year] - mean_val) / std_val if std_val > 0 else 0
        }
    
    def _identify_extremes(self, df, primary_col, supporting_cols):
        """Identify extreme events"""
        extremes = {}
        
        # Use max column for highest value if available, otherwise use primary
        max_col = next((c for c in supporting_cols if 'max' in c.lower()), primary_col)
        if max_col in df.columns:
            max_idx = df[max_col].idxmax()
            extremes['highest'] = {
                'value': df.loc[max_idx, max_col],
                'date': df.loc[max_idx, 'date']
            }
        
        # Use min column for lowest value if available, otherwise use primary
        min_col = next((c for c in supporting_cols if 'min' in c.lower()), primary_col)
        if min_col in df.columns:
            min_idx = df[min_col].idxmin()
            extremes['lowest'] = {
                'value': df.loc[min_idx, min_col],
                'date': df.loc[min_idx, 'date']
            }
        
        return extremes if extremes else None
    
    def _analyze_optional_features(self, df, optional_cols):
        """Analyze optional features only if they're notable"""
        features = {}
        
        for col in optional_cols:
            if col not in df.columns:
                continue
            
            # Example: real feel temperature difference
            if 'real_feel' in col.lower() and 'temp_mean' in df.columns:
                diff = (df[col] - df['temp_mean']).abs().mean()
                if diff > 5:  # Only notable if differs by >5 degrees on average
                    features['real_feel_diff'] = {
                        'avg_difference': diff,
                        'typically_colder': (df[col] - df['temp_mean']).mean() < 0
                    }
            
            # Add other optional feature analysis as needed
        
        return features if features else None
    
    def _detect_cross_variable_patterns(self, df, results):
        """Find interesting patterns across multiple variables"""
        patterns = {}
        
        # Pattern 1: Which variables showed strongest trends?
        trending_vars = []
        for var_name in ['temperature', 'precipitation', 'wind', 'humidity']:
            if var_name in results and results[var_name].get('trend'):
                trend = results[var_name]['trend']
                if trend['r_squared'] > 0.3:
                    trending_vars.append({
                        'name': var_name,
                        'r_squared': trend['r_squared'],
                        'direction': trend['direction'],
                        'slope': trend['slope']
                    })
        
        if trending_vars:
            # Sort by R² strength
            trending_vars.sort(key=lambda x: x['r_squared'], reverse=True)
            patterns['strongest_trends'] = trending_vars[:2]  # Top 2 trends
        
        # Pattern 2: Most variable conditions
        variability = {}
        for var_name in ['temperature', 'precipitation', 'wind', 'humidity']:
            if var_name in results and results[var_name].get('summary'):
                cv = results[var_name]['summary']['coefficient_of_variation']
                variability[var_name] = cv
        
        if variability:
            most_variable = max(variability.items(), key=lambda x: x[1])
            if most_variable[1] > 0.5:  # Only if CV > 0.5
                patterns['most_variable'] = {
                    'variable': most_variable[0],
                    'cv': most_variable[1]
                }
        
        # Pattern 3: Correlation between temperature and humidity (if both exist)
        if 'temperature' in results and 'humidity' in results:
            temp_col = self.variable_groups['temperature']['primary']
            humid_col = self.variable_groups['humidity']['primary']
            
            if temp_col in df.columns and humid_col in df.columns:
                corr = df[temp_col].corr(df[humid_col])
                if abs(corr) > 0.5:  # Strong correlation
                    patterns['temp_humidity_correlation'] = {
                        'correlation': corr,
                        'relationship': 'inverse' if corr < 0 else 'direct'
                    }
        
        return patterns


class ContentPlanner:
    """Decides what facts to include based on importance and significance"""
    
    def __init__(self, config):
        self.config = config
    
    def select_content(self, stats):
        """Select which facts to include"""
        content = []
        
        # Always include overview
        content.append(('overview', stats['basic']))
        
        # PRIMARY VARIABLES: Temperature and Precipitation (always include)
        for primary_var in ['temperature', 'precipitation']:
            if primary_var in stats:
                content.append((f'{primary_var}_summary', stats[primary_var]))
                
                # Include trend if significant
                if self._is_trend_significant(stats[primary_var].get('trend')):
                    content.append((f'{primary_var}_trend', stats[primary_var]['trend']))
                
                # Include seasonal if exists
                if stats[primary_var].get('seasonal'):
                    content.append((f'{primary_var}_seasonal', stats[primary_var]['seasonal']))
                
                # Include yearly comparison if notable
                if self._is_yearly_comparison_notable(stats[primary_var].get('yearly')):
                    content.append((f'{primary_var}_yearly', stats[primary_var]['yearly']))
                
                # Include extremes
                if stats[primary_var].get('extremes'):
                    content.append((f'{primary_var}_extremes', stats[primary_var]['extremes']))
        
        # SECONDARY VARIABLES: Wind and Humidity (only if notable)
        secondary_vars = []
        for var in ['wind', 'humidity']:
            if var in stats and self._is_variable_notable(stats[var]):
                secondary_vars.append((var, stats[var]))
        
        # If we have notable secondary variables, mention them
        if secondary_vars:
            content.append(('other_conditions', secondary_vars))
        
        # CROSS-VARIABLE PATTERNS
        if stats.get('patterns'):
            if stats['patterns'].get('strongest_trends'):
                content.append(('pattern_trends', stats['patterns']['strongest_trends']))
            if stats['patterns'].get('temp_humidity_correlation'):
                content.append(('pattern_correlation', stats['patterns']['temp_humidity_correlation']))
        
        return content
    
    def _is_trend_significant(self, trend_stats):
        """Check if trend is significant enough to mention"""
        if not trend_stats:
            return False
        return (trend_stats['r_squared'] >= self.config.r2_threshold and 
                trend_stats['p_value'] < self.config.p_value_threshold)
    
    def _is_yearly_comparison_notable(self, yearly_stats):
        """Check if year differences are significant"""
        if not yearly_stats:
            return False
        return (abs(yearly_stats['highest_zscore']) >= self.config.extreme_threshold or
                abs(yearly_stats['lowest_zscore']) >= self.config.extreme_threshold)
    
    def _is_variable_notable(self, var_stats):
        """Check if secondary variable deserves mention"""
        if not var_stats:
            return False
        
        # High variability
        if var_stats['summary']['coefficient_of_variation'] > 0.6:
            return True
        
        # Strong trend
        if var_stats.get('trend', {}).get('r_squared', 0) > self.config.r2_threshold:
            return True
        
        # Extreme yearly variation
        yearly = var_stats.get('yearly', {})
        if yearly and abs(yearly.get('highest_zscore', 0)) > self.config.extreme_threshold:
            return True
        
        return False


class Lexicalizer:
    """Converts numerical values to natural language descriptions"""
    
    def describe_trend(self, slope, r_squared, var_type='temperature'):
        """Describe trend magnitude and direction"""
        if r_squared < 0.2:
            return "remained relatively stable"
        
        magnitude = abs(slope)
        direction = "warming" if slope > 0 else "cooling"
        
        # Adjust language based on variable type
        if var_type == 'temperature':
            if magnitude > 0.5:
                strength = "significant"
            elif magnitude > 0.2:
                strength = "moderate"
            else:
                strength = "slight"
            return f"showed {strength} {direction}"
        
        elif var_type == 'precipitation':
            direction = "increasing" if slope > 0 else "decreasing"
            if magnitude > 2:
                strength = "substantially"
            elif magnitude > 1:
                strength = "moderately"
            else:
                strength = "slightly"
            return f"{strength} {direction}"
        
        else:
            direction = "increased" if slope > 0 else "decreased"
            return f"{direction}"
    
    def describe_temperature(self, temp):
        """Describe temperature with adjective"""
        if temp < 32:
            return "freezing"
        elif temp < 50:
            return "cold"
        elif temp < 65:
            return "cool"
        elif temp < 75:
            return "mild"
        elif temp < 85:
            return "warm"
        else:
            return "hot"
    
    def describe_variability(self, cv):
        """Describe coefficient of variation"""
        if cv > 1.0:
            return "highly variable"
        elif cv > 0.6:
            return "quite variable"
        elif cv > 0.3:
            return "moderately variable"
        else:
            return "relatively stable"
    
    def format_date(self, date):
        """Format date for natural language"""
        return date.strftime("%B %d, %Y")


class TemplateRealizer:
    """Generates text from templates and data"""
    
    def __init__(self):
        self.lexicalizer = Lexicalizer()
        self.templates = self._initialize_templates()
    
    def _initialize_templates(self):
        return {
            'overview': [
                "This analysis covers {n_years:.1f} years of weather observations from {station}, spanning {start_date} to {end_date}.",
            ],
            'temperature_summary': [
                "Temperatures averaged {mean:.1f}°F, ranging from {absolute_min:.1f}°F to {absolute_max:.1f}°F.",
                "Over this period, temperatures ranged from {absolute_min:.1f}°F to {absolute_max:.1f}°F, with a mean of {mean:.1f}°F.",
            ],
            'temperature_trend': [
                "Temperature {trend_desc} over the study period.",
            ],
            'temperature_seasonal': [
                "Seasonally, summer months averaged {summer:.1f}°F while winter months averaged {winter:.1f}°F, showing a {range:.1f}°F seasonal variation.",
            ],
            'temperature_yearly': [
                "{highest_year} was the warmest year at {highest_value:.1f}°F, while {lowest_year} was the coolest at {lowest_value:.1f}°F.",
            ],
            'temperature_extremes': [
                "The hottest temperature recorded was {highest_value:.1f}°F on {highest_date}, and the coldest was {lowest_value:.1f}°F on {lowest_date}.",
            ],
            'precipitation_summary': [
                "Precipitation totaled {total:.1f} inches over the period, averaging {annual_avg:.1f} inches annually.",
                "Annual precipitation averaged {annual_avg:.1f} inches, with a total of {total:.1f} inches recorded.",
            ],
            'precipitation_trend': [
                "Precipitation {trend_desc} over time.",
            ],
            'precipitation_extremes': [
                "The heaviest single-day precipitation was {highest_value:.2f} inches on {highest_date}.",
            ],
            'other_conditions_combined': [
                "Other conditions included {conditions_desc}.",
            ],
            'pattern_trends_multi': [
                "Notably, {var1} and {var2} both showed strong trends over the period.",
            ],
            'pattern_correlation': [
                "Temperature and humidity were {relationship} correlated, with {correlation_desc}.",
            ]
        }
    
    def realize(self, fact_type, data):
        """Generate text from template"""
        if fact_type not in self.templates:
            return ""
        
        template = random.choice(self.templates[fact_type])
        formatted_data = self._prepare_data(fact_type, data)
        
        try:
            return template.format(**formatted_data)
        except KeyError as e:
            print(f"Warning: Missing key {e} for template {fact_type}")
            return ""
    
    def _prepare_data(self, fact_type, data):
        """Prepare data for template formatting"""
        formatted = data.copy() if isinstance(data, dict) else {}
        
        # Handle dates
        if 'start_date' in formatted:
            formatted['start_date'] = self.lexicalizer.format_date(formatted['start_date'])
        if 'end_date' in formatted:
            formatted['end_date'] = self.lexicalizer.format_date(formatted['end_date'])
        
        # Temperature summary
        if fact_type == 'temperature_summary':
            if 'range' in data and data['range']:
                formatted['absolute_min'] = data['range'].get('absolute_min', data['summary']['min'])
                formatted['absolute_max'] = data['range'].get('absolute_max', data['summary']['max'])
            else:
                formatted['absolute_min'] = data['summary']['min']
                formatted['absolute_max'] = data['summary']['max']
            formatted['mean'] = data['summary']['mean']
        
        # Temperature trend
        if fact_type == 'temperature_trend':
            formatted['trend_desc'] = self.lexicalizer.describe_trend(
                data['slope'], data['r_squared'], 'temperature'
            )
        
        # Precipitation summary
        if fact_type == 'precipitation_summary':
            # Calculate total from annual average and years
            formatted['total'] = data['summary']['mean'] * formatted.get('n_records', 0) / 365.25
            formatted['annual_avg'] = data['summary']['mean'] * 365.25
        
        # Precipitation trend
        if fact_type == 'precipitation_trend':
            formatted['trend_desc'] = self.lexicalizer.describe_trend(
                data['slope'], data['r_squared'], 'precipitation'
            )
        
        # Extremes
        if 'extremes' in fact_type:
            if 'highest' in data:
                formatted['highest_value'] = data['highest']['value']
                formatted['highest_date'] = self.lexicalizer.format_date(data['highest']['date'])
            if 'lowest' in data:
                formatted['lowest_value'] = data['lowest']['value']
                formatted['lowest_date'] = self.lexicalizer.format_date(data['lowest']['date'])
        
        # Yearly comparisons
        if 'yearly' in fact_type:
            # Data is already properly formatted from the stats
            pass
        
        # Seasonal
        if 'seasonal' in fact_type:
            # Data is already properly formatted
            pass
        
        # Pattern correlation
        if fact_type == 'pattern_correlation':
            corr = data['correlation']
            formatted['relationship'] = "inversely" if data['relationship'] == 'inverse' else "positively"
            if abs(corr) > 0.7:
                formatted['correlation_desc'] = "hotter days typically being much drier" if corr < 0 else "hotter days typically being more humid"
            else:
                formatted['correlation_desc'] = "a moderate relationship between the two"
        
        return formatted
    
    def realize_combined_conditions(self, secondary_vars):
        """Combine multiple secondary variables into one sentence"""
        descriptions = []
        
        for var_name, var_data in secondary_vars:
            mean_val = var_data['summary']['mean']
            
            if var_name == 'wind':
                desc = f"winds averaging {mean_val:.1f} mph"
            elif var_name == 'humidity':
                desc = f"{mean_val:.1f}% humidity"
            else:
                desc = f"{var_name} averaging {mean_val:.1f}"
            
            descriptions.append(desc)
        
        if len(descriptions) == 1:
            return f"Other conditions included {descriptions[0]}."
        elif len(descriptions) == 2:
            return f"Other conditions included {descriptions[0]} and {descriptions[1]}."
        else:
            return f"Other conditions included {', '.join(descriptions[:-1])}, and {descriptions[-1]}."


class WeatherSummarizer:
    """Main summarizer class with scalable variable handling"""
    
    def __init__(self, config):
        self.config = config
        
        # Define variable groups - easily extensible
        self.variable_groups = {
            'temperature': {
                'primary': 'temp_mean',
                'supporting': ['temp_min', 'temp_max'],
                'optional': ['temp_real_feel_mean']
            },
            'precipitation': {
                'primary': 'precipitation_mean',
                'supporting': ['precipitation_max'],
                'optional': []
            },
            'wind': {
                'primary': 'wind_speed_mean',
                'supporting': ['wind_speed_max'],
                'optional': ['wind_direction_dominant']
            },
            'humidity': {
                'primary': 'humidity_mean',
                'supporting': [],
                'optional': []
            }
        }
        
        self.analyzer = DatasetAnalyzer(self.variable_groups)
        self.planner = ContentPlanner(config)
        self.realizer = TemplateRealizer()
    
    def generate_summary(self, input_file):
        """Generate summary from weather data CSV"""
        # Load data
        df = self._load_data(input_file)
        
        # Analyze data by groups
        stats = self.analyzer.analyze(df)
        
        # Plan content
        content = self.planner.select_content(stats)
        
        # Generate text
        sentences = []
        for fact_type, data in content:
            if fact_type == 'other_conditions':
                # Special handling for combined secondary variables
                sentence = self.realizer.realize_combined_conditions(data)
            else:
                sentence = self.realizer.realize(fact_type, data)
            
            if sentence:
                sentences.append(sentence)
        
        # Combine into summary
        summary = " ".join(sentences)
        
        return summary
    
    def _load_data(self, input_file):
        """Load and prepare weather data"""
        df = pd.read_csv(input_file)
        
        # Ensure date column is datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Auto-detect and standardize column names
        df = self._standardize_columns(df)
        
        # Handle missing values
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df = df.dropna(subset=numeric_cols, how='all')
        
        return df
    
    def _standardize_columns(self, df):
        """Standardize column names to match expected format"""
        # Create mapping for common variations
        column_mapping = {}
        
        for col in df.columns:
            col_lower = col.lower()
            
            # Temperature variations
            if 'temp' in col_lower and 'mean' in col_lower or col_lower == 'tavg':
                column_mapping[col] = 'temp_mean'
            elif 'temp' in col_lower and 'min' in col_lower or col_lower == 'tmin':
                column_mapping[col] = 'temp_min'
            elif 'temp' in col_lower and 'max' in col_lower or col_lower == 'tmax':
                column_mapping[col] = 'temp_max'
            
            # Precipitation variations
            elif 'precip' in col_lower or col_lower == 'prcp':
                if 'mean' in col_lower or 'avg' in col_lower:
                    column_mapping[col] = 'precipitation_mean'
                elif 'max' in col_lower:
                    column_mapping[col] = 'precipitation_max'
                elif 'min' not in col_lower:
                    column_mapping[col] = 'precipitation_mean'
            
            # Wind variations
            elif 'wind' in col_lower and 'speed' in col_lower:
                if 'mean' in col_lower or 'avg' in col_lower:
                    column_mapping[col] = 'wind_speed_mean'
                elif 'max' in col_lower:
                    column_mapping[col] = 'wind_speed_max'
            
            # Humidity variations
            elif 'humid' in col_lower:
                if 'mean' in col_lower or 'avg' in col_lower or col_lower == 'humidity':
                    column_mapping[col] = 'humidity_mean'
        
        # Rename columns
        df = df.rename(columns=column_mapping)
        
        return df


def main():
    parser = argparse.ArgumentParser(
        description='Generate natural language summary from weather dataset (scalable for many columns)'
    )
    
    # Statistical thresholds
    parser.add_argument('--r2_threshold', type=float, default=0.3,
                       help='Minimum R² to report a trend (default: 0.3)')
    parser.add_argument('--p_value_threshold', type=float, default=0.05,
                       help='Maximum p-value for significance (default: 0.05)')
    parser.add_argument('--extreme_threshold', type=float, default=2.0,
                       help='Z-score threshold for extremes (default: 2.0)')
    
    # Input/output
    parser.add_argument('--input', required=True, 
                       help='Input weather data CSV')
    parser.add_argument('--output', default='summary.txt', 
                       help='Output summary file')
    
    # Optional: Add station name if not in CSV
    parser.add_argument('--station', default=None,
                       help='Station name (if not in CSV)')
    
    args = parser.parse_args()
    
    # Create summarizer with these settings
    summarizer = WeatherSummarizer(args)
    
    # Generate summary
    print(f"Analyzing weather data from {args.input}...")
    summary = summarizer.generate_summary(args.input)
    
    # Save summary
    with open(args.output, 'w') as f:
        f.write(summary)
    
    print(f"\nGenerated Summary:")
    print("=" * 80)
    print(summary)
    print("=" * 80)
    print(f"\nSummary saved to {args.output}")
    print(f"\nConfiguration used:")
    print(f"  R² threshold: {args.r2_threshold}")
    print(f"  p-value threshold: {args.p_value_threshold}")
    print(f"  Extreme threshold: {args.extreme_threshold}")


if __name__ == '__main__':
    main()