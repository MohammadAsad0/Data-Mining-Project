class ContentPlanner:
    """Decides what facts to include based on importance and significance"""
    
    def __init__(self, config, stats, variable_groups):
        self.config = config
        self.stats = stats
        self.variable_groups = variable_groups
    
    def select_content(self):
        """Select which facts to include"""
        content = []
        
        # Always include overview
        content.append(('overview', self.stats['basic']))
        
        # PRIMARY VARIABLES: Temperature and Precipitation (always include)
        for primary_var in ['temperature', 'precipitation']:
            if primary_var in self.stats:
                content.append((f'{primary_var}_summary', self.stats[primary_var]))
                
                # Include trend if significant
                if self._is_trend_significant(self.stats[primary_var].get('trend')):
                    content.append((f'{primary_var}_trend', self.stats[primary_var]['trend']))
                
                # Include seasonal if exists
                if self.stats[primary_var].get('seasonal'):
                    content.append((f'{primary_var}_seasonal', self.stats[primary_var]['seasonal']))
                
                # Include yearly comparison if notable
                if self._is_yearly_comparison_notable(self.stats[primary_var].get('yearly')):
                    content.append((f'{primary_var}_yearly', self.stats[primary_var]['yearly']))
                
                # Include extremes
                if self.stats[primary_var].get('extremes'):
                    content.append((f'{primary_var}_extremes', self.stats[primary_var]['extremes']))
        
        # SECONDARY VARIABLES: Wind and Humidity (only if notable)
        secondary_vars = []
        for var in ['wind_speed', 'relative_humidity', 'rain', 'snow', 'precipitation_hours', 'sunshine_duration']:
            if var in self.stats and self._is_variable_notable(self.stats[var]):
                secondary_vars.append((var, self.stats[var]))
        
        # If we have notable secondary variables, mention them
        if secondary_vars:
            content.append(('other_conditions', secondary_vars))
        
        # CROSS-VARIABLE PATTERNS
        if self.stats.get('patterns'):
            if self.stats['patterns'].get('strongest_trends'):
                content.append(('pattern_trends', self.stats['patterns']['strongest_trends']))
            max_corr = 0
            max_corr_vars = {}
            for corr_stat in self.stats['patterns']['correlations']:
                if self.stats['patterns']['correlations'][corr_stat]['correlation'] > max_corr:
                    max_corr = self.stats['patterns']['correlations'][corr_stat]['correlation']
                    max_corr_vars = {'variables': corr_stat,
                                     'correlation': self.stats['patterns']['correlations'][corr_stat]['correlation'],
                                     'relationship': self.stats['patterns']['correlations'][corr_stat]['relationship']}
            content.append(('pattern_correlation', max_corr_vars))
        
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