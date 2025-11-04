from scipy import stats


class DatasetAnalyzer:
    def __init__(self, df, station, variable_groups):
        self.df = df
        self.station = station
        self.variable_groups = variable_groups

    def analyze(self):
        """Main analysis pipeline"""
        results = {
            'basic': self._compute_basic_info(),
        }
        
        # Analyze each variable group
        for group_name, group_config in self.variable_groups.items():
            primary_col = group_config['primary']
            
            if primary_col in self.df.columns:
                results[group_name] = {
                    'summary': self._summarize_primary(primary_col),
                    'range': self._compute_range(group_config['supporting']),
                    'trend': self._detect_trend(primary_col),
                    'seasonal': self._compute_seasonal_patterns(primary_col),
                    'yearly': self._compute_yearly_comparisons(primary_col),
                    'extremes': self._identify_extremes(primary_col, group_config['supporting']),
                    'optional_features': self._analyze_optional_features(group_config['primary'], group_config['comparison'])
                }
        
        # Cross-variable patterns
        results['patterns'] = self._detect_cross_variable_patterns(results)
        return results

    def _compute_basic_info(self):
        """Basic dataset information"""
        return {
            'start_date': self.df['date'].min().date(),
            'end_date': self.df['date'].max().date(),
            'n_records': len(self.df),
            'station': self.station
        }
    
    def _summarize_primary(self, col):
        """Summary statistics for primary variable"""
        return {
            'mean': self.df[col].mean(),
            'std': self.df[col].std(),
            'min': self.df[col].min(),
            'max': self.df[col].max(),
            'coefficient_of_variation': self.df[col].std() / self.df[col].mean() if self.df[col].mean() != 0 else 0
        }
    
    def _compute_range(self, supporting_cols):
        """Compute range using supporting columns (e.g., temp_min, temp_max)"""
        if not supporting_cols:
            return None
        
        range_info = {}
        for col in supporting_cols:
            if col in self.df.columns:
                if 'min' in col.lower():
                    range_info['absolute_min'] = self.df[col].min()
                elif 'max' in col.lower():
                    range_info['absolute_max'] = self.df[col].max()
        
        return range_info if range_info else None
    
    def _detect_trend(self, col):
        """Detect trend over time"""
        df_copy = self.df.copy()
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
    
    def _compute_seasonal_patterns(self, col):
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
        
        df_copy = self.df.copy()
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
    
    def _compute_yearly_comparisons(self, col):
        """Compare years to find outliers"""
        yearly = self.df.groupby(self.df['date'].dt.year)[col].mean()
        
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
    
    def _identify_extremes(self, primary_col, supporting_cols):
        """Identify extreme events"""
        extremes = {}
        
        # Use max column for highest value if available, otherwise use primary
        max_col = next((c for c in supporting_cols if 'max' in c.lower()), primary_col)
        if max_col in self.df.columns:
            max_idx = self.df[max_col].idxmax()
            extremes['highest'] = {
                'value': self.df.loc[max_idx, max_col],
                'date': self.df.loc[max_idx, 'date']
            }
        
        # Use min column for lowest value if available, otherwise use primary
        min_col = next((c for c in supporting_cols if 'min' in c.lower()), primary_col)
        if min_col in self.df.columns:
            min_idx = self.df[min_col].idxmin()
            extremes['lowest'] = {
                'value': self.df.loc[min_idx, min_col],
                'date': self.df.loc[min_idx, 'date']
            }
        
        return extremes if extremes else None
    
    def _analyze_optional_features(self, primary_col, comparison_cols):
        """Analyze optional features only if they're notable"""
        features = {}
        
        for col in comparison_cols:
            if col not in self.df.columns:
                continue
            

            diff = (self.df[col] - self.df[primary_col]).abs().mean()
            if diff > 5:  # Only notable if differs by >5 degrees on average. TODO: Make this configurable??
                features['real_feel_diff'] = {
                    'avg_difference': diff,
                    'is_negative': (self.df[col] - self.df[primary_col]).mean() < 0
                }
            
            # Add other optional feature analysis as needed
        
        return features if features else None
    
    def _detect_cross_variable_patterns(self, results):
        """Find interesting patterns across multiple variables"""
        patterns = {}
        
        # Pattern 1: Which variables showed strongest trends?
        trending_vars = []
        for var_name in self.variable_groups:
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
        for var_name in self.variable_groups:
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

        # Pattern 3: Correlation between variables (if both exist)
        variables_list = list(self.variable_groups.keys())
        patterns['correlations'] = {}
        for i in range(len(variables_list)):
            for j in range(i+1, len(variables_list)):
                if variables_list[i] in results and variables_list[j] in results:
                    i_col = self.variable_groups[variables_list[i]]['primary']
                    j_col = self.variable_groups[variables_list[j]]['primary']

            
                    if i_col in self.df.columns and j_col in self.df.columns:
                        corr = self.df[i_col].corr(self.df[j_col])
                        if abs(corr) > 0.5:  # Strong correlation
                            patterns['correlations'][f'{variables_list[i]}_and_{variables_list[j]}'] = {
                                'correlation': corr,
                                'relationship': 'inverse' if corr < 0 else 'direct'
                            }
        
        return patterns