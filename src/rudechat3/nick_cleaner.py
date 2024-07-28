import re

def is_valid_nickname(nickname):
    # Check if the nickname contains any invalid characters
    if re.search(r"[ ,*?!]", nickname):
        return False
    
    # Check if the nickname starts with any invalid characters
    if nickname[0] in {'$', ':'}:
        return False
    
    # Check if the nickname starts with channel type
    if nickname[0] in {'#', '&'}:
        return False
    
    # Check if the nickname contains a dot character
    if '.' in nickname:
        return False

    return True

def clean_nicknames(nicknames):
    # Return the cleaned nickname colors dictionary
    return {nickname: color for nickname, color in nicknames.items() if is_valid_nickname(nickname)}