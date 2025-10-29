from services import country_data, exchange_rate_data, generate_country_summary_image
from models import Countries, SessionDep
from fastapi import HTTPException, status
from main import app
from sqlmodel import select, func
from datetime import datetime, timezone
from fastapi.responses import FileResponse
import os
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_PATH = os.path.join(BASE_DIR, "cache", "summary.png")


@app.post("/countries/refresh")
def fetch_country_data(session: SessionDep):
    try:
        countries = country_data("https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies")
        exchange_rates = exchange_rate_data("https://open.er-api.com/v6/latest/USD")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "External data source unavailable",
                "details": str(e)
            }
        )

    if not countries or not exchange_rates:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "External data source unavailable", "details": "Could not fetch data from API"}
        )

    try:
        new_countries = []
        updated_count = 0

        for country in countries:
            name = country.get("name")
            if not name:
                continue
                
            population = country.get("population", 0)
            capital = country.get("capital")
            region = country.get("region")
            flag_url = country.get("flag")
            currencies = country.get("currencies") or []
            
            
            if not currencies:
                
                currency_code = None
                exchange_rate = None
                estimated_gdp = 0.0 
            else:
                currency_code = currencies[0].get("code") if currencies[0] else None
                
                if currency_code:
                    exchange_rate = exchange_rates.get(currency_code)
                    
                    # Calculate GDP
                    if exchange_rate and population:
                        gdp_per_capita = random.uniform(1000, 2000)
                        estimated_gdp = round((population * gdp_per_capita) / exchange_rate, 2)
                    else:
                    
                        estimated_gdp = None
                else:
                
                    exchange_rate = None
                    estimated_gdp = 0.0

            # Check if country exists
            existing = session.exec(
                select(Countries).where(Countries.name.ilike(name))
            ).first()

            if existing:
                # Update existing country
                existing.capital = capital
                existing.region = region
                existing.population = population
                existing.currency_code = currency_code
                existing.exchange_rate = exchange_rate
                existing.estimated_gdp = estimated_gdp
                existing.flag_url = flag_url
                existing.last_refreshed_at = datetime.now(timezone.utc)
                session.add(existing)
                updated_count += 1
            else:
                # Create new country
                new_country = Countries(
                    name=name,
                    capital=capital,
                    region=region,
                    population=population,
                    currency_code=currency_code,
                    exchange_rate=exchange_rate,
                    estimated_gdp=estimated_gdp,
                    flag_url=flag_url,
                    last_refreshed_at=datetime.now(timezone.utc)
                )
                new_countries.append(new_country)

        if new_countries:
            session.add_all(new_countries)

        session.commit()

        # summary image
        try:
            generate_country_summary_image(session)
        except Exception as img_error:
            print(f"Image generation failed: {img_error}")

        total_processed = len(new_countries) + updated_count
        return {"message": f"Saved/updated {total_processed} countries successfully"}

    except HTTPException as e:
        session.rollback()
        raise e
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "details": str(e)}
        )


@app.get("/countries")
def get_countries(
    session: SessionDep, 
    skip: int = 0, 
    limit: int = 10,
    name: str | None = None,
    region: str | None = None,
    currency: str | None = None,
    sort: str | None = None
):
    
    query = select(Countries)

    # filters
    if name:
        query = query.where(Countries.name.ilike(f"%{name}%"))
    if region:
        query = query.where(Countries.region.ilike(f"%{region}%"))
    if currency:
        query = query.where(Countries.currency_code.ilike(f"%{currency}%"))

    # sorting
    if sort:
        sort_mapping = {
            "gdp_asc": Countries.estimated_gdp.asc(),
            "gdp_desc": Countries.estimated_gdp.desc(),
            "population_asc": Countries.population.asc(),
            "population_desc": Countries.population.desc(),
            "name_asc": Countries.name.asc(),
            "name_desc": Countries.name.desc(),
        }
        sort_order = sort_mapping.get(sort)
        if sort_order is None:
            raise HTTPException(
                status_code=400, 
                detail={"error": "Invalid sort parameter"}
            )
        query = query.order_by(sort_order)

    # Get paginated results
    countries = session.exec(query.offset(skip).limit(limit)).all()

    return countries


@app.get("/countries/image")
def get_country_summary_image():
    if not os.path.exists(IMAGE_PATH):
        raise HTTPException(
            status_code=404,
            detail={"error": "Summary image not found"}
        )
    return FileResponse(IMAGE_PATH, media_type="image/png")


@app.get("/countries/{name}")
def get_country_by_name(name: str, session: SessionDep):
    
    query = select(Countries).where(Countries.name.ilike(name))
    result = session.exec(query).first()
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail={"error": "Country not found"}
        )
    
    return result


@app.delete("/countries/{name}")
def delete_country(name: str, session: SessionDep):
    query = select(Countries).where(Countries.name.ilike(name))
    country = session.exec(query).first()

    if not country:
        raise HTTPException(
            status_code=404,
            detail={"error": "Country not found"}
        )
    session.delete(country)
    session.commit()
    return {"message": f"Country '{name}' deleted successfully"}


@app.get("/status")
def total_countries_and_last_refresh(session: SessionDep):
    total_countries = session.exec(
        select(func.count()).select_from(Countries)
    ).one()
    
    last_refresh = session.exec(
        select(func.max(Countries.last_refreshed_at))
    ).one()

    return {
        "total_countries": total_countries,
        "last_refreshed_at": last_refresh
    }