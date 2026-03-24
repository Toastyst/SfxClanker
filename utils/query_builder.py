import re

def build_search_query(raw_term: str) -> str:
    words = re.findall(r'\w+', raw_term.lower())
    words = [w for w in words if len(w) >= 3][:6]
    query = ' +'.join(words)
    if any(x in raw_term.lower() for x in ['attack hit', 'sword']):
        query += ' +sword'
    if 'level up' in raw_term.lower():
        query += ' +chime'
    if any(x in raw_term.lower() for x in ['wall crumble', 'secret']):
        query += ' +stone +break'
    return query

def enhance_query(query: str) -> str:
    return query + " dark fantasy souls-like low reverb gritty armor medieval dark souls style"