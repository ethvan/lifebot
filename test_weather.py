import asyncio
import aiohttp

async def geocode(city: str):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city, "count": 1}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            data = await response.json()
            return data

async def get_weather(lat: float, lon: float):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            return await response.json()


async def main():
    geo = await geocode("Chicago")
    if "results" not in geo:
        print("City not found")
        return
    
    city_info = geo["results"][0]
    lat = city_info["latitude"]
    lon = city_info["longitude"]
    print(f"Found {city_info['name']}, {city_info['country']} at ({lat}, {lon})")
    
    weather = await get_weather(lat, lon)
    print(weather)

asyncio.run(main())