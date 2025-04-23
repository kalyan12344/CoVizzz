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
from typing import Dict, Optional, Union
import traceback

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# ✅ Dropbox Direct Download Links
DATASET_FILES = {
    "us_cases": "data/covid19_us_daily_cases.csv",
    "us_deaths": "data/covid19_us_daily_deaths.csv",
    "global_cases": "data/covid19_global_daily_cases.csv",
    "global_deaths": "data/covid19_global_daily_deaths.csv",
}

# ✅ Load datasets from Dropbox
def load_datasets() -> Dict[str, pd.DataFrame]:
    datasets = {}
    for key, url in DATASET_FILES.items():
        print(f"Loading dataset '{key}' from local file...")
        try:
            datasets[key] = pd.read_csv(url)
            print(f"✅ Loaded '{key}'")
        except Exception as e:
            print(f"❌ Error loading '{key}': {e}")
    return datasets

DATASETS = load_datasets()

# ===== Helper Functions =====
def extract_code_from_llm_response(text: str) -> str:
    # Extract code inside triple backticks
    match = re.search(r"```(?:python)?(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        # Fallback: Stop at first non-code line
        lines = text.strip().splitlines()
        code_lines = []
        for line in lines:
            if "Your task" in line or "Output" in line:
                break
            code_lines.append(line)
        return "\n".join(code_lines).strip()


def safe_convert(obj):
    if isinstance(obj, (np.ndarray, pd.Series)):
        return obj.tolist()
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if isinstance(obj, (np.int64, np.float64)):
        return float(obj)
    return str(obj)

def run_code_and_return_plot(code: str, df: pd.DataFrame, user_query: str) -> Dict[str, Optional[Union[dict, str]]]:
    local_env = {"df": df.copy(), "pd": pd, "go": go, "px": px}
    try:
        exec(code, {}, local_env)
        fig = local_env.get("fig")
        if fig is None:
            return {"plot": None, "error": "LLM did not generate a figure."}
        fig_dict = fig.to_dict()
        fig_json = json.loads(json.dumps(fig_dict, default=safe_convert))
        return {"plot": fig_json, "error": None}
    except Exception as e:
        traceback.print_exc()
        return {"plot": None, "error": str(e)}

# ===== /query Route =====
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
        prompt = f"""
You are a Python data visualization expert using Plotly and Pandas.

📝 A user asked: "{user_query}"

You are working with a Pandas DataFrame named `df` loaded from a COVID-19 dataset: `{dataset_key}`.

The available datasets are:

---

🔹 **Dataset: global_deaths**
- Columns: 'Country/Region', 'Province/State', 'Lat', 'Long', 'Date', 'Deaths', 'Daily_Deaths'
- Use `Daily_Deaths` for daily death queries (e.g., "deaths in India on April 21, 2021")
- Use `Deaths` for cumulative totals (e.g., "total deaths in Italy until May 2021")
- Filter by: 'Country/Region', optionally 'Province/State'
- Use: `px.bar()` for single-day, `px.line()` for trends

---

🔹 **Dataset: us_deaths**
- Columns: 'Admin2', 'Province_State', 'Country_Region', 'Date', 'Deaths', 'Daily_Deaths'
- Use `Daily_Deaths` for daily trends or per-date queries
- Use `Deaths` only for cumulative totals if the user asks for total deaths
- Filter by: 'Province_State' or 'Admin2'
- Use: `px.bar()` for single-day or comparison, `px.line()` for time series

---

🔹 **Dataset: global_cases**
- Columns: 'Country/Region', 'Province/State', 'Lat', 'Long', 'Date', 'Cases', 'Daily_Cases'
- Use `Daily_Cases` for daily new cases or trends
- Use `Cases` for cumulative totals
- Filter by: 'Country/Region' and optionally 'Province/State'
- Use: `px.line()` for trends, `px.bar()` for one-time comparisons

---

🔹 **Dataset: us_cases**
- Columns: 'Admin2', 'Province_State', 'Country_Region', 'Date', 'Cases', 'Daily_Cases'
- Use `Daily_Cases` for trends or day-specific queries
- Use `Cases` if the user asks for total or cumulative cases
- Filter by: 'Province_State' or 'Admin2'
- Use: `px.bar()` for daily comparisons, `px.line()` for time series

---
must use columns which are available in the dataset : {columns_list}



📅 Date Handling (All Datasets):
- Always convert using: `df['Date'] = pd.to_datetime(df['Date'])`
- For exact date: `df['Date'] == pd.to_datetime('YYYY-MM-DD')`
- For month/year: use `.dt.month` and `.dt.year`

📊 Aggregation Tips:
- Use `groupby('Date')` or `groupby('Province_State')` as needed
- Always use `.reset_index()` after groupby

🖼️ Output Format:
- Only return Python code in triple backticks
- Assign your chart to a variable called `fig`
- DO NOT use markdown, `print()`, or `return fig`

Example output format:

```python
fig = px.line(...)
fig.update_layout(title="...")
Your task is to understand the dataset type from {dataset_key} and generate an appropriate Plotly chart using only available column names{columns_list}.
- When using `update_xaxes` or `update_yaxes`, only use valid Plotly properties.
- For `rangemode`, allowed values are: 'normal', 'tozero', 'nonnegative'.
- Do NOT use 'auto' for `rangemode`.

🎯 Example Plotly Visualizations:

first make the df based on the user selected dataset and then make the plot
1️ Line Chart - Daily Cases Over Time in india

fig = px.line(df[df['Country/Region'] == 'India'], 
              x='Date', 
              y='Daily_Cases',
              title='Daily COVID-19 Cases in India Over Time')
fig.show()

2  Bar Chart – Top 10 Countries by Daily Deaths


country_deaths = df.groupby('Country/Region')['Daily_Deaths'].sum().reset_index()
top10 = country_deaths.sort_values(by='Daily_Deaths', ascending=False).head(10)
fig = px.bar(top10, x='Country/Region', y='Daily_Deaths', title='Top 10 Countries by Daily Deaths')
fig.show()

3 Choropleth Map – Global Daily Deaths

global_deaths = df.groupby('Country/Region')['Daily_Deaths'].sum().reset_index()
fig = px.choropleth(global_deaths, locations='Country/Region', locationmode='country names',
                    color='Daily_Deaths', title='Global COVID-19 Daily Deaths')
fig.show()

4  Pie Chart – Share of Daily Cases Among Top 5 Countries

country_cases = df.groupby('Country/Region')['Daily_Cases'].sum().reset_index()
top5 = country_cases.sort_values(by='Daily_Cases', ascending=False).head(5)
fig = px.pie(top5, names='Country/Region', values='Daily_Cases', title='Top 5 Countries by Daily Cases')
fig.show()

5 Area Chart – Daily Cases Over Time for Selected Countries

country_cases = df.groupby('Country/Region')['Daily_Cases'].sum().reset_index()
fig = px.area(country_cases, x='Date', y='Daily_Cases', color='Country/Region', title='Daily Cases Over Time by Country')
fig.show()

 Note: Always ensure proper data filtering, grouping, and sorting before plotting. Stick to using Daily_Cases for cases and Daily_Deaths for deaths across all chart types.

 """
        headers = {"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}", "Content-Type": "application/json"}
        payload = {"model": "agentica-org/deepcoder-14b-preview:free", "messages": [{"role": "user", "content": prompt}]}
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        if response.status_code != 200:
            return jsonify({"error": f"OpenRouter API error: {response.text}"}), 500
        llm_data = response.json()
        code = extract_code_from_llm_response(llm_data["choices"][0]["message"]["content"])
        result = run_code_and_return_plot(code, df, user_query)
        return jsonify({"code": code, "visualization": result["plot"], "error": result["error"]})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"{type(e).__name__}: {str(e)}"}), 500

# ===== /summary Route =====
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
```python
filtered_df = df[df['Country/Region'] == 'India']
total = filtered_df['Daily_Deaths'].sum()

Query: "Max daily deaths in USA"
```python
filtered_df = df[df['Country/Region'] == 'USA']
max_daily = filtered_df['Daily_Deaths'].max()


If unclear:
total = "Data not available"
"""
        headers = {"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}", "Content-Type": "application/json"}
        payload = {"model": "agentica-org/deepcoder-14b-preview:free", "messages": [{"role": "user", "content": prompt}], "temperature": 0}
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        if response.status_code != 200:
            return jsonify({"error": f"OpenRouter API error: {response.text}"}), 500
        llm_data = response.json()
        code = extract_code_from_llm_response(llm_data["choices"][0]["message"]["content"])
        local_env = {"df": df.copy(), "pd": pd}
        exec(code, {}, local_env)
        response_lines = []
        if "total" in local_env:
            response_lines.append(f"Total: {safe_convert(local_env.get('total'))}")
        if "max_daily" in local_env:
            response_lines.append(f"Max Daily: {safe_convert(local_env.get('max_daily'))}")
        if "peak_date" in local_env:
            response_lines.append(f"Peak Date: {safe_convert(local_env.get('peak_date'))}")
        summary_text = "\n".join(response_lines) if response_lines else "Data not available"
        return jsonify({"summary": summary_text.strip(), "error": None})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"{type(e).__name__}: {str(e)}"}), 500

# ===== Run Flask =====
if __name__ == "__main__":
    print("🚀 Flask server running at http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
