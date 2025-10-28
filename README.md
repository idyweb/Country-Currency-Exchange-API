# Country Currency & Exchange API

A FastAPI backend service that fetches country data and currency exchange rates from public APIs, stores them in a MySQL database, and provides rich filtering, CRUD operations, and an auto-generated summary image.

# Features

- Fetch and cache country data with currency information

- Compute estimated GDP using exchange rates

- Serve country data with pagination, filtering, and sorting

- Auto-generate and serve summary image

- MySQL database integration

- Environment-based configuration using .env

- Fully tested with PyTest

## Installation & Setup

1. Clone the Repository
```bash
git clone https://github.com/idyweb/Country-Currency-Exchange-API.git
cd Country-Currency-Exchange-Api
```

2. Create & Activate Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Dependencies

```bash
pip install -r requirements.txt
```

4. Run the Application
```bash
uvicorn main:app --reload
```

## Image Generation

After calling /countries/refresh, an image is automatically generated and stored at:

```bash
/cache/summary.png
```

It contains:

- Total countries

- Top 5 GDP countries

- Last refresh time