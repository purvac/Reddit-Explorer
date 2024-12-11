import re

def remove_special_characters(text: str) -> str:
    pattern = r'[^a-zA-Z0-9\s]'
    return re.sub(pattern, '', text)