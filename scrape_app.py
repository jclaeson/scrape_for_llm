from flask import Flask, render_template, request
from app.scraping import scrape_website

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    url = request.form['url']
    depth = int(request.form['depth'])  # Get the depth from the form
    data = scrape_website(url, depth)

    # Ensure `data` is a list, even if it's a single dictionary
    if isinstance(data, dict):
        data = [data]

    return render_template('index.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)
