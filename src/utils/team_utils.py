import re
import unicodedata

def normalize_text(text: str) -> str:
    if not text:
        return ""
    # Lowercase with Turkish support
    text = text.replace("İ", "i").replace("I", "ı")
    text = text.lower()
    # Normalize unicode characters
    text = text.replace("ş", "s").replace("ç", "c").replace("ğ", "g").replace("ü", "u").replace("ö", "o").replace("ı", "i")
    return text

def is_besiktas_team(team_name: str, team_slug: str = "") -> bool:
    """Accurately detects if a team is Beşiktaş across football and basketball."""
    norm_name = normalize_text(team_name)
    norm_slug = normalize_text(team_slug)
    
    if "besiktas" in norm_name or "besiktas" in norm_slug:
        return True
    return False

def format_team_name(team_name: str, is_besiktas: bool = False) -> str:
    """Formats team name, adding badge for Beşiktaş if requested."""
    clean_name = team_name.strip()
    if is_besiktas:
        return f"⭐ {clean_name}"
    return clean_name
