import requests
from models import Countries, Session
import random

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


countries = country_data("https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies")
# print(countries)
exchange_rates = exchange_rate_data("https://open.er-api.com/v6/latest/USD")
matched_countries = match_countries_with_exchange_rates(countries, exchange_rates)
# print(matched_countries)