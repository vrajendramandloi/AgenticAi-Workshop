import urllib.parse
import webbrowser

def open_train_status_in_browser(train_number_or_name: str, station: str = "") -> str:
    """Opens the user's default web browser to check the live running position of a train from a station.
    
    Args:
        train_number_or_name: The train number or name (e.g., '12951' or 'Rajdhani Express').
        station: Optional station name or code (e.g., 'Thane' or 'BCT').
    """
    query = f"live running status train {train_number_or_name} {station}".strip()
    search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    
    # Opens the URL in your local browser window
    webbrowser.open(search_url)
    
    return f"Successfully opened browser searching for train {train_number_or_name} position near {station}."
