from flask import Flask, request, jsonify
from pytrends.request import TrendReq
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

app = Flask(__name__)

@app.route('/get_trends', methods=['GET'])
def get_trends():
    # Get keywords, region, and timeframe from API request
    keywords = request.args.get('keywords', '')
    region = request.args.get('region', 'US')
    timeframe = request.args.get('timeframe', 'today 12-m')

    if not keywords:
        return jsonify({"error": "No keywords provided"}), 400

    keyword_list = keywords.split(',')

    try:
        # Create a session with retry settings to prevent blocking
        session = requests.Session()
        retries = Retry(
            total=5,  # Number of retries
            backoff_factor=0.1,
            allowed_methods=["GET", "POST"],  # Fix for method_whitelist error
            status_forcelist=[429, 500, 502, 503, 504]  # Retry on these error codes
        )
        session.mount("https://", HTTPAdapter(max_retries=retries))

        # Initialize Pytrends with session to avoid Google blocking requests
        pytrends = TrendReq(
            hl='en-US',
            tz=360,
            timeout=(10, 25),
            retries=2,
            backoff_factor=0.1,
            requests_args={"session": session}
        )

        pytrends.build_payload(keyword_list, cat=0, timeframe=timeframe, geo=region, gprop='')

        # Fetch Google Trends data
        trends_data = pytrends.interest_over_time()

        if trends_data.empty:
            return jsonify({"error": "No data available for the given keywords"}), 400

        # Convert trends data to JSON
        trends_dict = trends_data.drop(columns=['isPartial']).to_dict()

        return jsonify({"status": "success", "data": trends_dict})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
