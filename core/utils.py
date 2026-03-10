from typing import Any, Dict, List

def merge_context(existing: Dict[Any,str], new_data: Dict[Any,str]) -> Dict[Any,str]:
    merged = dict(existing or {})
    
    for key,value in (new_data or {}).items():
        if value in (None, '', [], {}, ()):  # skip empty values
            continue
        merged[key] = value
    return merged

def top_n(items: List[Dict[str, Any]], n: int) -> List[Dict[str, Any]]:
    if not isinstance(items, list):
        return []
    return items[:n]


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def compact_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in data.items() if v not in (None, '', [], {}, ())}