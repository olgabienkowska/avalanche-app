from flask import Flask, render_template, request
from sqlalchemy import create_engine
import psycopg2
import google.generativeai as genai
from avalanche_prompt import analyze_avalanche_data, format_accident_data, format_avalanche_insights
import pandas as pd
import re
import os
from markupsafe import Markup
from sqlalchemy import text

#Tokens
user = os.environ.get('USER')
password_postgres = os.environ.get('PASSWORD_POSTGRES')
GENAI_API_KEY = os.environ.get("GENAI_API_KEY")
DATABASE_URL = os.environ.get('DATABASE_URL')
# Fix the URL if it uses the old "postgres" scheme
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configure Google Generative AI
genai.configure(api_key=GENAI_API_KEY)

# Set up the Generative AI model configuration
generation_config = {
    "temperature": 0.15,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 2000,
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

app = Flask(__name__)
engine = create_engine(DATABASE_URL)


@app.route('/')
def index():
    # Query the `location_name` column
    with engine.connect() as connection:
        result = connection.execute(text("SELECT DISTINCT location_name FROM avalanche_data ORDER BY 1"))
        locations = [row[0] for row in result]

    return render_template('index.html', locations=locations)

@app.template_filter('bold_and_split')
def bold_and_split(text):
    import re
    from markupsafe import Markup

    # Ensure the text is a string
    if not isinstance(text, str):
        text = str(text) if text is not None else ""

    # Apply bold formatting by converting **text** to <strong>text</strong>
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

    # Convert non-empty lines in the text to bullet points, ignoring empty lines
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) > 1:
        formatted_text = "<ul>" + "".join(f"<li>{line}</li>" for line in lines) + "</ul>"
    else:
        # Return single-line text without bullets
        formatted_text = lines[0] if lines else ""

    return Markup(formatted_text)


@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    # Query the entire `avalanche_data` table to get the dataset
    with engine.connect() as connection:
        df = pd.read_sql("SELECT * FROM avalanche_data", connection)
        dataset_json = df.to_json(orient='records')

    # Fetch unique location names for the dropdown
    with engine.connect() as connection:
        result = connection.execute(text("SELECT DISTINCT location_name FROM avalanche_data ORDER BY 1"))
        locations = [row[0] for row in result]

    # Determine selected location: use form input if available, otherwise default to the first location
    selected_location = request.form.get('location', locations[0] if locations else None)

    # Format the data using `format_accident_data`
    formatted_data = format_accident_data(df)

    # Retrieve data for the selected location if it exists
    location_data = formatted_data.get(selected_location, {"summary": "", "overview": ""})

    # Generate insights and risk analysis for the selected location
    analysis = format_avalanche_insights(dataset_json, selected_location)

    # Pass the formatted data to the template
    return render_template(
        'index.html',
        locations=locations,
        summary=location_data['summary'],
        overview=location_data['overview'],
        selected_location=selected_location,
        insights=analysis["insights"],
        risk_analysis=analysis["risk_analysis"]
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)



