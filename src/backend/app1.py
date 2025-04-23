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
def run_code_and_return_plot(code: str, df: pd.DataFrame, user_query: str) -> Dict[str, Optional[Union[dict, str]]]:
    local_env = {
        "df": df.copy(),
        "pd": pd,
        "go": go,
        "px": px
    }

    try:
        # ✅ Replace wrong column references with available ones
        if "y='Deaths'" in code and 'Deaths' not in df.columns and 'Daily_Deaths' in df.columns:
            code = code.replace("y='Deaths'", "y='Daily_Deaths'")
        if "y=\"Deaths\"" in code and 'Deaths' not in df.columns and 'Daily_Deaths' in df.columns:
            code = code.replace('y="Deaths"', 'y="Daily_Deaths"')
        if "y='Cases'" in code and 'Cases' not in df.columns and 'Daily_Cases' in df.columns:
            code = code.replace("y='Cases'", "y='Daily_Cases'")
        if "y=\"Cases\"" in code and 'Cases' not in df.columns and 'Daily_Cases' in df.columns:
            code = code.replace('y="Cases"', 'y="Daily_Cases"')

        # ✅ Ensure groupby has reset_index
        if "groupby(" in code and "reset_index" not in code:
            code = code.replace(".groupby(", ".groupby(").replace(").sum()", ").sum().reset_index()")

        print("🔥 Final Code to Execute:\n", code)

        # ✅ Execute the LLM code
        exec(code, {}, local_env)
        fig = local_env.get("fig")

        # ✅ If LLM code did not generate fig, fallback to default trend chart
        if fig is None:
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

            fallback_y = None
            if 'Daily_Deaths' in df.columns:
                fallback_y = 'Daily_Deaths'
            elif 'Daily_Cases' in df.columns:
                fallback_y = 'Daily_Cases'
            elif 'Deaths' in df.columns:
                fallback_y = 'Deaths'
            elif 'Cases' in df.columns:
                fallback_y = 'Cases'

            if fallback_y:
                fallback_df = df.groupby('Date')[fallback_y].sum().reset_index()
                fig = px.line(fallback_df, x='Date', y=fallback_y, title=f"Trend of {fallback_y} Over Time")
            else:
                return {"plot": None, "error": "No valid y-axis column found for fallback chart."}

        # ✅ Convert to JSON-safe dictionary
        fig_dict = fig.to_dict()
        fig_json = json.loads(json.dumps(fig_dict, default=safe_convert))

        return {"plot": fig_json, "error": None}

    except Exception as e:
        traceback.print_exc()
        return {"plot": None, "error": str(e)}


# route for handling the query form the frontend and sending it to llm
@app.route("/query", methods=["POST"])
def handle_query():
    print("Incoming JSON:", request.json)
    print("query:", request.json.get("query"))
    print("dataset:", request.json.get("dataset"))
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
You are a Python data visualization expert using Plotly and Pandas.

📝 A user asked: "{user_query}"

You are working with a Pandas DataFrame named df loaded from a COVID-19 dataset: {dataset_key}.

The available datasets are:

---

🔹 **Dataset: global_deaths**
- Columns: 'Country/Region', 'Province/State', 'Lat', 'Long', 'Date', 'Deaths', 'Daily_Deaths'
- Use Daily_Deaths for daily death queries (e.g., "deaths in India on April 21, 2021")
- Use Deaths for cumulative totals (e.g., "total deaths in Italy until May 2021")
- Filter by: 'Country/Region', optionally 'Province/State'
- Use: px.bar() for single-day, px.line() for trends

---

🔹 **Dataset: us_deaths**
- Columns: 'Admin2', 'Province_State', 'Country_Region', 'Date', 'Deaths', 'Daily_Deaths'
- Use Daily_Deaths for daily trends or per-date queries
- Use Deaths only for cumulative totals if the user asks for total deaths
- Filter by: 'Province_State' or 'Admin2'
- Use: px.bar() for single-day or comparison, px.line() for time series

---

🔹 **Dataset: global_cases**
- Columns: 'Country/Region', 'Province/State', 'Lat', 'Long', 'Date', 'Cases', 'Daily_Cases'
- Use Daily_Cases for daily new cases or trends
- Use Cases for cumulative totals
- Filter by: 'Country/Region' and optionally 'Province/State'
- Use: px.line() for trends, px.bar() for one-time comparisons

---

🔹 **Dataset: us_cases**
- Columns: 'Admin2', 'Province_State', 'Country_Region', 'Date', 'Cases', 'Daily_Cases'
- Use Daily_Cases for trends or day-specific queries
- Use Cases if the user asks for total or cumulative cases
- Filter by: 'Province_State' or 'Admin2'
- Use: px.bar() for daily comparisons, px.line() for time series

---

📅 Date Handling (All Datasets):
- Always convert using: df['Date'] = pd.to_datetime(df['Date'])
- For exact date: df['Date'] == pd.to_datetime('YYYY-MM-DD')
- For month/year: use .dt.month and .dt.year

📊 Aggregation Tips:
- Use groupby('Date') or groupby('Province_State') as needed
- Always use .reset_index() after groupby

🖼️ Output Format:
- Only return Python code in triple backticks
- Assign your chart to a variable called fig
- DO NOT use markdown, print(), or return fig

Example output format:

python
fig = px.line(...)
fig.update_layout(title="...")
Your task is to understand the dataset type from {dataset_key} and generate an appropriate Plotly chart using only available column names. """



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

        result = run_code_and_return_plot(code, df, user_query)


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

@app.route("/summary", methods=["POST"])
def handle_summary():
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

        # 🎯 LLM Prompt: Generate only what's needed
        prompt = f"""
You are a Python data analyst.

### User Query:
"{user_query}"

You are working with a Pandas DataFrame `df` with columns:
{columns_list}

---

### Task:
- Understand the query and calculate ONLY what's requested:
   - For total deaths or cases ➜ assign to `total`
   - For max daily ➜ assign to `max_daily`
   - For peak date ➜ assign to `peak_date`
- If not asked, DO NOT calculate unnecessary values.
- If data is missing, assign "Data not available".
- If the dataset is related to deaths always use Daily_Deaths column to give output or to make sum or to get deaths between to dates
Only return Python code inside triple backticks. No explanations.

### Example:

Query: "Total deaths in India"
python
filtered_df = df[df['Country/Region'] == 'India']
total = filtered_df['Daily_Deaths'].sum()

Query: "Max daily deaths in USA"
python
filtered_df = df[df['Country/Region'] == 'USA']
max_daily = filtered_df['Daily_Deaths'].max()


If unclear:
total = "Data not available"
"""

        headers = {
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "agentica-org/deepcoder-14b-preview:free",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0
        }

        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)

        if response.status_code != 200:
            return jsonify({"error": f"OpenRouter API error: {response.text}"}), 500

        llm_data = response.json()
        raw_text = llm_data["choices"][0]["message"]["content"]
        code = extract_code_from_llm_response(raw_text)

        print(f"\n📝 Generated Code:\n{code}")

        # ⚙️ Execute LLM-generated code
        local_env = {"df": df.copy(), "pd": pd}
        try:
            exec(code, {}, local_env)
        except Exception as e:
            traceback.print_exc()
            return jsonify({"error": f"Code execution error: {str(e)}"}), 500

        # 📤 Dynamically build response
        response_lines = []

        if "total" in local_env:
            total_value = local_env.get("total")
            response_lines.append(f"Total: {safe_convert(total_value)}")

        if "max_daily" in local_env:
            max_daily_value = local_env.get("max_daily")
            response_lines.append(f"Max Daily: {safe_convert(max_daily_value)}")

        if "peak_date" in local_env:
            peak_date_value = local_env.get("peak_date")
            response_lines.append(f"Peak Date: {safe_convert(peak_date_value)}")

        summary_text = "\n".join(response_lines) if response_lines else "Data not available"

        return jsonify({
            "summary": summary_text.strip(),
            "error": None
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"{type(e).__name__}: {str(e)}"}), 500



if __name__ == "__main__":
    print("🚀 Flask server running at http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)