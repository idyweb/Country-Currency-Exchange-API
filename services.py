import requests
from models import Countries, SessionDep
import random
from fastapi.responses import FileResponse
from sqlmodel import select, func
from PIL import Image, ImageDraw, ImageFont
import os


def country_data(url):
    country_data = requests.get(url)
    if country_data.status_code == 200:
        countries = country_data.json()
        print(f"Fetched {len(countries)} countries from API.")
        return countries


def exchange_rate_data(url):
    exchange_rate_data = requests.get(url)
    if exchange_rate_data.status_code == 200:
        exchange_rates = exchange_rate_data.json().get("rates", {})
        print("Fetched exchange rates from API.")
        return exchange_rates


def match_countries_with_exchange_rates(countries, exchange_rates):
    for country in countries:
        currency_code = None
        currencies = country.get("currencies", [])
        if currencies and isinstance(currencies, list):
            currency_code = currencies[0].get("code")
        country["exchange_rate"] = exchange_rates.get(currency_code)
    return countries


def calculate_estimated_gdp(country: dict) -> float | None:
    population = country.get("population")
    exchange_rate = country.get("exchange_rate")
    if not population or not exchange_rate or exchange_rate == 0:
        return None
    gdp_per_capita = random.uniform(1000, 2000)
    return round((population * gdp_per_capita) / exchange_rate, 2)


def generate_country_summary_image(session: SessionDep):
    total_countries = session.exec(select(func.count()).select_from(Countries)).one()
    top_5_gdp_countries = session.exec(
        select(Countries).order_by(Countries.estimated_gdp.desc()).limit(5)
    ).all()
    last_refresh_timestamp = session.exec(
        select(func.max(Countries.last_referenced_at))
    ).one()

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    cache_dir = os.path.join(BASE_DIR, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    image_path = "cache/summary.png"
    image = Image.new('RGB', (800, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)

    try:
        title_font = ImageFont.truetype("arial.ttf", 24)
        text_font = ImageFont.truetype("arial.ttf", 18)
    except:
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()

    draw.text((10, 10), "Country Summary Report", font=title_font, fill=(0, 0, 0))
    draw.text((10, 50), f"Total Countries: {total_countries}", font=text_font, fill=(0, 0, 0))
    draw.text((10, 80), "Top 5 Countries by Estimated GDP:", font=text_font, fill=(0, 0, 0))

    y_offset = 110
    for country in top_5_gdp_countries:
        draw.text((10, y_offset), f"{country.name} – GDP: {country.estimated_gdp}", font=text_font, fill=(0, 0, 0))
        y_offset += 30

    draw.text((10, y_offset + 10), f"Last Refreshed: {last_refresh_timestamp}", font=text_font, fill=(0, 0, 0))

    image.save(image_path)
    print(f"✅ Image saved at {image_path}")

countries = country_data("https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies")
# print(countries)
exchange_rates = exchange_rate_data("https://open.er-api.com/v6/latest/USD")
matched_countries = match_countries_with_exchange_rates(countries, exchange_rates)
# print(matched_countries)