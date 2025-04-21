from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
import plotly.graph_objects as go
import plotly.express as px
from dotenv import load_dotenv
import requests
import json
import re
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Union
import traceback

# Loading environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Constants
DATA_DIR = Path("data")
DATASET_FILES = {
    "us_cases": "covid19_us_daily_cases.csv",
    "us_deaths": "covid19_us_daily_deaths.csv",
    "global_cases": "covid19_global_daily_cases.csv",
    "global_deaths": "covid19_global_daily_deaths.csv",
}

def load_datasets() -> Dict[str, pd.DataFrame]:
    datasets = {}
    for key, filename in DATASET_FILES.items():
        file_path = DATA_DIR / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {file_path}")
        datasets[key] = pd.read_csv(file_path)
    return datasets

# Loading datasets 
try:
    DATASETS = load_datasets()
except FileNotFoundError as e:
    print(f"Error loading datasets: {e}")
    DATASETS = {}

#  cleaning LLM response and striping natural language
def extract_code_from_llm_response(text: str) -> str:
    match = re.search(r"```(?:python)?(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    lines = text.strip().splitlines()
    code_lines = [line for line in lines if not line.strip().startswith(("Here's", "This", "#", "Output"))]
    return "\n".join(code_lines)

# filter out non-serializable objects
def safe_convert(obj):
    if isinstance(obj, (np.ndarray, pd.Series)):
        return obj.tolist()
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if isinstance(obj, (np.int64, np.float64)):
        return float(obj)
    return str(obj)
#running the llm given code and returning the plot
def run_code_and_return_plot(code: str, df: pd.DataFrame) -> Dict[str, Optional[Union[dict, str]]]:
    local_env = {
        "df": df.copy(),
        "pd": pd,
        "go": go,
        "px": px
    }

    try:
        # ✅ Auto fix: wrong y='Deaths' (should be 'Daily_Deaths')
        if "y='Deaths'" in code and 'Deaths' not in df.columns:
            code = code.replace("y='Deaths'", "y='Daily_Deaths'")
        if "y=\"Deaths\"" in code and 'Deaths' not in df.columns:
            code = code.replace('y="Deaths"', 'y="Daily_Deaths"')

        # ✅ Auto fix: if groupby used, enforce reset_index
        if "groupby(" in code and "reset_index" not in code:
            code = code.replace(".groupby(", ".groupby(").replace(").sum()", ").sum().reset_index()")

        # ✅ Fallback if LLM forgets groupby
        if "groupby" not in code and "Daily_Deaths" in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df = df.groupby('Date')['Daily_Deaths'].sum().reset_index()
            local_env["df"] = df
            code = "fig = px.line(df, x='Date', y='Daily_Deaths', title='Total Daily Deaths Over Time')"

        exec(code, {}, local_env)
        fig = local_env.get("fig")
        if fig is None:
            return {"plot": None, "error": "No figure named 'fig' was generated."}
        fig_dict = fig.to_dict()
        fig_json = json.loads(json.dumps(fig_dict, default=safe_convert))
        return {"plot": fig_json, "error": None}
    except Exception as e:
        traceback.print_exc()
        return {"plot": None, "error": str(e)}

# route for handling the query form the frontend and sending it to llm
@app.route("/query", methods=["POST"])
def handle_query():
    try:
        user_query = request.json.get("query", "")
        dataset_key = request.json.get("dataset", "us_deaths")

        if not user_query:
            return jsonify({"error": "Query cannot be empty."}), 400

        df = DATASETS.get(dataset_key)
        if df is None:
            return jsonify({"error": f"Invalid dataset key: {dataset_key}"}), 400

        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

        columns_list = ', '.join(df.columns.tolist())
        print("columns_list",columns_list)
        # ✅ Final LLM Prompt
        prompt = f"""
You are a Python data visualization expert using Plotly.

📝 A user asked: "{user_query}"

You are working with a Pandas DataFrame named `df`.

⚠️ You MUST only use the following column names exactly as provided:
{columns_list}

Do NOT assume or rename any columns (e.g., don’t convert 'Country/Region' to 'Country_Region').
If you use a wrong column name, the code will fail.

Use these names exactly as-is in any filtering, grouping, or plotting.

Instructions:
- Always convert 'Date' using df['Date'] = pd.to_datetime(df['Date'])
- Prefer filtering locations in this order: 'Admin2' (county), 'Province_State' (state), 'Country/Region' (country)
- If a specific date is mentioned, filter using: df['Date'] == pd.to_datetime('YYYY-MM-DD')
- After filtering, group by 'Date' using: df.groupby('Date')['Cases' or 'Deaths'].sum().reset_index()
- Add a column 'Label' or 'Region' if comparing multiple locations

📊 Chart Type Rules:
- If the query filters to a **single day**, use `px.bar(...)` for a single bar
- If the query includes **multiple dates**, use `px.line(...)` to show trends

🖼️ Visualization:
- Always assign the chart to a variable called `fig`
- Set a clear title using fig.update_layout(title=...)
- Do not use `print()` or markdown — only return valid Python code inside triple backticks
- DO NOT use `return fig`
- Just assign the chart to a variable named `fig`
- My environment will handle retrieving and rendering `fig`
"""



        headers = {
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "agentica-org/deepcoder-14b-preview:free",
            # "model": "qwen/qwen2.5-vl-3b-instruct:free",
            "messages": [{"role": "user", "content": prompt}]
        }

        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)

        if response.status_code != 200:
            return jsonify({"error": f"OpenRouter API error: {response.text}"}), 500

        llm_data = response.json()
        raw_text = llm_data["choices"][0]["message"]["content"]
        code = extract_code_from_llm_response(raw_text)

        print(f"\n📝 User Query:\n{user_query}")
        print(f"\n🧠 Generated Code:\n{code}")

        result = run_code_and_return_plot(code, df)

        if result["error"]:
            print(f"\n❌ Code Execution Error:\n{result['error']}")
        else:
            print("\n📊 Plot Data Preview (First 500 characters):")
            print(json.dumps(result["plot"], indent=2)[:500])

        return jsonify({
            "code": code,
            "visualization": result["plot"],
            "error": result["error"]
        })

    except Exception as e:
        print("\n=== ❌ Server Error ===")
        traceback.print_exc()
        return jsonify({"error": f"{type(e).__name__}: {str(e)}"}), 500


if __name__ == "__main__":
    print("🚀 Flask server running at http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
