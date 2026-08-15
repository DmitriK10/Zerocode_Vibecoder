from flask import Flask, render_template, jsonify
import json
import os

app = Flask(__name__)

# Полный путь к файлу projects.json
PROJECTS_PATH = os.path.join(os.path.dirname(__file__), 'projects.json')

def load_projects():
    with open(PROJECTS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

@app.route('/')
def index():
    projects = load_projects()
    return render_template('index.html', projects=projects)

@app.route('/api/projects')
def api_projects():
    return jsonify(load_projects())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)