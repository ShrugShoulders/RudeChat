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
        r'\bhis bag\b': 'their bag',
        r'\bher bag\b': 'their bag',
        r'\bhis laptop\b': 'their laptop',
        r'\bher laptop\b': 'their laptop',
        r'\bhis friend\b': 'their friend',
        r'\bher friend\b': 'their friend',
        r'\bhis children\b': 'their children',
        r'\bher children\b': 'their children',
        r'\bhis child\b': 'their child',
        r'\bher child\b': 'their child',
        r'\bhis husband\b': 'their spouse',
        r'\bher husband\b': 'their spouse',
        r'\bhis wife\b': 'their spouse',
        r'\bher wife\b': 'their spouse',
        r'\bhis son\b': 'their child',
        r'\bher son\b': 'their child',
        r'\bhis daughter\b': 'their child',
        r'\bher daughter\b': 'their child',
        r'\bhis work\b': 'their work',
        r'\bher work\b': 'their work',
        r'\bhis project\b': 'their project',
        r'\bher project\b': 'their project',
        r'\bhis team\b': 'their team',
        r'\bher team\b': 'their team',
        r'\bhis manager\b': 'their manager',
        r'\bher manager\b': 'their manager',
        r'\bhis leader\b': 'their leader',
        r'\bher leader\b': 'their leader',
        r'\bhis mentor\b': 'their mentor',
        r'\bher mentor\b': 'their mentor',
        r'\bhis doctor\b': 'their doctor',
        r'\bher doctor\b': 'their doctor',
        r'\bhis health\b': 'their health',
        r'\bher health\b': 'their health',
        r'\bhis therapist\b': 'their therapist',
        r'\bher therapist\b': 'their therapist',
        r'\bhis story\b': 'their story',
        r'\bher story\b': 'their story',
        r'\bhis experience\b': 'their experience',
        r'\bher experience\b': 'their experience',
        r'\bhis problem\b': 'their problem',
        r'\bher problem\b': 'their problem',
        r'\bhis solution\b': 'their solution',
        r'\bher solution\b': 'their solution',
    }

            
    pronouns = {
        r'\bhe\b': 'they',
        r'\bhis\b': 'their',
        r'\bshe\b': 'they',
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
