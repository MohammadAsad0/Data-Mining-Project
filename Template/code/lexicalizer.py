class Lexicalizer:
    """Converts numerical values to natural language descriptions"""
    
    def describe_trend(self, slope, r_squared, var_type='temperature'):
        """Describe trend magnitude and direction"""
        if r_squared < 0.2:
            return "remained relatively stable"
        
        magnitude = abs(slope)
        direction = "increasing" if slope > 0 else "decreasing"
        
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
        if temp < 0:
            return "freezing"
        elif temp < 8:
            return "cold"
        elif temp < 16:
            return "cool"
        elif temp < 25:
            return "mild"
        elif temp < 32:
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