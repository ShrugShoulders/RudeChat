import re

def replace_pronouns(text):
    """Replace gender-specific pronouns with gender-neutral pronouns"""
    phrases = {
        r'\bhis job\b': 'their job',
        r'\bher job\b': 'their job',
        r'\bhis car\b': 'their car',
        r'\bher car\b': 'their car',
        r'\bher house\b': 'their house',
        r'\bhis house\b': 'their house',
        r'\bhis friends\b': 'their friends',
        r'\bher friends\b': 'their friends',
    }
            
    pronouns = {
        r'\bhe\b': 'they',
        r'\bhim\b(?!\s+\bjob\b|\s+\bcar\b|\s+\bhouse\b|\s+\bfriends\b)': 'them',
        r'\bhis\b': 'their',
        r'\bshe\b': 'they',
        r'\bher\b(?!\s+\bjob\b|\s+\bcar\b|\s+\bhouse\b|\s+\bfriends\b)': 'them',
        r'\bher\b': 'their',
        r'\blads\b': 'folks',
        r'\blasses\b': 'folks',
    }
    
    # Replace specific phrases
    for pattern, replacement in phrases.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Replace pronouns
    for pattern, replacement in pronouns.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
    return text
