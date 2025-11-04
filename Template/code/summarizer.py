import pandas as pd
from dataset_analyzer import DatasetAnalyzer
from content_planner import ContentPlanner
from template_realizer import TemplateRealizer

class Summarizer:
    def __init__(self, config):
        self.config = config
        self.variable_groups = {
            'temperature': {
                'primary': 'temperature_2m_mean (°C)',
                'supporting': ['temperature_2m_min (°C)', 'temperature_2m_max (°C)'],
                'comparison': ['apparent_temperature_mean (°C)']
            },
            'precipitation': {
                'primary': 'precipitation_sum (mm)',
                'supporting': [],
                'comparison': []
            },
            'rain': {
                'primary': 'rain_sum (mm)',
                'supporting': [],
                'comparison': []
            },
            'snow': {
                'primary': 'snowfall_sum (cm)',
                'supporting': [],
                'comparison': []
            },
            'precipitation_hours': {
                'primary': 'precipitation_hours (h)',
                'supporting': [],
                'comparison': []
            },
            'wind_speed': {
                'primary': 'wind_speed_10m_mean (km/h)',
                'supporting': ['wind_speed_10m_min (km/h)', 'wind_speed_10m_max (km/h)'],
                'comparison': ['wind_gusts_10m_mean (km/h)']
            },
            'relative_humidity': {
                'primary': 'relative_humidity_2m_mean (%)',
                'supporting': ['relative_humidity_2m_min (%)', 'relative_humidity_2m_max (%)'],
                'comparison': []
            },
            'sunshine_duration': {
                'primary': 'sunshine_duration (s)',
                'supporting': [],
                'comparison': []
            }
        }

    def generate_summary(self):
        """Generate summary from weather data CSV"""
        # Load data
        df = self._load_data(self.config.input)
        
        # Analyze data
        analyzer = DatasetAnalyzer(df, self.config.station_name, self.variable_groups)
        stats = analyzer.analyze()

        # Plan content
        planner = ContentPlanner(self.config, stats, self.variable_groups)
        content = planner.select_content()
        
        # Generate text
        realizer = TemplateRealizer()
        sentences = []
        for fact_type, data in content:
            sentence = ''
            if fact_type == 'other_conditions':
                sentence = realizer.realize_combined_conditions(data)
            else:
                sentence = realizer.realize(fact_type, data)
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
        
        # Handle missing values
        df = df.dropna()

        return df