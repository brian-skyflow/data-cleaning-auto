from flask import Flask, request, jsonify
import pandas as pd
import requests
from io import BytesIO
import os

app = Flask(__name__)

# Airtable configuration - these should be set as environment variables on Heroku later
AIRTABLE_API_URL = os.getenv('AIRTABLE_API_URL')  # e.g., 'https://api.airtable.com/v0/your_base_id/your_table_name'
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')  # Your Airtable API Key

@app.route('/process-excel', methods=['POST'])
def process_excel():
    try:
        # Get JSON data from the incoming request
        data = request.json
        file_url = data.get('file_url')

        if not file_url:
            return jsonify({'error': 'file_url is required'}), 400

        # Download the Excel file from the provided URL
        response = requests.get(file_url)
        if response.status_code != 200:
            return jsonify({'error': 'Failed to download Excel file'}), 400

        # Load the Excel file into pandas from the downloaded content
        excel_content = BytesIO(response.content)
        df = pd.read_excel(excel_content)

        # Perform your calculations - Example: adding a new column
        if 'existing_column' in df.columns:
            df['new_column'] = df['existing_column'] * 2
        else:
            return jsonify({'error': 'existing_column not found in Excel file'}), 400

        # Save the processed data to CSV format (optional)
        csv_data = df.to_csv(index=False)

        # Prepare records for Airtable (converting dataframe rows to dictionary format)
        records = df.to_dict(orient='records')
        for record in records:
            airtable_record = {"fields": record}

            # Make a POST request to Airtable API to upload each record
            airtable_response = requests.post(
                AIRTABLE_API_URL,
                json=airtable_record,
                headers={
                    'Authorization': f'Bearer {AIRTABLE_API_KEY}',
                    'Content-Type': 'application/json'
                }
            )
            if airtable_response.status_code not in [200, 201]:
                return jsonify({'error': f'Failed to upload record: {airtable_response.text}'}), 400

        return jsonify({'message': 'Excel processed and data uploaded to Airtable successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
