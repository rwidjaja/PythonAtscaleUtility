# overview_semantic_extract.py
def extract_window_project(html_text):
    marker = "window.project"
    idx = html_text.find(marker)
    if idx == -1:
        return None
    eq = html_text.find("=", idx)
    if eq == -1:
        return None
    brace = html_text.find("{", eq)
    if brace == -1:
        return None
    depth = 0
    i = brace
    while i < len(html_text):
        ch = html_text[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return html_text[brace:i+1]
        i += 1
    return None


def extract_basic_fields(obj):
    basic = {}
    if isinstance(obj, dict):
        # Extract common fields
        for field in ['id', 'name', 'uiid']:
            if field in obj:
                basic[field] = obj[field]

        # Extract from properties
        props = obj.get('properties', {})
        if isinstance(props, dict):
            if 'caption' in props:
                basic['caption'] = props['caption']
            if 'visible' in props:
                basic['visible'] = props['visible']
            # Extract other useful properties
            for prop_key in ['folder', 'dimension-type', 'level-type', 'default-aggregation']:
                if prop_key in props:
                    basic[prop_key] = props[prop_key]

    return basic