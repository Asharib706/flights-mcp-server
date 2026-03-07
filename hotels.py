from typing import Any, List, Optional
import httpx
from mcp.server.fastmcp import FastMCP

from fast_hotels.hotels_impl import HotelData, Guests
from fast_hotels import get_hotels
from fast_hotels.schema import Result, Hotel
from dataclasses import asdict

from datetime import datetime, timedelta
import re


# initialize the MCP server
mcp = FastMCP("hotels")


# ── City / Location mapping ─────────────────────────────────────────────────
# Maps common city names, abbreviations, and country names to their
# Google Hotels-compatible location strings.

CITY_LOCATION_MAP: dict[str, str] = {
    # ── United States ──
    "new york":       "New York",
    "nyc":            "New York",
    "los angeles":    "Los Angeles",
    "la":             "Los Angeles",
    "san francisco":  "San Francisco",
    "sf":             "San Francisco",
    "chicago":        "Chicago",
    "miami":          "Miami",
    "washington":     "Washington DC",
    "washington dc":  "Washington DC",
    "dc":             "Washington DC",
    "dallas":         "Dallas",
    "houston":        "Houston",
    "atlanta":        "Atlanta",
    "boston":          "Boston",
    "seattle":        "Seattle",
    "denver":         "Denver",
    "phoenix":        "Phoenix",
    "orlando":        "Orlando",
    "las vegas":      "Las Vegas",
    "honolulu":       "Honolulu",
    "portland":       "Portland",
    "san diego":      "San Diego",
    "austin":         "Austin",
    "nashville":      "Nashville",

    # ── Canada ──
    "toronto":        "Toronto",
    "vancouver":      "Vancouver",
    "montreal":       "Montreal",
    "calgary":        "Calgary",
    "ottawa":         "Ottawa",

    # ── United Kingdom ──
    "london":         "London",
    "manchester":     "Manchester",
    "birmingham":     "Birmingham",
    "edinburgh":      "Edinburgh",
    "glasgow":        "Glasgow",

    # ── Europe ──
    "paris":          "Paris",
    "amsterdam":      "Amsterdam",
    "frankfurt":      "Frankfurt",
    "munich":         "Munich",
    "berlin":         "Berlin",
    "rome":           "Rome",
    "milan":          "Milan",
    "madrid":         "Madrid",
    "barcelona":      "Barcelona",
    "zurich":         "Zurich",
    "vienna":         "Vienna",
    "brussels":       "Brussels",
    "lisbon":         "Lisbon",
    "copenhagen":     "Copenhagen",
    "oslo":           "Oslo",
    "stockholm":      "Stockholm",
    "helsinki":        "Helsinki",
    "dublin":         "Dublin",
    "athens":         "Athens",
    "istanbul":       "Istanbul",
    "moscow":         "Moscow",
    "prague":         "Prague",
    "warsaw":         "Warsaw",
    "budapest":       "Budapest",

    # ── Middle East ──
    "dubai":          "Dubai",
    "abu dhabi":      "Abu Dhabi",
    "doha":           "Doha",
    "riyadh":         "Riyadh",
    "jeddah":         "Jeddah",
    "muscat":         "Muscat",
    "kuwait":         "Kuwait City",
    "bahrain":        "Bahrain",
    "amman":          "Amman",
    "beirut":         "Beirut",
    "tel aviv":       "Tel Aviv",

    # ── Pakistan ──
    "karachi":        "Karachi",
    "lahore":         "Lahore",
    "islamabad":      "Islamabad",
    "peshawar":       "Peshawar",
    "quetta":         "Quetta",
    "multan":         "Multan",
    "faisalabad":     "Faisalabad",

    # ── India ──
    "delhi":          "New Delhi",
    "new delhi":      "New Delhi",
    "mumbai":         "Mumbai",
    "bombay":         "Mumbai",
    "bangalore":      "Bangalore",
    "bengaluru":      "Bangalore",
    "chennai":        "Chennai",
    "kolkata":        "Kolkata",
    "hyderabad":      "Hyderabad",
    "goa":            "Goa",

    # ── East Asia ──
    "tokyo":          "Tokyo",
    "osaka":          "Osaka",
    "kyoto":          "Kyoto",
    "seoul":          "Seoul",
    "beijing":        "Beijing",
    "shanghai":       "Shanghai",
    "hong kong":      "Hong Kong",
    "taipei":         "Taipei",
    "singapore":      "Singapore",
    "bangkok":        "Bangkok",
    "kuala lumpur":   "Kuala Lumpur",
    "kl":             "Kuala Lumpur",
    "manila":         "Manila",
    "jakarta":        "Jakarta",
    "hanoi":          "Hanoi",
    "ho chi minh":    "Ho Chi Minh City",
    "saigon":         "Ho Chi Minh City",
    "bali":           "Bali",
    "phuket":         "Phuket",

    # ── Oceania ──
    "sydney":         "Sydney",
    "melbourne":      "Melbourne",
    "brisbane":       "Brisbane",
    "auckland":       "Auckland",
    "perth":          "Perth",

    # ── Africa ──
    "cairo":          "Cairo",
    "johannesburg":   "Johannesburg",
    "nairobi":        "Nairobi",
    "lagos":          "Lagos",
    "cape town":      "Cape Town",
    "casablanca":     "Casablanca",
    "marrakech":      "Marrakech",

    # ── South America ──
    "sao paulo":      "Sao Paulo",
    "rio de janeiro": "Rio de Janeiro",
    "buenos aires":   "Buenos Aires",
    "santiago":       "Santiago",
    "bogota":         "Bogota",
    "lima":           "Lima",
    "mexico city":    "Mexico City",
    "cancun":         "Cancun",
}


def resolve_location(location: str) -> str:
    """Resolve a location string to a Google Hotels-compatible location name.

    Checks the curated CITY_LOCATION_MAP first, then falls back to using
    the raw input (which works for most city names and IATA codes since
    the fast-hotels library handles IATA→city conversion internally).
    """
    query_lower = location.strip().lower()
    if query_lower in CITY_LOCATION_MAP:
        return CITY_LOCATION_MAP[query_lower]
    # Return as-is — the fast-hotels library can handle IATA codes and city names directly
    return location.strip()


def parse_price(price_val) -> float:
    """Parse a price value (float, int, or string) into a float.
    Returns inf for unparseable values."""
    if isinstance(price_val, (int, float)):
        return float(price_val)
    if isinstance(price_val, str):
        cleaned = re.sub(r'[^\d.]', '', price_val)
        return float(cleaned) if cleaned else float('inf')
    return float('inf')


def format_hotel_info(hotel: dict) -> str:
    """Formats hotel information into a human-readable string.

    Args:
        hotel: Dictionary containing hotel information with keys:
               name, price, rating, amenities, url

    Returns:
        Formatted string describing the hotel.
    """
    name = hotel.get("name", "Unknown Hotel")
    price = hotel.get("price")
    rating = hotel.get("rating")
    amenities = hotel.get("amenities", [])
    url = hotel.get("url")

    parts = [f"🏨 **{name}**"]

    if price is not None:
        parts.append(f"   💰 Price: ${price:,.2f} per night")

    if rating is not None:
        # Star rating visual
        full_stars = int(rating)
        star_display = "⭐" * full_stars
        parts.append(f"   ⭐ Rating: {rating}/5 {star_display}")

    if amenities:
        amenities_str = ", ".join(amenities[:8])  # Cap at 8 amenities for readability
        parts.append(f"   🛎️ Amenities: {amenities_str}")

    if url:
        parts.append(f"   🔗 URL: {url}")

    return "\n".join(parts)


def validate_dates(checkin_date: str, checkout_date: str) -> str | None:
    """Validate check-in and check-out dates. Returns error message or None."""
    date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    if not date_pattern.match(checkin_date):
        return "Check-in date must be in YYYY-MM-DD format."
    if not date_pattern.match(checkout_date):
        return "Check-out date must be in YYYY-MM-DD format."

    try:
        checkin = datetime.strptime(checkin_date, "%Y-%m-%d")
        checkout = datetime.strptime(checkout_date, "%Y-%m-%d")
    except ValueError:
        return "Invalid date values. Please use valid YYYY-MM-DD dates."

    if checkout <= checkin:
        return "Check-out date must be after check-in date."

    if (checkout - checkin).days > 30:
        return "Maximum stay is 30 nights. Please narrow your date range."

    return None


def fetch_hotels(
    location: str,
    checkin_date: str,
    checkout_date: str,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    room_type: str = "standard",
    amenities: list[str] | None = None,
    limit: int | None = None,
    sort_by: str | None = None,
) -> Result:
    """Internal helper to call the fast-hotels library.

    Returns a Result object with .hotels list.
    """
    resolved_location = resolve_location(location)

    hotel_data = [
        HotelData(
            checkin_date=checkin_date,
            checkout_date=checkout_date,
            location=resolved_location,
            room_type=room_type,
            amenities=amenities,
        )
    ]

    guests = Guests(adults=adults, children=children, infants=infants)

    result = get_hotels(
        hotel_data=hotel_data,
        guests=guests,
        room_type=room_type,
        amenities=amenities,
        fetch_mode="fallback",
        limit=limit,
        sort_by=sort_by,
    )

    return result


def hotels_to_dicts(hotels: list) -> list[dict]:
    """Convert Hotel objects to dictionaries for processing."""
    result = []
    for h in hotels:
        result.append({
            "name": h.name,
            "price": h.price,
            "rating": h.rating,
            "amenities": h.amenities if h.amenities else [],
            "url": h.url,
        })
    return result


# ══════════════════════════════════════════════════════════════════════════════
# MCP Tools
# ══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def search_hotels(
    location: str,
    checkin_date: str,
    checkout_date: str,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    room_type: str = "standard",
    limit: int = 20,
) -> list[str]:
    """Search for hotels in a given location with check-in/check-out dates.

    This is the primary hotel search tool. It returns a list of available
    hotels with their name, price, rating, amenities, and booking URL.

    Accepts city names (e.g. "Tokyo", "New York"), abbreviations
    (e.g. "NYC", "LA"), or IATA airport codes (e.g. "HND", "JFK").

    Args:
        location (str): City name, abbreviation, or IATA airport code.
        checkin_date (str): Check-in date in YYYY-MM-DD format.
        checkout_date (str): Check-out date in YYYY-MM-DD format.
        adults (int, optional): Number of adult guests. Defaults to 1.
        children (int, optional): Number of children. Defaults to 0.
        infants (int, optional): Number of infants. Defaults to 0.
        room_type (str, optional): "standard", "deluxe", or "suite". Defaults to "standard".
        limit (int, optional): Maximum number of hotels to return. Defaults to 20.

    Returns:
        list[str]: Formatted hotel information strings.
    """
    # Validate dates
    date_error = validate_dates(checkin_date, checkout_date)
    if date_error:
        return [date_error]

    if room_type not in ("standard", "deluxe", "suite"):
        return ["Room type must be 'standard', 'deluxe', or 'suite'."]

    try:
        result = fetch_hotels(
            location=location,
            checkin_date=checkin_date,
            checkout_date=checkout_date,
            adults=adults,
            children=children,
            infants=infants,
            room_type=room_type,
            limit=limit,
        )

        if not result.hotels:
            return [f"No hotels found in '{location}' for the specified dates."]

        hotel_dicts = hotels_to_dicts(result.hotels)
        resolved = resolve_location(location)

        output = [
            f"🏨 Found {len(hotel_dicts)} hotel(s) in {resolved} "
            f"({checkin_date} → {checkout_date}):"
        ]

        if result.lowest_price:
            output[0] += f" | Lowest price: ${result.lowest_price:,.2f}"

        for hotel in hotel_dicts:
            output.append(format_hotel_info(hotel))

        return output

    except Exception as e:
        return [f"An error occurred while searching for hotels: {str(e)}"]


@mcp.tool()
async def get_cheapest_hotels(
    location: str,
    checkin_date: str,
    checkout_date: str,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    room_type: str = "standard",
    limit: int = 10,
) -> list[str]:
    """Get hotels sorted by price (cheapest first) for a given location and dates.

    Use this when the user wants to find the most affordable hotel options.

    Args:
        location (str): City name, abbreviation, or IATA airport code.
        checkin_date (str): Check-in date in YYYY-MM-DD format.
        checkout_date (str): Check-out date in YYYY-MM-DD format.
        adults (int, optional): Number of adult guests. Defaults to 1.
        children (int, optional): Number of children. Defaults to 0.
        infants (int, optional): Number of infants. Defaults to 0.
        room_type (str, optional): "standard", "deluxe", or "suite". Defaults to "standard".
        limit (int, optional): Maximum number of hotels to return. Defaults to 10.

    Returns:
        list[str]: Hotels sorted from cheapest to most expensive.
    """
    date_error = validate_dates(checkin_date, checkout_date)
    if date_error:
        return [date_error]

    if room_type not in ("standard", "deluxe", "suite"):
        return ["Room type must be 'standard', 'deluxe', or 'suite'."]

    try:
        result = fetch_hotels(
            location=location,
            checkin_date=checkin_date,
            checkout_date=checkout_date,
            adults=adults,
            children=children,
            infants=infants,
            room_type=room_type,
            sort_by="price",
        )

        if not result.hotels:
            return [f"No hotels found in '{location}' for the specified dates."]

        hotel_dicts = hotels_to_dicts(result.hotels)

        # The library sorts price descending, we want ascending (cheapest first)
        hotel_dicts.sort(key=lambda h: parse_price(h["price"]))
        hotel_dicts = hotel_dicts[:limit]

        resolved = resolve_location(location)
        output = [
            f"💰 Cheapest hotels in {resolved} "
            f"({checkin_date} → {checkout_date}):"
        ]

        for hotel in hotel_dicts:
            output.append(format_hotel_info(hotel))

        return output

    except Exception as e:
        return [f"An error occurred while searching for cheapest hotels: {str(e)}"]


@mcp.tool()
async def get_best_rated_hotels(
    location: str,
    checkin_date: str,
    checkout_date: str,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    room_type: str = "standard",
    limit: int = 10,
) -> list[str]:
    """Get hotels sorted by rating (highest rated first) for a given location and dates.

    Use this when the user cares about quality and guest ratings above all else.

    Args:
        location (str): City name, abbreviation, or IATA airport code.
        checkin_date (str): Check-in date in YYYY-MM-DD format.
        checkout_date (str): Check-out date in YYYY-MM-DD format.
        adults (int, optional): Number of adult guests. Defaults to 1.
        children (int, optional): Number of children. Defaults to 0.
        infants (int, optional): Number of infants. Defaults to 0.
        room_type (str, optional): "standard", "deluxe", or "suite". Defaults to "standard".
        limit (int, optional): Maximum number of hotels to return. Defaults to 10.

    Returns:
        list[str]: Hotels sorted from highest to lowest rating.
    """
    date_error = validate_dates(checkin_date, checkout_date)
    if date_error:
        return [date_error]

    if room_type not in ("standard", "deluxe", "suite"):
        return ["Room type must be 'standard', 'deluxe', or 'suite'."]

    try:
        result = fetch_hotels(
            location=location,
            checkin_date=checkin_date,
            checkout_date=checkout_date,
            adults=adults,
            children=children,
            infants=infants,
            room_type=room_type,
            sort_by="rating",
        )

        if not result.hotels:
            return [f"No hotels found in '{location}' for the specified dates."]

        hotel_dicts = hotels_to_dicts(result.hotels)
        hotel_dicts = hotel_dicts[:limit]

        resolved = resolve_location(location)
        output = [
            f"⭐ Best rated hotels in {resolved} "
            f"({checkin_date} → {checkout_date}):"
        ]

        for hotel in hotel_dicts:
            output.append(format_hotel_info(hotel))

        return output

    except Exception as e:
        return [f"An error occurred while searching for best rated hotels: {str(e)}"]


@mcp.tool()
async def get_best_value_hotels(
    location: str,
    checkin_date: str,
    checkout_date: str,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    room_type: str = "standard",
    limit: int = 10,
) -> list[str]:
    """Get hotels sorted by best value (highest rating-to-price ratio).

    Use this when the user wants the best balance of quality and affordability.
    Hotels with high ratings and low prices rank highest.

    Args:
        location (str): City name, abbreviation, or IATA airport code.
        checkin_date (str): Check-in date in YYYY-MM-DD format.
        checkout_date (str): Check-out date in YYYY-MM-DD format.
        adults (int, optional): Number of adult guests. Defaults to 1.
        children (int, optional): Number of children. Defaults to 0.
        infants (int, optional): Number of infants. Defaults to 0.
        room_type (str, optional): "standard", "deluxe", or "suite". Defaults to "standard".
        limit (int, optional): Maximum number of hotels to return. Defaults to 10.

    Returns:
        list[str]: Hotels sorted by best value (rating/price ratio).
    """
    date_error = validate_dates(checkin_date, checkout_date)
    if date_error:
        return [date_error]

    if room_type not in ("standard", "deluxe", "suite"):
        return ["Room type must be 'standard', 'deluxe', or 'suite'."]

    try:
        # sort_by=None uses default best-value sorting (rating/price ratio)
        result = fetch_hotels(
            location=location,
            checkin_date=checkin_date,
            checkout_date=checkout_date,
            adults=adults,
            children=children,
            infants=infants,
            room_type=room_type,
            sort_by=None,
        )

        if not result.hotels:
            return [f"No hotels found in '{location}' for the specified dates."]

        hotel_dicts = hotels_to_dicts(result.hotels)
        hotel_dicts = hotel_dicts[:limit]

        resolved = resolve_location(location)
        output = [
            f"🏆 Best value hotels in {resolved} "
            f"({checkin_date} → {checkout_date}):"
        ]

        for hotel in hotel_dicts:
            # Add value score if both rating and price are available
            if hotel.get("rating") and hotel.get("price") and hotel["price"] > 0:
                value_score = hotel["rating"] / hotel["price"] * 100
                output.append(format_hotel_info(hotel) + f"\n   📊 Value score: {value_score:.2f}")
            else:
                output.append(format_hotel_info(hotel))

        return output

    except Exception as e:
        return [f"An error occurred while searching for best value hotels: {str(e)}"]


@mcp.tool()
async def filter_hotels_by_price(
    location: str,
    checkin_date: str,
    checkout_date: str,
    min_price: float = 0,
    max_price: float = 10000,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    room_type: str = "standard",
) -> list[str]:
    """Search hotels within a specific price range.

    Use this when the user has a budget in mind, e.g. "hotels under $200"
    or "hotels between $100 and $300 per night".

    Args:
        location (str): City name, abbreviation, or IATA airport code.
        checkin_date (str): Check-in date in YYYY-MM-DD format.
        checkout_date (str): Check-out date in YYYY-MM-DD format.
        min_price (float, optional): Minimum price per night in USD. Defaults to 0.
        max_price (float, optional): Maximum price per night in USD. Defaults to 10000.
        adults (int, optional): Number of adult guests. Defaults to 1.
        children (int, optional): Number of children. Defaults to 0.
        infants (int, optional): Number of infants. Defaults to 0.
        room_type (str, optional): "standard", "deluxe", or "suite". Defaults to "standard".

    Returns:
        list[str]: Hotels within the specified price range, sorted cheapest first.
    """
    date_error = validate_dates(checkin_date, checkout_date)
    if date_error:
        return [date_error]

    if min_price < 0:
        return ["Minimum price cannot be negative."]
    if max_price <= min_price:
        return ["Maximum price must be greater than minimum price."]

    if room_type not in ("standard", "deluxe", "suite"):
        return ["Room type must be 'standard', 'deluxe', or 'suite'."]

    try:
        result = fetch_hotels(
            location=location,
            checkin_date=checkin_date,
            checkout_date=checkout_date,
            adults=adults,
            children=children,
            infants=infants,
            room_type=room_type,
        )

        if not result.hotels:
            return [f"No hotels found in '{location}' for the specified dates."]

        hotel_dicts = hotels_to_dicts(result.hotels)

        # Filter by price range
        filtered = [
            h for h in hotel_dicts
            if h.get("price") is not None and min_price <= parse_price(h["price"]) <= max_price
        ]

        if not filtered:
            return [
                f"No hotels found in '{location}' within the price range "
                f"${min_price:,.0f} – ${max_price:,.0f} per night."
            ]

        # Sort by price ascending
        filtered.sort(key=lambda h: parse_price(h["price"]))

        resolved = resolve_location(location)
        output = [
            f"🏨 {len(filtered)} hotel(s) in {resolved} "
            f"within ${min_price:,.0f} – ${max_price:,.0f}/night "
            f"({checkin_date} → {checkout_date}):"
        ]

        for hotel in filtered:
            output.append(format_hotel_info(hotel))

        return output

    except Exception as e:
        return [f"An error occurred while filtering hotels by price: {str(e)}"]


@mcp.tool()
async def filter_hotels_by_amenities(
    location: str,
    checkin_date: str,
    checkout_date: str,
    amenities: str,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    room_type: str = "standard",
    limit: int = 20,
) -> list[str]:
    """Search hotels with specific amenity preferences.

    Pass desired amenities as a comma-separated string.
    The amenities are sent as preferences to the Google Hotels search.

    Common amenities: wifi, breakfast, pool, gym, parking, spa,
    restaurant, bar, air conditioning, pet-friendly, kitchen.

    Args:
        location (str): City name, abbreviation, or IATA airport code.
        checkin_date (str): Check-in date in YYYY-MM-DD format.
        checkout_date (str): Check-out date in YYYY-MM-DD format.
        amenities (str): Comma-separated amenity preferences (e.g. "wifi,breakfast,pool").
        adults (int, optional): Number of adult guests. Defaults to 1.
        children (int, optional): Number of children. Defaults to 0.
        infants (int, optional): Number of infants. Defaults to 0.
        room_type (str, optional): "standard", "deluxe", or "suite". Defaults to "standard".
        limit (int, optional): Maximum number of hotels to return. Defaults to 20.

    Returns:
        list[str]: Hotels matching the amenity preferences.
    """
    date_error = validate_dates(checkin_date, checkout_date)
    if date_error:
        return [date_error]

    if room_type not in ("standard", "deluxe", "suite"):
        return ["Room type must be 'standard', 'deluxe', or 'suite'."]

    amenities_list = [a.strip().lower() for a in amenities.split(",") if a.strip()]
    if not amenities_list:
        return ["Please provide at least one amenity (e.g. 'wifi,breakfast')."]

    try:
        result = fetch_hotels(
            location=location,
            checkin_date=checkin_date,
            checkout_date=checkout_date,
            adults=adults,
            children=children,
            infants=infants,
            room_type=room_type,
            amenities=amenities_list,
            limit=limit,
        )

        if not result.hotels:
            return [
                f"No hotels found in '{location}' with amenities: {', '.join(amenities_list)}."
            ]

        hotel_dicts = hotels_to_dicts(result.hotels)

        resolved = resolve_location(location)
        output = [
            f"🛎️ {len(hotel_dicts)} hotel(s) in {resolved} "
            f"with amenities [{', '.join(amenities_list)}] "
            f"({checkin_date} → {checkout_date}):"
        ]

        for hotel in hotel_dicts:
            output.append(format_hotel_info(hotel))

        return output

    except Exception as e:
        return [f"An error occurred while searching for hotels with amenities: {str(e)}"]


@mcp.tool()
async def compare_hotels_multi_location(
    locations: str,
    checkin_date: str,
    checkout_date: str,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    room_type: str = "standard",
) -> list[str]:
    """Compare hotels across MULTIPLE locations in one call.

    Use this when the user wants to compare hotel options in different cities,
    e.g. "compare hotels in Tokyo, Osaka, and Kyoto" or
    "which city has cheaper hotels: Dubai or Istanbul?".

    Results from all locations are combined and clearly labeled so the user
    can compare prices and options across cities.

    Args:
        locations (str): Comma-separated city names or IATA codes
                        (e.g. "Tokyo,Osaka,Kyoto" or "DXB,IST,CAI").
        checkin_date (str): Check-in date in YYYY-MM-DD format.
        checkout_date (str): Check-out date in YYYY-MM-DD format.
        adults (int, optional): Number of adult guests. Defaults to 1.
        children (int, optional): Number of children. Defaults to 0.
        infants (int, optional): Number of infants. Defaults to 0.
        room_type (str, optional): "standard", "deluxe", or "suite". Defaults to "standard".

    Returns:
        list[str]: Combined hotel results from all locations with a price comparison summary.
    """
    date_error = validate_dates(checkin_date, checkout_date)
    if date_error:
        return [date_error]

    if room_type not in ("standard", "deluxe", "suite"):
        return ["Room type must be 'standard', 'deluxe', or 'suite'."]

    location_list = [loc.strip() for loc in locations.split(",") if loc.strip()]
    if not location_list:
        return ["Please provide at least one location."]

    if len(location_list) > 5:
        return ["Maximum 5 locations allowed. Please narrow your selection."]

    combined_output: list[str] = []
    location_cheapest: list[tuple[str, float | None]] = []

    for loc in location_list:
        resolved = resolve_location(loc)
        try:
            result = fetch_hotels(
                location=loc,
                checkin_date=checkin_date,
                checkout_date=checkout_date,
                adults=adults,
                children=children,
                infants=infants,
                room_type=room_type,
                limit=5,  # Cap at 5 per location
            )

            if not result.hotels:
                combined_output.append(f"\n📍 {resolved}: No hotels found.")
                location_cheapest.append((resolved, None))
                continue

            hotel_dicts = hotels_to_dicts(result.hotels)
            cheapest = min(
                (parse_price(h["price"]) for h in hotel_dicts if h.get("price")),
                default=None
            )
            location_cheapest.append((resolved, cheapest))

            combined_output.append(
                f"\n📍 {resolved}: {len(hotel_dicts)} hotel(s) found "
                f"| Cheapest: ${cheapest:,.2f}" if cheapest else
                f"\n📍 {resolved}: {len(hotel_dicts)} hotel(s) found"
            )

            for hotel in hotel_dicts:
                combined_output.append(format_hotel_info(hotel))

        except Exception as e:
            combined_output.append(f"\n⚠️ {resolved}: Error — {str(e)}")
            location_cheapest.append((resolved, None))

    # Build header with comparison summary
    header = (
        f"🏨 Hotel comparison across {len(location_list)} location(s) "
        f"({checkin_date} → {checkout_date}):\n"
    )

    valid_prices = [(loc, p) for loc, p in location_cheapest if p is not None]
    if valid_prices:
        header += "\n💰 Price Comparison (cheapest per location):\n"
        for loc, price in valid_prices:
            header += f"   {loc}: ${price:,.2f}\n"

        cheapest_loc = min(valid_prices, key=lambda x: x[1])
        header += f"\n🏆 Cheapest location: {cheapest_loc[0]} at ${cheapest_loc[1]:,.2f}/night"

    return [header] + combined_output


@mcp.tool()
async def compare_hotels_multi_date(
    location: str,
    checkin_dates: str,
    nights: int = 1,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    room_type: str = "standard",
) -> list[str]:
    """Compare hotel prices across MULTIPLE check-in dates for the same location.

    Use this when the user wants to find the cheapest date to book,
    e.g. "which day next week has the cheapest hotels in Tokyo?" or
    "compare hotel prices in Dubai for March 10, 11, and 12".

    Args:
        location (str): City name, abbreviation, or IATA airport code.
        checkin_dates (str): Comma-separated check-in dates in YYYY-MM-DD format
                            (e.g. "2026-04-10,2026-04-11,2026-04-12"). Max 7 dates.
        nights (int, optional): Number of nights per stay. Defaults to 1.
        adults (int, optional): Number of adult guests. Defaults to 1.
        children (int, optional): Number of children. Defaults to 0.
        infants (int, optional): Number of infants. Defaults to 0.
        room_type (str, optional): "standard", "deluxe", or "suite". Defaults to "standard".

    Returns:
        list[str]: Hotel results grouped by date with a price comparison summary.
    """
    if room_type not in ("standard", "deluxe", "suite"):
        return ["Room type must be 'standard', 'deluxe', or 'suite'."]

    date_list = [d.strip() for d in checkin_dates.split(",") if d.strip()]
    if not date_list:
        return ["Please provide at least one check-in date."]
    if len(date_list) > 7:
        return ["Maximum 7 dates allowed. Please narrow your selection."]
    if nights < 1 or nights > 30:
        return ["Number of nights must be between 1 and 30."]

    resolved = resolve_location(location)
    combined_output: list[str] = []
    date_cheapest: list[tuple[str, float | None]] = []

    for checkin in date_list:
        # Calculate checkout date
        try:
            checkin_dt = datetime.strptime(checkin, "%Y-%m-%d")
            checkout_dt = checkin_dt + timedelta(days=nights)
            checkout = checkout_dt.strftime("%Y-%m-%d")
        except ValueError:
            combined_output.append(f"\n📅 {checkin}: Invalid date format.")
            date_cheapest.append((checkin, None))
            continue

        try:
            result = fetch_hotels(
                location=location,
                checkin_date=checkin,
                checkout_date=checkout,
                adults=adults,
                children=children,
                infants=infants,
                room_type=room_type,
                limit=5,  # Cap at 5 per date
            )

            if not result.hotels:
                combined_output.append(f"\n📅 {checkin}: No hotels found.")
                date_cheapest.append((checkin, None))
                continue

            hotel_dicts = hotels_to_dicts(result.hotels)
            cheapest = min(
                (parse_price(h["price"]) for h in hotel_dicts if h.get("price")),
                default=None
            )
            date_cheapest.append((checkin, cheapest))

            combined_output.append(
                f"\n📅 {checkin} → {checkout} ({nights} night{'s' if nights > 1 else ''}): "
                f"{len(hotel_dicts)} hotel(s) | Cheapest: ${cheapest:,.2f}" if cheapest else
                f"\n📅 {checkin} → {checkout}: {len(hotel_dicts)} hotel(s)"
            )

            for hotel in hotel_dicts[:3]:  # Show top 3 per date
                combined_output.append(format_hotel_info(hotel))

        except Exception as e:
            combined_output.append(f"\n📅 {checkin}: Error — {str(e)}")
            date_cheapest.append((checkin, None))

    # Build header with price comparison
    header = (
        f"🏨 Multi-date hotel comparison in {resolved} "
        f"({nights} night{'s' if nights > 1 else ''} per stay):\n"
    )

    valid_prices = [(d, p) for d, p in date_cheapest if p is not None]
    if valid_prices:
        header += "\n💰 Price Comparison (cheapest per date):\n"
        for date, price in valid_prices:
            header += f"   {date}: ${price:,.2f}\n"

        cheapest_date = min(valid_prices, key=lambda x: x[1])
        header += f"\n🏆 Cheapest date: {cheapest_date[0]} at ${cheapest_date[1]:,.2f}/night"

    return [header] + combined_output


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
