from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os

app = Flask(__name__)
CORS(app)  # Allow all origins for development

# Load Visualization Data from JSON File
with open('visualizations.json', 'r') as f:
    visualizations = json.load(f)
print(f"Loaded {len(visualizations)} visualizations from JSON file.")
# Get OpenRouter API Key from environment variable
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def call_openrouter_llm(user_query):
    print(f"Loaded {len(visualizations)} visualizations from JSON file.")

    prompt = f"""
You are a Visualization Retrieval AI.

Given the following `visualization.json`:

[INSERT visualization.json CONTENT HERE]

And the user query:

"{user_query}"

Select the most relevant visualization. Match based on tags, title, and description. If no perfect match, suggest the closest available visualization.


Visualizations List:
{json.dumps(visualizations, indent=2)}

User Query: "{user_query}"

Respond ONLY in this JSON format:
{{"id": "viz_xxx", "title": "...", "description": "...", "viz_url": "..." }}
"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {"role": "system", "content": "You are a visualization selector."},
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)

    if response.status_code == 200:
        try:
            content = response.json()['choices'][0]['message']['content']
            result = json.loads(content)
            print(f"LLM Response: {result}")
            return {
                "text": f"Here is the best visualization for your query: {result.get('title')}",
                "title": result.get("title"),
                "description": result.get("description"),
                "viz_url": result.get("viz_url")
            }
        except Exception as e:
            return {"error": f"Failed to parse LLM response: {str(e)}"}
    else:
        return {"error": f"OpenRouter API Error: {response.status_code}"}

@app.route('/get_visualization', methods=['POST'])
def get_visualization():
    data = request.get_json()
    user_query = data.get("query")

    if not user_query:
        return jsonify({"error": "No query provided."}), 400

    result = call_openrouter_llm(user_query)
    return jsonify(result)

if __name__ == "__main__":
    app.run(port=5002, debug=True)
