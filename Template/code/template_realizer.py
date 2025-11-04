import random
from lexicalizer import Lexicalizer

class TemplateRealizer:
    """Generates text from templates and data"""
    
    def __init__(self):
        self.lexicalizer = Lexicalizer()
        self.templates = self._initialize_templates()
    
    def _initialize_templates(self):
        return {
            'overview': [
                "This analysis covers daily weather observations from {station}, spanning {start_date} to {end_date}.",
            ],
            'temperature_summary': [
                "Temperatures averaged {mean:.1f}°C, ranging from {absolute_min:.1f}°C to {absolute_max:.1f}°C.",
                "Over this period, temperatures ranged from {absolute_min:.1f}°C to {absolute_max:.1f}°C, with a mean of {mean:.1f}°C.",
            ],
            'temperature_trend': [
                "Temperature {trend_desc} over the study period.",
            ],
            'temperature_seasonal': [
                "Seasonally, summer months averaged {summer:.1f}°C while winter months averaged {winter:.1f}°C, showing a {range:.1f}°C seasonal variation.",
            ],
            'temperature_yearly': [
                "{highest_year} was the warmest year at {highest_value:.1f}°C, while {lowest_year} was the coolest at {lowest_value:.1f}°C.",
            ],
            'temperature_extremes': [
                "The hottest temperature recorded was {highest_value:.1f}°C on {highest_date}, and the coldest was {lowest_value:.1f}°C on {lowest_date}.",
            ],
            'precipitation_summary': [
                "Precipitation totaled {total:.1f} mm over the period, averaging {annual_avg:.1f} mm annually.",
                "Annual precipitation averaged {annual_avg:.1f} mm, with a total of {total:.1f} mm recorded.",
            ],
            'precipitation_trend': [
                "Precipitation {trend_desc} over time.",
            ],
            'precipitation_extremes': [
                "The heaviest single-day precipitation was {highest_value:.2f} mm on {highest_date}.",
            ],
            'other_conditions_combined': [
                "Other conditions included {conditions_desc}.",
            ],
            'pattern_trends_multi': [
                "Notably, {var1} and {var2} both showed strong trends over the period.",
            ],
            'pattern_correlation': [
                "The variables {vars} were the strongest correlated, having a {relationship} relationship.",
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
            formatted['total'] = data['summary']['mean'] * formatted.get('n_records', 1826)
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
            formatted['relationship'] = "inverse" if data['relationship'] == 'inverse' else "positive"
            formatted['vars'] = data['variables'].replace('_', ' ')
        
        return formatted
    
    def realize_combined_conditions(self, secondary_vars):
        """Combine multiple secondary variables into one sentence"""
        descriptions = []
        
        for var_name, var_data in secondary_vars:
            mean_val = var_data['summary']['mean']
            
            if var_name == 'wind_speed':
                desc = f"wind speed averaging {mean_val:.1f} kmh"
            elif var_name == 'rain':
                desc = f"rain averaging {mean_val:.1f} mm"
            elif var_name == 'snow':
                desc = f"snow averaging {mean_val:.1f} cm"
            elif var_name == 'relative_humidity':
                desc = f"relative humidity averaging {mean_val:.1f}%"
            else:
                desc = f"{var_name.replace('_', ' ')} averaging {mean_val:.1f}"
            
            descriptions.append(desc)
        
        if len(descriptions) == 1:
            return f"Other conditions included {descriptions[0]}."
        elif len(descriptions) == 2:
            return f"Other conditions included {descriptions[0]} and {descriptions[1]}."
        else:
            return f"Other conditions included {', '.join(descriptions[:-1])}, and {descriptions[-1]}."