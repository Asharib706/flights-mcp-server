from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

from fast_flights import FlightData, Passengers, Result, get_flights, search_airport
from fast_flights._generated_enum import Airport
from dataclasses import asdict

from datetime import datetime, timedelta


# initialize the MCP server
mcp = FastMCP("flights")


# ── City / Country → IATA code mapping ──────────────────────────────────────
# The fast_flights search_airport() function is unreliable for many major cities
# (e.g. "New York", "Tokyo", "Karachi", "JFK", "LAX" all return empty).
# This mapping fixes that by providing a hand-curated lookup.

CITY_AIRPORT_MAP: dict[str, list[str]] = {
    # ── United States ──
    "new york":       ["JFK", "EWR", "LGA"],
    "nyc":            ["JFK", "EWR", "LGA"],
    "los angeles":    ["LAX"],
    "la":             ["LAX"],
    "san francisco":  ["SFO", "OAK", "SJC"],
    "sf":             ["SFO"],
    "chicago":        ["ORD", "MDW"],
    "miami":          ["MIA", "FLL"],
    "washington":     ["IAD", "DCA", "BWI"],
    "washington dc":  ["IAD", "DCA", "BWI"],
    "dc":             ["IAD", "DCA", "BWI"],
    "dallas":         ["DFW", "DAL"],
    "houston":        ["IAH", "HOU"],
    "atlanta":        ["ATL"],
    "boston":          ["BOS"],
    "seattle":        ["SEA"],
    "denver":         ["DEN"],
    "detroit":        ["DTW"],
    "phoenix":        ["PHX"],
    "orlando":        ["MCO"],
    "minneapolis":    ["MSP"],
    "philadelphia":   ["PHL"],
    "las vegas":      ["LAS"],
    "honolulu":       ["HNL"],
    "portland":       ["PDX"],
    "charlotte":      ["CLT"],
    "san diego":      ["SAN"],
    "austin":         ["AUS"],
    "nashville":      ["BNA"],
    "salt lake city": ["SLC"],

    # ── Canada ──
    "toronto":        ["YYZ", "YTZ"],
    "vancouver":      ["YVR"],
    "montreal":       ["YUL"],
    "calgary":        ["YYC"],
    "ottawa":         ["YOW"],

    # ── United Kingdom ──
    "london":         ["LHR", "LGW", "STN", "LTN", "LCY", "SEN"],
    "manchester":     ["MAN"],
    "birmingham":     ["BHX"],
    "edinburgh":      ["EDI"],
    "glasgow":        ["GLA"],

    # ── Europe ──
    "paris":          ["CDG", "ORY"],
    "amsterdam":      ["AMS"],
    "frankfurt":      ["FRA"],
    "munich":         ["MUC"],
    "berlin":         ["BER"],
    "rome":           ["FCO", "CIA"],
    "milan":          ["MXP", "LIN"],
    "madrid":         ["MAD"],
    "barcelona":      ["BCN"],
    "zurich":         ["ZRH"],
    "vienna":         ["VIE"],
    "brussels":       ["BRU"],
    "lisbon":         ["LIS"],
    "copenhagen":     ["CPH"],
    "oslo":           ["OSL"],
    "stockholm":      ["ARN"],
    "helsinki":        ["HEL"],
    "dublin":         ["DUB"],
    "athens":         ["ATH"],
    "istanbul":       ["IST", "SAW"],
    "moscow":         ["SVO", "DME", "VKO"],
    "prague":         ["PRG"],
    "warsaw":         ["WAW"],
    "budapest":       ["BUD"],

    # ── Middle East ──
    "dubai":          ["DXB", "DWC"],
    "abu dhabi":      ["AUH"],
    "doha":           ["DOH"],
    "riyadh":         ["RUH"],
    "jeddah":         ["JED"],
    "muscat":         ["MCT"],
    "kuwait":         ["KWI"],
    "bahrain":        ["BAH"],
    "amman":          ["AMM"],
    "beirut":         ["BEY"],
    "tel aviv":       ["TLV"],

    # ── Pakistan ──
    "karachi":        ["KHI"],
    "lahore":         ["LHE"],
    "islamabad":      ["ISB"],
    "peshawar":       ["PEW"],
    "quetta":         ["UET"],
    "multan":         ["MUX"],
    "faisalabad":     ["LYP"],
    "sialkot":        ["SKT"],
    "pakistan":        ["KHI", "LHE", "ISB", "PEW", "UET", "MUX", "LYP", "SKT"],

    # ── India ──
    "delhi":          ["DEL"],
    "new delhi":      ["DEL"],
    "mumbai":         ["BOM"],
    "bombay":         ["BOM"],
    "bangalore":      ["BLR"],
    "bengaluru":      ["BLR"],
    "chennai":        ["MAA"],
    "kolkata":        ["CCU"],
    "hyderabad":      ["HYD"],
    "india":          ["DEL", "BOM", "BLR", "MAA", "CCU", "HYD"],

    # ── East Asia ──
    "tokyo":          ["NRT", "HND"],
    "osaka":          ["KIX", "ITM"],
    "seoul":          ["ICN", "GMP"],
    "beijing":        ["PEK", "PKX"],
    "shanghai":       ["PVG", "SHA"],
    "hong kong":      ["HKG"],
    "taipei":         ["TPE", "TSA"],
    "singapore":      ["SIN"],
    "bangkok":        ["BKK", "DMK"],
    "kuala lumpur":   ["KUL"],
    "kl":             ["KUL"],
    "manila":         ["MNL"],
    "jakarta":        ["CGK"],
    "hanoi":          ["HAN"],
    "ho chi minh":    ["SGN"],
    "saigon":         ["SGN"],

    # ── Oceania ──
    "sydney":         ["SYD"],
    "melbourne":      ["MEL"],
    "brisbane":       ["BNE"],
    "auckland":       ["AKL"],
    "perth":          ["PER"],

    # ── Africa ──
    "cairo":          ["CAI"],
    "johannesburg":   ["JNB"],
    "nairobi":        ["NBO"],
    "lagos":          ["LOS"],
    "cape town":      ["CPT"],
    "casablanca":     ["CMN"],
    "addis ababa":    ["ADD"],

    # ── South America ──
    "sao paulo":      ["GRU", "CGH"],
    "rio de janeiro": ["GIG", "SDU"],
    "buenos aires":   ["EZE", "AEP"],
    "santiago":       ["SCL"],
    "bogota":         ["BOG"],
    "lima":           ["LIM"],
    "mexico city":    ["MEX"],
    "cancun":         ["CUN"],
    "panama city":    ["PTY"],

    # ── Country-level shortcuts ──
    "uae":            ["DXB", "AUH", "SHJ"],
    "saudi arabia":   ["RUH", "JED", "DMM"],
    "uk":             ["LHR", "LGW", "MAN", "EDI"],
    "usa":            ["JFK", "LAX", "ORD", "ATL", "DFW"],
    "japan":          ["NRT", "HND", "KIX"],
    "south korea":    ["ICN"],
    "china":          ["PEK", "PVG", "CAN"],
    "australia":      ["SYD", "MEL", "BNE"],
    "germany":        ["FRA", "MUC", "BER"],
    "france":         ["CDG", "ORY"],
    "italy":          ["FCO", "MXP"],
    "spain":          ["MAD", "BCN"],
    "turkey":         ["IST"],
    "canada":         ["YYZ", "YVR", "YUL"],
    "brazil":         ["GRU", "GIG"],
    "qatar":          ["DOH"],
}

# ── IATA code → readable name lookup (built from Airport enum) ───────────────
IATA_TO_NAME: dict[str, str] = {}
IATA_CODES: set[str] = set()   # quick membership check
for member in Airport:
    iata = member.value
    IATA_CODES.add(iata)
    readable = member.name.replace("_", " ").title()
    IATA_TO_NAME[iata] = readable


def parse_price(price_str: str) -> float:
    """Parse a price string like '$123', 'PKR\xa041035', 'EUR 500' into a float.
    Strips all non-numeric characters except the decimal point."""
    import re
    cleaned = re.sub(r'[^\d.]', '', price_str)
    return float(cleaned) if cleaned else float('inf')


# Helper Functions

def format_flight_info(flight_data, origin_airport, destination_airport):
    """
    Formats flight information into a human-readable string.

    Args:
        flight_data: Dictionary containing flight information
        origin_airport: Name of Origin airport city and IATA code (ex: "Seattle (SEA)")
        destination_airport: Name of Destination airport city and IATA code (ex: "Tokyo (HND)")

    Returns:
        Formatted string describing the flight
    """
    
    duration_parts = flight_data['duration'].split()
    
    if len(duration_parts) == 4:
        duration_formatted = f"{duration_parts[0]} hours and {duration_parts[2]} minutes"
    else:
        duration_formatted = flight_data['duration']
    
    # Reformat departure and arrival dates
    def expand_date(date_str):
        # Map abbreviated month and day
        month_map = {
            'Jan': 'January', 'Feb': 'February', 'Mar': 'March', 
            'Apr': 'April', 'May': 'May', 'Jun': 'June', 
            'Jul': 'July', 'Aug': 'August', 'Sep': 'September', 
            'Oct': 'October', 'Nov': 'November', 'Dec': 'December'
        }
        day_map = {'Mon': 'Monday', 'Tue': 'Tuesday', 'Wed': 'Wednesday', 
                   'Thu': 'Thursday', 'Fri': 'Friday', 'Sat': 'Saturday', 
                   'Sun': 'Sunday'}
        
        parts = date_str.split()
        time = f"{parts[0]} {parts[1]}"  # "9:40 AM"
        
        # Handle the day abbreviation (removing the comma)
        day_abbr = parts[3].rstrip(',')  # "Sat" (removing comma from "Sat,")
        month_abbr = parts[4]  # "Apr"
        day = parts[5]  # "5"
        
        full_day = day_map.get(day_abbr, day_abbr)
        full_month = month_map.get(month_abbr, month_abbr)
        
        # Add ordinal suffix to the day
        day_with_suffix = day + ('th' if not day.endswith(('1', '2', '3')) or day.endswith(('11', '12', '13')) else 
                                 ('st' if day.endswith('1') else 
                                  ('nd' if day.endswith('2') else 
                                   ('rd' if day.endswith('3') else 'th'))))
        
        return f"{time} on {full_day}, {full_month} {day_with_suffix}"
    
    # Determine best flight qualifier
    best_flight_qualifier = "considered one of the best options by Google Flights" if flight_data['is_best'] else "an available option"
    
    # Handle potential None or empty values
    stops = flight_data["stops"]
    stops_text = f"{stops} stop{'s' if stops != 1 else ''}" if stops > 0 else "non-stop"
    
    formatted_string = (
        f"This flight departs at {expand_date(flight_data['departure'])} from {origin_airport}, local time, "
        f"and arrives at {expand_date(flight_data['arrival'])} in {destination_airport}, local time. "
        f"The flight is operated by {flight_data['name']} and has a duration of {duration_formatted} "
        f"with {stops_text} in between. "
        f"And it's price is {flight_data['price']} and is {best_flight_qualifier}!"
    )
    
    return formatted_string





# Main Functions

@mcp.tool()
async def get_airport(city_or_airport_name: str) -> str:
    """Search for airports by city name, country name, or IATA code.

    ⚡ ALWAYS call this tool FIRST before searching for flights, even if you
    think you know the IATA code.  It handles cities with multiple airports
    (e.g. "New York" → JFK, EWR, LGA) and common abbreviations.

    Accepts any of the following inputs:
      • City name:    "New York", "Tokyo", "Karachi", "London"
      • Country name: "Pakistan", "UAE", "Japan"
      • Abbreviation: "NYC", "LA", "DC", "KL"
      • IATA code:    "JFK", "LHR", "KHI"
      • Airport name: "Heathrow", "Narita", "O'Hare"

    Args:
        city_or_airport_name (str): City, country, abbreviation, IATA code, or airport name.

    Returns:
        str: List of matching airports with IATA codes.  When a city has
             multiple airports, ALL of them are returned so you can search
             flights to each one using search_flights_multi_airport.
    """
    try:
        query = city_or_airport_name.strip()
        query_lower = query.lower()
        query_upper = query.upper()

        results: list[str] = []

        # ── Tier 1: Direct IATA code lookup ──────────────────────────────
        if len(query) == 3 and query_upper in IATA_TO_NAME:
            name = IATA_TO_NAME[query_upper]
            results.append(f"Found 1 airport matching '{query}':")
            results.append(f"1. {name} ({query_upper})")
            return "\n".join(results)

        # ── Tier 2: City / country / abbreviation mapping ────────────────
        if query_lower in CITY_AIRPORT_MAP:
            codes = CITY_AIRPORT_MAP[query_lower]
            results.append(f"Found {len(codes)} airport(s) for '{query}':")
            for idx, code in enumerate(codes, 1):
                name = IATA_TO_NAME.get(code, code)
                results.append(f"{idx}. {name} ({code})")
            if len(codes) > 1:
                results.append(
                    f"\n💡 This location has {len(codes)} airports. "
                    f"Use search_flights_multi_airport with destinations=\"{','.join(codes)}\" "
                    f"to search all of them at once."
                )
            return "\n".join(results)

        # ── Tier 3: Fallback to fast_flights search_airport() ────────────
        airports = search_airport(city_or_airport_name)
        if airports:
            results.append(f"Found {len(airports)} airport(s) matching '{city_or_airport_name}':")
            for idx, match in enumerate(airports, 1):
                readable_name = match.name.replace("_", " ").title()
                iata_code = match.value
                results.append(f"{idx}. {readable_name} ({iata_code})")
            if len(airports) > 1:
                codes = [m.value for m in airports]
                results.append(
                    f"\n💡 Multiple airports found. "
                    f"Use search_flights_multi_airport with destinations=\"{','.join(codes)}\" "
                    f"to search all of them at once."
                )
            return "\n".join(results)

        # ── Nothing found ────────────────────────────────────────────────
        return (
            f"No airports found matching '{city_or_airport_name}'.\n"
            f"Tips: Try the full city name (e.g. 'New York' instead of 'NY'), "
            f"the airport name (e.g. 'Heathrow'), or a 3-letter IATA code (e.g. 'LHR')."
        )

    except Exception as e:
        return f"An error occurred while searching for the airport: {str(e)}"


@mcp.tool()
async def get_current_date() -> str:
    """Get today's date in YYYY-MM-DD format.

    ⚡ ALWAYS call this BEFORE making any flight search so you know the
    current year and can validate that departure dates are in the future.
    """
    return datetime.now().strftime("%Y-%m-%d")


@mcp.tool()
async def get_general_flights_info(origin: str, destination: str, departure_date: str,
                      trip_type: str = "one-way", seat: str = "economy",
                      adults: int = 1, children: int = 0, infants_in_seat: int = 0, infants_on_lap: int = 0,
                      n_flights: int = 40) -> list[str]:
    """Get comprehensive flight information for a single origin→destination route on one date.

    ⚡ BEFORE calling this tool:
      1. Call get_current_date to know today's date.
      2. Call get_airport for BOTH origin and destination to get valid IATA codes.
      3. For cities with multiple airports, use search_flights_multi_airport instead.
      4. For round-trips, make two separate one-way calls (outbound + return).
      5. For multiple dates, use search_flights_multi_date instead.

    Args:
        origin (str): 3-letter IATA code of the origin airport (e.g. "ISB", "JFK", "LHR"). Must be obtained from get_airport.
        destination (str): 3-letter IATA code of the destination airport (e.g. "DXB", "CDG"). Must be obtained from get_airport.
        departure_date (str): Departure date in YYYY-MM-DD format. Must be today or in the future.
        trip_type (str, optional): "one-way" or "round-trip". Defaults to "one-way".
        seat (str, optional): "economy", "premium-economy", "business", or "first". Defaults to "economy".
        adults (int, optional): Number of adult passengers. Defaults to 1.
        children (int, optional): Number of children. Defaults to 0.
        infants_in_seat (int, optional): Number of infants in a seat. Defaults to 0.
        infants_on_lap (int, optional): Number of infants on a lap. Defaults to 0.
        n_flights (int, optional): Max number of flights to return. Defaults to 40.

    Returns:
        list[str]: A list of human-readable flight information strings.
    """

    if (len(origin) != 3 or len(destination) != 3):
        return ["Origin and destination must be 3 characters."]
    
    if (len(departure_date) != 10 or departure_date[4] != '-' or departure_date[7] != '-'):
        return ["Departure date must be in YYYY-MM-DD format."]
    
    if (trip_type != "one-way" and trip_type != "round-trip"):
        return ["Trip type must be either 'one-way' or 'round-trip'."]
    
    if (seat != "economy" and seat != "premium-economy" and seat != "business" and seat != "first"):
        return ["Seat type must be either 'economy', 'premium-economy', 'business', or 'first'."]
    

    try:
        
        # Make API call to Google Flights via fast-flights

        flight_data_input = [FlightData(date=departure_date, from_airport=origin, to_airport=destination)]
        
        passengers_input = Passengers(adults=adults, children=children, infants_in_seat=infants_in_seat, infants_on_lap=infants_on_lap)

        result: Result = get_flights(
            flight_data=flight_data_input,
            trip=trip_type,
            seat=seat,
            passengers=passengers_input,
            fetch_mode="fallback"
        )
        
        result = asdict(result)
        
        if not result or "flights" not in result:
            return ["No flight data available for the specified route and dates."]

        current_price = result["current_price"]
        all_flights = result["flights"]

        if not all_flights:
            return ["No flights found for the specified route and dates."]

        top_n_flights = all_flights[0: min(n_flights, len(all_flights))]

        flight_info = []

        origin_airport = origin
        destination_airport = destination

        for flight in top_n_flights:
            flight_info.append(format_flight_info(flight, origin_airport, destination_airport))

        output = [f"The current overall flight prices for this route and time are: {str(current_price)}."] + flight_info


        return output


    except httpx.RequestError:
        return ["Unable to connect to the flight search service. Please try again later."]
    
    except ValueError as e:
        return [f"Invalid data received: {str(e)}"]
    
    except Exception as e:
        return [f"An unexpected error occurred while searching for flights: {str(e)}"]



@mcp.tool()
async def get_cheapest_flights(origin: str, destination: str, departure_date: str,
                      trip_type: str = "one-way", seat: str = "economy",
                      adults: int = 1, children: int = 0, infants_in_seat: int = 0, infants_on_lap: int = 0) -> list[str]:
   
    """Get the cheapest flights sorted by price for a single route and date.

    ⚡ BEFORE calling this tool:
      1. Call get_current_date to know today's date.
      2. Call get_airport for BOTH origin and destination to get valid IATA codes.
      3. For cities with multiple airports, use search_flights_multi_airport instead.
      4. For round-trips, make two separate one-way calls.
      5. For comparing prices across dates, use search_flights_multi_date instead.

    Args:
        origin (str): 3-letter IATA code of the origin airport. Must be obtained from get_airport.
        destination (str): 3-letter IATA code of the destination airport. Must be obtained from get_airport.
        departure_date (str): Departure date in YYYY-MM-DD format.
        trip_type (str, optional): "one-way" or "round-trip". Defaults to "one-way".
        seat (str, optional): "economy", "premium-economy", "business", or "first". Defaults to "economy".
        adults (int, optional): Number of adult passengers. Defaults to 1.
        children (int, optional): Number of children. Defaults to 0.
        infants_in_seat (int, optional): Number of infants in a seat. Defaults to 0.
        infants_on_lap (int, optional): Number of infants on a lap. Defaults to 0.

    Returns:
        list[str]: Flights sorted from cheapest to most expensive.
    """

    if (len(origin) != 3 or len(destination) != 3):
        return ["Origin and destination must be 3 characters."]
    
    if (len(departure_date) != 10 or departure_date[4] != '-' or departure_date[7] != '-'):
        return ["Departure date must be in YYYY-MM-DD format."]
    
    if (trip_type != "one-way" and trip_type != "round-trip"):
        return ["Trip type must be either 'one-way' or 'round-trip'."]
    
    if (seat != "economy" and seat != "premium-economy" and seat != "business" and seat != "first"):
        return ["Seat type must be either 'economy', 'premium-economy', 'business', or 'first'."]

    try:
        # Make API call to Google Flights via fast-flights

        flight_data_input = [FlightData(date=departure_date, from_airport=origin, to_airport=destination)]
        passengers_input = Passengers(adults=adults, children=children, infants_in_seat=infants_in_seat, infants_on_lap=infants_on_lap)

        result: Result = get_flights(
            flight_data=flight_data_input,
            trip=trip_type,
            seat=seat,
            passengers=passengers_input,
            fetch_mode="fallback"
        )
        
        result = asdict(result)
        
        if not result or "flights" not in result:
            return ["No flight data available for the specified route and dates."]

        all_flights = result["flights"]

        if not all_flights:
            return ["No flights found for the specified route and dates."]

        def get_price_value(flight):
            return parse_price(flight['price'])

        price_sorted_flights = sorted(all_flights, key=get_price_value)

        top_n_flights = price_sorted_flights[0: min(30, len(price_sorted_flights))]

        flight_info = []

        origin_airport = origin
        destination_airport = destination

        for flight in top_n_flights:
            flight_info.append(format_flight_info(flight, origin_airport, destination_airport))

        output = ["Here are the cheapest flights for this route and time: "] + flight_info

        print(output)
        return output



    except httpx.RequestError:
        return ["Unable to connect to the flight search service. Please try again later."]
    
    except ValueError as e:
        return [f"Invalid data received: {str(e)}"]
    
    except Exception as e:
        return [f"An unexpected error occurred while searching for flights: {str(e)}"]


@mcp.tool()
async def get_best_flights(origin: str, destination: str, departure_date: str,
                      trip_type: str = "one-way", seat: str = "economy",
                      adults: int = 1, children: int = 0, infants_in_seat: int = 0, infants_on_lap: int = 0) -> list[str]:
   
    """Get the best flights as ranked by Google Flights for a single route and date.

    Google Flights considers a combination of price, duration, and number of
    stops to determine "best" flights.

    ⚡ BEFORE calling this tool:
      1. Call get_current_date to know today's date.
      2. Call get_airport for BOTH origin and destination to get valid IATA codes.
      3. For cities with multiple airports, use search_flights_multi_airport instead.
      4. For round-trips, make two separate one-way calls.

    Args:
        origin (str): 3-letter IATA code of the origin airport. Must be obtained from get_airport.
        destination (str): 3-letter IATA code of the destination airport. Must be obtained from get_airport.
        departure_date (str): Departure date in YYYY-MM-DD format.
        trip_type (str, optional): "one-way" or "round-trip". Defaults to "one-way".
        seat (str, optional): "economy", "premium-economy", "business", or "first". Defaults to "economy".
        adults (int, optional): Number of adult passengers. Defaults to 1.
        children (int, optional): Number of children. Defaults to 0.
        infants_in_seat (int, optional): Number of infants in a seat. Defaults to 0.
        infants_on_lap (int, optional): Number of infants on a lap. Defaults to 0.

    Returns:
        list[str]: The best-ranked flights for this route.
    """

    if (len(origin) != 3 or len(destination) != 3):
        return ["Origin and destination must be 3 characters."]
    
    if (len(departure_date) != 10 or departure_date[4] != '-' or departure_date[7] != '-'):
        return ["Departure date must be in YYYY-MM-DD format."]
    
    if (trip_type != "one-way" and trip_type != "round-trip"):
        return ["Trip type must be either 'one-way' or 'round-trip'."]
    
    if (seat != "economy" and seat != "premium-economy" and seat != "business" and seat != "first"):
        return ["Seat type must be either 'economy', 'premium-economy', 'business', or 'first'."]

    try:
        # Make API call to Google Flights via fast-flights

        flight_data_input = [FlightData(date=departure_date, from_airport=origin, to_airport=destination)]

        passengers_input = Passengers(adults=adults, children=children, infants_in_seat=infants_in_seat, infants_on_lap=infants_on_lap)

        result: Result = get_flights(
            flight_data=flight_data_input,
            trip=trip_type,
            seat=seat,
            passengers=passengers_input,
            fetch_mode="fallback"
        )
        
        result = asdict(result)
        
        if not result or "flights" not in result:
            return ["No flight data available for the specified route and dates."]

        all_flights = result["flights"]

        if not all_flights:
            return ["No flights found for the specified route and dates."]

        best_flights = []

        for flight in all_flights:
            if (flight['is_best']):
                best_flights.append(flight)
        
        if not best_flights:
            return ["No best flights found for the specified route and dates."]


        top_n_flights = best_flights[0: min(30, len(best_flights))]

        flight_info = []

        origin_airport = origin
        destination_airport = destination

        for flight in top_n_flights:
            flight_info.append(format_flight_info(flight, origin_airport, destination_airport))

        output = ["Here are the best flights for this route and time: "] + flight_info

        print(output)
        return output
    



    except httpx.RequestError:
        return ["Unable to connect to the flight search service. Please try again later."]
    
    except ValueError as e:
        return [f"Invalid data received: {str(e)}"]
    
    except Exception as e:
        return [f"An unexpected error occurred while searching for flights: {str(e)}"]
    


@mcp.tool()
async def get_time_filtered_flights(state: str, target_time_str: str, origin: str, destination: str, departure_date: str,
                      trip_type: str = "one-way", seat: str = "economy",
                      adults: int = 1, children: int = 0, infants_in_seat: int = 0, infants_on_lap: int = 0) -> list[str]:
   
    """Get flights filtered by departure time (before or after a given time).

    Use this when the user has a time preference, e.g. "flights after 6 PM"
    or "morning flights before 10 AM".

    ⚡ BEFORE calling this tool:
      1. Call get_current_date to know today's date.
      2. Call get_airport for BOTH origin and destination to get valid IATA codes.
      3. For round-trips, make two separate one-way calls.

    Args:
        state (str): "before" or "after". "before" = departing before the target time. "after" = departing on or after the target time.
        target_time_str (str): Target time in HH:MM AM/PM format (e.g. "7:00 PM", "9:30 AM").
        origin (str): 3-letter IATA code of the origin airport. Must be obtained from get_airport.
        destination (str): 3-letter IATA code of the destination airport. Must be obtained from get_airport.
        departure_date (str): Departure date in YYYY-MM-DD format.
        trip_type (str, optional): "one-way" or "round-trip". Defaults to "one-way".
        seat (str, optional): "economy", "premium-economy", "business", or "first". Defaults to "economy".
        adults (int, optional): Number of adult passengers. Defaults to 1.
        children (int, optional): Number of children. Defaults to 0.
        infants_in_seat (int, optional): Number of infants in a seat. Defaults to 0.
        infants_on_lap (int, optional): Number of infants on a lap. Defaults to 0.

    Returns:
        list[str]: Flights matching the time filter.
    """

    if (len(origin) != 3 or len(destination) != 3):
        return ["Origin and destination must be 3 characters."]
    
    if (len(departure_date) != 10 or departure_date[4] != '-' or departure_date[7] != '-'):
        return ["Departure date must be in YYYY-MM-DD format."]
    
    if (trip_type != "one-way" and trip_type != "round-trip"):
        return ["Trip type must be either 'one-way' or 'round-trip'."]
    
    if (seat != "economy" and seat != "premium-economy" and seat != "business" and seat != "first"):
        return ["Seat type must be either 'economy', 'premium-economy', 'business', or 'first'."]
    
    if (state != "before" and state != "after"):
        return ["State must be either 'before' or 'after'."]

    try:
        # Validate time format first

        try:
            target_time = datetime.strptime(target_time_str, '%I:%M %p').time()
        except ValueError:
            return ["Invalid time format. Please use HH:MM AM/PM format (e.g., '7:00 PM')."]


        # Make API call to Google Flights via fast-flights
        flight_data_input = [FlightData(date=departure_date, from_airport=origin, to_airport=destination)]

        passengers_input = Passengers(adults=adults, children=children, infants_in_seat=infants_in_seat, infants_on_lap=infants_on_lap)

        result: Result = get_flights(
            flight_data=flight_data_input,
            trip=trip_type,
            seat=seat,
            passengers=passengers_input,
            fetch_mode="fallback"
        )
        
        result = asdict(result)
        
        if not result or "flights" not in result:
            return ["No flight data available for the specified route and dates."]


        all_flights = result["flights"]

        if not all_flights:
            return ["No flights found for the specified route and dates."]


        valid_flights = []
        
        for flight in all_flights:

            parts = flight['departure'].split(" ")
            time_str = parts[0] + " " + parts[1]

            flight_time = datetime.strptime(time_str, '%I:%M %p').time()

            if (state == "before"):
                if (flight_time < target_time):
                    valid_flights.append(flight)
            elif (state == "after"):
                if (flight_time >= target_time):
                    valid_flights.append(flight)

        if not valid_flights:
            return [f"No flights found {state} {target_time_str} for the specified route and dates."]


        top_n_flights = valid_flights[0: min(30, len(valid_flights))]

        flight_info = []

        origin_airport = origin
        destination_airport = destination

        for flight in top_n_flights:
            flight_info.append(format_flight_info(flight, origin_airport, destination_airport))

        context_str = f"Here are the time-filtered flights {('before' if state == 'before' else 'on or after')} {target_time_str}: "

        output = [context_str] + flight_info

        print(output)
        return output


    except httpx.RequestError:
        return ["Unable to connect to the flight search service. Please try again later."]
    
    except ValueError as e:
        return [f"Invalid data received: {str(e)}"]
    
    except Exception as e:
        return [f"An unexpected error occurred while searching for flights: {str(e)}"]
    

# ── New Tools: Date Range & Multi-Airport/Date Search ────────────────────────

@mcp.tool()
async def get_date_range(start_date: str, end_date: str) -> list[str]:
    """Generate a list of dates between start_date and end_date (inclusive).

    Use this when the user wants to compare flights across several days,
    e.g. "find the cheapest day to fly next week".

    The output can be passed directly to search_flights_multi_date.
    Maximum range is 7 days to keep results manageable.

    Args:
        start_date (str): Start date in YYYY-MM-DD format.
        end_date (str): End date in YYYY-MM-DD format (inclusive).

    Returns:
        list[str]: List of dates in YYYY-MM-DD format.
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        if end < start:
            return ["Error: end_date must be on or after start_date."]

        delta_days = (end - start).days
        if delta_days > 7:
            return [
                f"Error: Date range is {delta_days} days. Maximum allowed is 7 days. "
                f"Please narrow the range."
            ]

        dates = []
        current = start
        while current <= end:
            dates.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)

        return dates

    except ValueError:
        return ["Error: Dates must be in YYYY-MM-DD format."]


@mcp.tool()
async def search_flights_multi_airport(
    origin: str,
    destinations: str,
    departure_date: str,
    trip_type: str = "one-way",
    seat: str = "economy",
    adults: int = 1,
    children: int = 0,
    infants_in_seat: int = 0,
    infants_on_lap: int = 0,
) -> list[str]:
    """Search flights across MULTIPLE destination airports in one call.

    Use this when a city has several airports (e.g. London → LHR, LGW, STN)
    or when comparing routes to nearby airports. The get_airport tool will
    suggest using this tool when multiple airports are found.

    Results from all airports are combined and clearly labeled so the user
    can compare.

    ⚡ BEFORE calling this tool:
      1. Call get_current_date.
      2. Call get_airport for origin (single IATA code).
      3. Call get_airport for the destination city/country — it will return
         all airport codes and suggest using this tool.

    Args:
        origin (str): 3-letter IATA code of the origin airport (single airport).
        destinations (str): Comma-separated IATA codes of destination airports
                            (e.g. "JFK,EWR,LGA" or "LHR,LGW,STN").
        departure_date (str): Departure date in YYYY-MM-DD format.
        trip_type (str, optional): "one-way" or "round-trip". Defaults to "one-way".
        seat (str, optional): "economy", "premium-economy", "business", or "first". Defaults to "economy".
        adults (int, optional): Number of adult passengers. Defaults to 1.
        children (int, optional): Number of children. Defaults to 0.
        infants_in_seat (int, optional): Number of infants in a seat. Defaults to 0.
        infants_on_lap (int, optional): Number of infants on a lap. Defaults to 0.

    Returns:
        list[str]: Combined flight results from all destination airports, labeled by airport.
    """
    dest_codes = [d.strip().upper() for d in destinations.split(",") if d.strip()]

    if not dest_codes:
        return ["Error: Please provide at least one destination IATA code."]

    if len(origin) != 3:
        return ["Error: Origin must be a 3-letter IATA code."]

    combined_output: list[str] = []

    for dest in dest_codes:
        if len(dest) != 3:
            combined_output.append(f"\n⚠️ Skipping invalid code '{dest}' (must be 3 letters).")
            continue

        dest_name = IATA_TO_NAME.get(dest, dest)
        origin_name = IATA_TO_NAME.get(origin.upper(), origin)

        try:
            flight_data_input = [FlightData(date=departure_date, from_airport=origin, to_airport=dest)]
            passengers_input = Passengers(
                adults=adults, children=children,
                infants_in_seat=infants_in_seat, infants_on_lap=infants_on_lap
            )

            result: Result = get_flights(
                flight_data=flight_data_input,
                trip=trip_type,
                seat=seat,
                passengers=passengers_input,
                fetch_mode="fallback"
            )
            result = asdict(result)

            flights = result.get("flights", [])
            if not flights:
                combined_output.append(f"\n✈️ {dest_name} ({dest}): No flights found.")
                continue

            combined_output.append(f"\n✈️ {dest_name} ({dest}): Found {len(flights)} flight(s)")

            current_price = result.get("current_price", "N/A")
            combined_output.append(f"   Current price level: {current_price}")

            for flight in flights[:10]:  # Cap at 10 per airport to keep output manageable
                combined_output.append(format_flight_info(flight, f"{origin_name} ({origin})", f"{dest_name} ({dest})"))

        except Exception as e:
            combined_output.append(f"\n⚠️ {dest_name} ({dest}): Error — {str(e)}")

    if not combined_output:
        return ["No flights found for any of the specified destination airports."]

    header = f"Flight results from {IATA_TO_NAME.get(origin.upper(), origin)} ({origin}) to {len(dest_codes)} airport(s) on {departure_date}:"
    return [header] + combined_output


@mcp.tool()
async def search_flights_multi_date(
    origin: str,
    destination: str,
    departure_dates: str,
    trip_type: str = "one-way",
    seat: str = "economy",
    adults: int = 1,
    children: int = 0,
    infants_in_seat: int = 0,
    infants_on_lap: int = 0,
) -> list[str]:
    """Search flights for the SAME route across MULTIPLE dates to compare prices.

    Use this when the user wants to find the cheapest day to fly, e.g.
    "find flights from Islamabad to Dubai between March 5 and March 10".

    ⚡ WORKFLOW:
      1. Call get_current_date.
      2. Call get_airport for origin and destination.
      3. Call get_date_range to generate the list of dates.
      4. Pass the comma-separated dates to this tool.

    Args:
        origin (str): 3-letter IATA code of the origin airport.
        destination (str): 3-letter IATA code of the destination airport.
        departure_dates (str): Comma-separated dates in YYYY-MM-DD format
                               (e.g. "2026-03-05,2026-03-06,2026-03-07"). Max 7 dates.
        trip_type (str, optional): "one-way" or "round-trip". Defaults to "one-way".
        seat (str, optional): "economy", "premium-economy", "business", or "first". Defaults to "economy".
        adults (int, optional): Number of adult passengers. Defaults to 1.
        children (int, optional): Number of children. Defaults to 0.
        infants_in_seat (int, optional): Number of infants in a seat. Defaults to 0.
        infants_on_lap (int, optional): Number of infants on a lap. Defaults to 0.

    Returns:
        list[str]: Flight results grouped by date, with a price comparison summary.
    """
    date_list = [d.strip() for d in departure_dates.split(",") if d.strip()]

    if not date_list:
        return ["Error: Please provide at least one departure date."]

    if len(date_list) > 7:
        return ["Error: Maximum 7 dates allowed. Please narrow the range."]

    if len(origin) != 3 or len(destination) != 3:
        return ["Error: Origin and destination must be 3-letter IATA codes."]

    origin_name = IATA_TO_NAME.get(origin.upper(), origin)
    dest_name = IATA_TO_NAME.get(destination.upper(), destination)
    combined_output: list[str] = []
    date_cheapest: list[tuple[str, str]] = []  # (date, cheapest_price)

    for date in date_list:
        try:
            flight_data_input = [FlightData(date=date, from_airport=origin, to_airport=destination)]
            passengers_input = Passengers(
                adults=adults, children=children,
                infants_in_seat=infants_in_seat, infants_on_lap=infants_on_lap
            )

            result: Result = get_flights(
                flight_data=flight_data_input,
                trip=trip_type,
                seat=seat,
                passengers=passengers_input,
                fetch_mode="fallback"
            )
            result = asdict(result)

            flights = result.get("flights", [])
            current_price = result.get("current_price", "N/A")

            if not flights:
                combined_output.append(f"\n📅 {date}: No flights found.")
                continue

            # Find cheapest flight for this date
            cheapest_price = None
            for f in flights:
                try:
                    p = parse_price(f["price"])
                    if cheapest_price is None or p < cheapest_price:
                        cheapest_price = p
                except (ValueError, KeyError):
                    pass

            price_str = f"${cheapest_price:,.0f}" if cheapest_price else "N/A"
            date_cheapest.append((date, price_str))

            combined_output.append(f"\n📅 {date}: {len(flights)} flight(s) found | Cheapest: {price_str} | Price level: {current_price}")

            # Show top 5 flights per date
            for flight in flights[:5]:
                combined_output.append(format_flight_info(flight, f"{origin_name} ({origin})", f"{dest_name} ({destination})"))

        except Exception as e:
            combined_output.append(f"\n📅 {date}: Error — {str(e)}")

    # Add price comparison summary at the top
    header = f"Multi-date flight search: {origin_name} ({origin}) → {dest_name} ({destination})\n"
    if date_cheapest:
        header += "\n💰 Price Comparison Summary:\n"
        for date, price in date_cheapest:
            header += f"   {date}: {price}\n"

        # Find the cheapest date
        valid_prices = [(d, p) for d, p in date_cheapest if p != "N/A"]
        if valid_prices:
            cheapest_date = min(valid_prices, key=lambda x: parse_price(x[1]))
            header += f"\n🏆 Cheapest date: {cheapest_date[0]} at {cheapest_date[1]}"

    return [header] + combined_output


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
