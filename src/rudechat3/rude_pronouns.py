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
        r'\bhis father\b': 'their father',
        r'\bher father\b': 'their father',
        r'\bhis mother\b': 'their mother',
        r'\bher mother\b': 'their mother',
        r'\bhis brother\b': 'their sibling',
        r'\bher brother\b': 'their sibling',
        r'\bhis sister\b': 'their sibling',
        r'\bher sister\b': 'their sibling',
        r'\bhis book\b': 'their book',
        r'\bher book\b': 'their book',
        r'\bhis phone\b': 'their phone',
        r'\bher phone\b': 'their phone',
        r'\bhis boss\b': 'their boss',
        r'\bher boss\b': 'their boss',
        r'\bhis teacher\b': 'their teacher',
        r'\bher teacher\b': 'their teacher',
        r'\bhis colleague\b': 'their colleague',
        r'\bher colleague\b': 'their colleague',
        r'\bhis advice\b': 'their advice',
        r'\bher advice\b': 'their advice',
        r'\bhis opinion\b': 'their opinion',
        r'\bher opinion\b': 'their opinion',
        r'\bher thoughts\b': 'their thoughts',
        r'\bhis thoughts\b': 'their thoughts',
        r'\bher thought\b': 'their thought',
        r'\bhis thought\b': 'their thought',
    }
            
    pronouns = {
        r'\bhe\b': 'they',
        r'\bhim\b(?!\s+\bjob\b|\s+\bcar\b|\s+\bhouse\b|\s+\bfriends\b|\s+\bfather\b|\s+\bmother\b|\s+\bbrother\b|\s+\bsister\b|\s+\bbook\b|\s+\bphone\b|\s+\bboss\b|\s+\bteacher\b|\s+\bcolleague\b|\s+\badvice\b|\s+\bopinion\b)': 'them',
        r'\bhis\b': 'their',
        r'\bshe\b': 'they',
        r'\bher\b(?!\s+\bjob\b|\s+\bcar\b|\s+\bhouse\b|\s+\bfriends\b|\s+\bfather\b|\s+\bmother\b|\s+\bbrother\b|\s+\bsister\b|\s+\bbook\b|\s+\bphone\b|\s+\bboss\b|\s+\bteacher\b|\s+\bcolleague\b|\s+\badvice\b|\s+\bopinion\b)': 'them',
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
