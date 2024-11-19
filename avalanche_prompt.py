import os
import xml.etree.ElementTree as ET
import pandas as pd
import google.generativeai as genai
from sqlalchemy import create_engine
import psycopg2
from avalanche_create_data_load_to_postgres import generate_avalanche_data
from markupsafe import Markup
from datetime import datetime


# Configure Google Generative AI
GENAI_API_KEY = os.environ.get("GENAI_API_KEY")
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

def format_accident_data(df):
    formatted_data = {}

    for location in df['location_name'].unique():
        # Filter the dataframe for each location
        location_data = df[df['location_name'] == location]

        # Calculate accident count for each location
        accident_count = len(location_data)

        # Directly format the summary for each location
        summary_match = f"Number of accidents in **{location}** : **{accident_count}**"

        # Format overview matches as plain text
        overview_matches = []
        for _, row in location_data.iterrows():
            report_date_formatted = datetime.strptime(row['report_date'], '%Y-%m-%dT%H:%M:%S').strftime('%B %d, %Y')
            overview_match = (
                f"The accident took place on **{report_date_formatted}**. The avalanche danger was **{row['danger_rating_description']}** "
                f"with main problem being **{row['danger_problem']}**. "
                f"The accident took place during **{row['travel_mode']}**. The group size was **{row['group_size']}**, "
                f"with **{row['num_uninjured']}** uninjured, **{row['num_injured']}** injured and **{row['num_fatal']}** fatal. "
                f"The elevation was **{row['elevation']}**, with **{row['aspect']}** aspect and **{row['slope_angle']}** angle."
            )
            overview_matches.append(overview_match)

        # Store summary and overview in formatted_data
        formatted_data[location] = {
            "summary": summary_match,
            "overview": "\n".join(overview_matches)  # Only overview matches are joined with newlines
        }

    return formatted_data


def analyze_avalanche_data(dataset_json, location):
    prompt = f"""
    
    You are an avalanche researcher, analyzing the dataset in detail and providing advice. 
    
    1. Analyze the provided dataset:
    
    {dataset_json}
    
    Based on the following dataset, identify patterns related to avalanche type, primary trigger, seasonal trends, danger rating, and regional differences. 
    Format the output EXACTLY as follows with no title. 

    Avalanche Type: [Provide an analysis of the summary of types observed and distribution of incidents]
    Primary Trigger: [Provide an analysis of common causes or triggers of avalanches and distribution of incidents]
    Seasonal Trends: [Provide an analysis of relevant seasonal patterns and distribution of incidents]
    Danger Ratings: [Provide an analysis of  of danger ratings and distribution of incidents]
    Regional Variances: [Provide an analysis of regional Variances: Regional differences and specific subregion trends]
          
    
    2. Next, make a risk assesment for the incident `location_name` matches '{location}' EXACTLY. 
    Write EXACTLY 3 sentences on what could be considered risk factors. Don't include title. Start the sentence with 'Risk factors for the location were:'.

"""

    return prompt


def format_avalanche_insights(dataset_json, location):
    # Generate the prompt
    prompt = analyze_avalanche_data(dataset_json, location)

    # Call the model to generate the analysis
    response = model.generate_content(prompt)
    response_text = response.text

    # Split the response into Insights and Risk Analysis based on a unique marker
    if "Risk factors for the location were:" in response_text:
        insights_text, risk_analysis = response_text.split('Risk factors for the location were:')
        insights_text = insights_text.strip()
        risk_analysis = "Risk factors for the location were: " + risk_analysis.strip()
    else:
        insights_text, risk_analysis = response_text, ""

    # Further separate each part within insights based on known section headers
    sections = ["Avalanche Type", "Primary Trigger", "Seasonal Trends", "Danger Ratings", "Regional Variances"]
    insights = {}

    # Parse each section using the headers as markers
    for i, section in enumerate(sections):
        start_index = insights_text.find(f"{section}:")
        end_index = insights_text.find(f"{sections[i + 1]}:") if i + 1 < len(sections) else None
        if start_index != -1:
            insights[section] = insights_text[start_index + len(section) + 1:end_index].strip()

    # Return the structured output
    return {
        "insights": insights,
        "risk_analysis": risk_analysis
    }