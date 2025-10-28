from services import country_data, exchange_rate_data, match_countries_with_exchange_rates, calculate_estimated_gdp
from models import Countries, SessionDep
from main import app
from sqlmodel import select
from datetime import datetime

@app.on_event("startup")
def on_startup():
    from models import create_db_and_tables
    create_db_and_tables()

@app.post("/countries/refresh")
def fetch_country_data(session: SessionDep):
    countries = country_data("https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies")
    exchange_rates = exchange_rate_data("https://open.er-api.com/v6/latest/USD")

    country_obj = []

    for country in countries:
        name = country.get("name")
        population = country.get("population")
        capital = country.get("capital")
        region = country.get("region")
        flag_url = country.get("flag")

        
        currencies = country.get("currencies") or []
        currency_code = currencies[0].get("code") if currencies else None

        
        exchange_rate = exchange_rates.get(currency_code) if currency_code else None

        
        if currency_code is None:
            estimated_gdp = 0  
        elif exchange_rate is None:
            estimated_gdp = None  
        else:
            estimated_gdp = calculate_estimated_gdp({
                "population": population,
                "exchange_rate": exchange_rate
            })

        
        existing = session.exec(select(Countries).where(Countries.name.ilike(name))).first()

        if existing:
            existing.capital = capital
            existing.region = region
            existing.population = population
            existing.currency_code = currency_code
            existing.exchange_rate = exchange_rate
            existing.estimated_gdp = estimated_gdp
            existing.flag_url = flag_url
            existing.last_referenced_at = datetime.utcnow()
        else:
            new_country = Countries(
                name=name,
                capital=capital,
                region=region,
                population=population,
                currency_code=currency_code,
                exchange_rate=exchange_rate,
                estimated_gdp=estimated_gdp,
                flag_url=flag_url,
            )
            country_obj.append(new_country)

    if country_obj:
        session.add_all(country_obj)
    
    session.commit()

    return {"message": f"Saved/updated {len(country_obj)} countries successfully"}

