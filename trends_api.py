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
        # Create a requests session with retry settings
        session = requests.Session()
        retries = Retry(
            total=5,  # Number of retries
            backoff_factor=0.1,  # Small delay between retries
            allowed_methods=["GET", "POST"],  # Replaces method_whitelist
            status_forcelist=[429, 500, 502, 503, 504]  # Retries only on these errors
        )
        session.mount("https://", HTTPAdapter(max_retries=retries))

        # Initialize Pytrends **without** requests_args
        pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))

        # Set payload and fetch data
        pytrends.build_payload(keyword_list, cat=0, timeframe=timeframe, geo=region, gprop='')
        trends_data = pytrends.interest_over_time()

        if trends_data.empty:
            return jsonify({"error": "No data available for the given keywords"}), 400

        # Convert timestamps to string format before returning JSON
        trends_dict = trends_data.drop(columns=['isPartial']).to_dict()
        trends_dict = {str(k): v for k, v in trends_dict.items()}  # Convert keys to strings

        return jsonify({"status": "success", "data": trends_dict})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
