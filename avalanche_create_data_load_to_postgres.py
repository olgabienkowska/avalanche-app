import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import psycopg2
from faker import Faker
from datetime import datetime, timedelta
import random

#tokens
user = os.environ.get('USER')
password_postgres = os.environ.get('PASSWORD_POSTGRES')
DATABASE_URL = os.environ.get('DATABASE_URL')
# Fix the URL if it uses the old "postgres" scheme
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Initialize Faker for generating random names and emails
fake = Faker()

# Dictionary to store operator_name and email pairs
operator_email_map = {}

def random_date(start_date, end_date):
    """Generate a random date in ISO format between two dates."""
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return (start_date + timedelta(days=random_days)).isoformat()

def generate_latitude_longitude():
    """Generate random latitude and longitude within Austria's approximate range."""
    lat = round(random.uniform(46.0, 48.0), 5)
    lon = round(random.uniform(9.5, 16.0), 5)
    return lat, lon

def select_random_or_nan(options, p_nan=0.1):
    """Randomly select an option or return NaN based on probability."""
    return random.choice(options) if random.random() > p_nan else np.nan

def generate_group_distribution(group_size):
    """Ensure group size matches the sum of uninjured, injured, and fatal."""
    if group_size == 1:
        # Randomly assign the single person to be uninjured, injured, or fatal
        uninjured = 1 if random.random() < 0.5 else 0
        injured = 1 if uninjured == 0 and random.random() < 0.5 else 0
        fatal = 1 if uninjured == 0 and injured == 0 else 0
        return uninjured, injured, fatal

    # For groups greater than 1, split among uninjured, injured, and fatal
    uninjured = random.randint(0, group_size)
    injured = random.randint(0, group_size - uninjured)
    fatal = group_size - uninjured - injured
    return uninjured, injured, fatal


def generate_email(operator_name):
    """Generate email based on operator's name."""
    first_name, last_name = operator_name.split(' ', 1)
    return f"{first_name.lower()}.{last_name.lower()}@avalanche.com"

def random_date_within_season(start_date, end_date):
    """Generate a random date between start_date and end_date, limited to November through April."""
    allowed_months = [11, 12, 1, 2, 3, 4]  # November to April
    while True:
        random_date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
        if random_date.month in allowed_months:
            return random_date.strftime('%Y-%m-%dT%H:%M:%S')

# Main function to generate synthetic data
def generate_avalanche_data(num_records=64):
    """Generate a synthetic dataset based on identified patterns."""
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2024, 12, 31)

    data = []

    for _ in range(num_records):
        operator_name = fake.name()
        email = generate_email(operator_name)

        country = "Austria"
        state = random.choice(["Steiermark", "Tirol", "Vorarlberg"])
        subregion = fake.city()
        location_name = random.choice([
        "Großer Bösenstein", "Kelchsau", "Juppenmulde / Schröcken", "Eisentälispitze / Gargellen",
        "Piz Buin / Grüne Kuppe", "Litznersattel", "Tiajamähdli / gegenüber Alpe Vergalda",
        "Nenzigasttal / Kösterle", "Sidanjoch", "Gamsgrübl", "Hahnentrittkopf", "Rettenbachferner",
        "Nockspitze", "Rinsennock", "Mohnenfluh / 'Klemmle'", "Reggentörl", "Plannerseekarspitze",
        "Kleiner Wildkamm", "Olympiahang, Granatspitzgruppe", "Preberkessel", "Wannig", "Ruschletalm",
        "Jamtal", "Rauris", "Steinmandl / Schwarzwassertal", "Pfannenkopf / Valfagehr"
        ])
        latitude, longitude = generate_latitude_longitude()
        danger_rating_description = random.choice(["low", "moderate", "considerable", "high"])
        danger_problem = random.choice(["slab", "persistent slab", "loose dry", "wet snow"])
        av_length = round(random.uniform(50, 500), 2)
        av_width = round(random.uniform(10, 200), 2)
        av_thickness = round(random.uniform(0.5, 3.0), 2)
        av_type = random.choice(["dry", "wet", "mixed"])
        av_size = random.choice(["small", "medium", "large", "very large"])
        av_release = random.choice(["natural", "human-triggered", "unknown"])
        av_humidity = random.choice(["dry", "moist", "wet", "unknown"])
        travel_mode = random.choice(["ascent", "descent", "stationary"])
        group_size = random.randint(1, 6)

        # Ensure group size matches the sum of uninjured, injured, and fatal
        num_uninjured, num_injured, num_fatal = generate_group_distribution(group_size)

        equip_transceiver = random.choice(["all", "some", "none", "unknown"])
        equip_balloon_pack = random.choice(["yes", "no", "unknown"])
        elevation = round(random.uniform(1500, 3000), 2)
        aspect = random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"])
        slope_angle = round(random.uniform(25, 45), 2)

        data.append([
            random_date_within_season(start_date, end_date), operator_name, email, country, state, subregion, location_name,
            latitude, longitude, danger_rating_description, danger_problem, av_length, av_width, av_thickness,
            av_type, av_size, av_release, av_humidity, travel_mode, group_size, num_uninjured, num_injured,
            num_fatal, equip_transceiver, equip_balloon_pack, elevation, aspect, slope_angle
        ])

    # Convert list to DataFrame
    columns = [
        "report_date", "operator_name", "email", "country", "state", "subregion", "location_name", "latitude",
        "longitude", "danger_rating_description", "danger_problem", "av_length", "av_width", "av_thickness",
        "av_type", "av_size", "av_release", "av_humidity", "travel_mode", "group_size", "num_uninjured",
        "num_injured", "num_fatal", "equip_transceiver", "equip_balloon_pack", "elevation", "aspect", "slope_angle"
    ]

    df = pd.DataFrame(data, columns=columns)

    return df

def store_in_postgresql(df, table_name, db_url):
    # Create a connection string
    engine = create_engine(DATABASE_URL)
    df.to_sql(table_name, engine, if_exists='replace', index=False)




# table_df = generate_avalanche_data(100)
# Example usage:
# store_in_postgresql(table_df, table_name="avalanche_data", db_url=DATABASE_URL)

