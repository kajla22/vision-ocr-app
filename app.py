from flask import Flask, render_template, request
import requests, os

app = Flask(__name__)

VISION_ENDPOINT = os.getenv("VISION_ENDPOINT")  # For your API endpoint
VISION_KEY = os.getenv("VISION_KEY")  # For your API key


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    image = request.files['file']
    image_data = image.read()
    headers = {'Ocp-Apim-Subscription-Key': VISION_KEY, 'Content-Type': 'application/octet-stream'}
    ocr_url = f"{VISION_ENDPOINT}/vision/v3.2/ocr"

    response = requests.post(ocr_url, headers=headers, data=image_data)
    result = response.json()

    text_output = []
    for region in result.get('regions', []):
        for line in region['lines']:
            line_text = ' '.join([word['text'] for word in line['words']])
            text_output.append(line_text)
    return render_template('result.html', text="\n".join(text_output))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080,debug=True)