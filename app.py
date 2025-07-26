import streamlit as st
import yaml
import pandas as pd
import sqlite3
from datetime import date

DB_FILE = "nutrition_log.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE,
            calories INTEGER,
            protein INTEGER,
            carbs INTEGER,
            fat INTEGER,
            saturated_fat INTEGER,
            unsaturated_fat INTEGER,
            fiber INTEGER,
            sugar INTEGER,
            sodium INTEGER,
            score REAL,
            vitamin_highlights TEXT,
            suggestions TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_entry(entry):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO entries (
            date, calories, protein, carbs, fat, saturated_fat, unsaturated_fat, fiber, sugar, sodium, score, vitamin_highlights, suggestions
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        entry["Date"],
        entry["Calories"],
        entry["Protein"],
        entry["Carbs"],
        entry["Fat"],
        entry.get("Saturated Fat", 0),
        entry.get("Unsaturated Fat", 0),
        entry.get("Fiber", 0),
        entry.get("Sugar", 0),
        entry.get("Sodium", 0),
        entry["Score"],
        entry.get("Vitamin Highlights", ""),
        entry["Suggestions"]
    ))
    conn.commit()
    conn.close()

def get_all_entries():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM entries ORDER BY date DESC", conn)
    conn.close()
    return df

def get_averages():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("""
        SELECT 
            ROUND(AVG(calories), 1) AS avg_calories,
            ROUND(AVG(protein), 1) AS avg_protein,
            ROUND(AVG(carbs), 1) AS avg_carbs,
            ROUND(AVG(fat), 1) AS avg_fat,
            ROUND(AVG(saturated_fat), 1) AS avg_saturated_fat,
            ROUND(AVG(unsaturated_fat), 1) AS avg_unsaturated_fat,
            ROUND(AVG(fiber), 1) AS avg_fiber,
            ROUND(AVG(sugar), 1) AS avg_sugar,
            ROUND(AVG(sodium), 1) AS avg_sodium,
            ROUND(AVG(score), 1) AS avg_score
        FROM entries
    """, conn)
    conn.close()
    return df

# Initialize DB
init_db()

st.set_page_config(page_title="Nutrition Logger", layout="centered")
st.title("🥗 Daily Nutrition Tracker (Expanded)")

# Date selector
log_date = st.date_input("Select date to log:", value=date.today())

# Paste ChatGPT response
# Template YAML to preload in the input box
template_yaml = """
Calories: 1450
Protein: 75g
Carbs: 140g
Fat: 50g
Saturated Fat: 14g
Unsaturated Fat: 36g
Fiber: 10g
Sugar: 24g
Sodium: 1350mg
Score: 8/10
Vitamin Highlights:
- Good source of Calcium and Vitamin B12 from yogurt and cheese
- Moderate Magnesium from nuts
Suggestions:
- Add some vegetables for micronutrients and fiber
- Slightly reduce sodium intake by choosing lower sodium deli meats
""".strip()


st.markdown("### Paste ChatGPT Response")
input_text = st.text_area("ChatGPT Output example:", value= template_yaml ,height=300, placeholder=template_yaml)

if st.button("📥 Save Entry"):
    if not input_text.strip():
        st.warning("Please paste a response first.")
    else:
        try:
            data = yaml.safe_load(input_text)
            entry = {
                "Date": log_date.isoformat(),
                "Calories": int(str(data.get("Calories", 0)).replace("kcal", "").strip()),
                "Protein": int(str(data.get("Protein", 0)).replace("g", "").strip()),
                "Carbs": int(str(data.get("Carbs", 0)).replace("g", "").strip()),
                "Fat": int(str(data.get("Fat", 0)).replace("g", "").strip()),
                "Saturated Fat": int(str(data.get("Saturated Fat", 0)).replace("g", "").strip()),
                "Unsaturated Fat": int(str(data.get("Unsaturated Fat", 0)).replace("g", "").strip()),
                "Fiber": int(str(data.get("Fiber", 0)).replace("g", "").strip()),
                "Sugar": int(str(data.get("Sugar", 0)).replace("g", "").strip()),
                "Sodium": int(str(data.get("Sodium", 0)).replace("mg", "").strip()),
                "Score": float(str(data.get("Score", 0)).split("/")[0].strip()),
                "Vitamin Highlights": "\n".join(data.get("Vitamin Highlights", [])) if isinstance(data.get("Vitamin Highlights"), list) else str(data.get("Vitamin Highlights", "")),
                "Suggestions": "; ".join(data.get("Suggestions", []))
            }
            save_entry(entry)
            st.success(f"Entry for {log_date.isoformat()} saved to database.")
        except Exception as e:
            st.error(f"Failed to parse or save. Check formatting.\n\n{e}")


# Fetch entry for selected date only
def get_entry_by_date(selected_date):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM entries WHERE date = ?", (selected_date,))
    row = c.fetchone()
    conn.close()
    if row:
        cols = ["id", "date", "calories", "protein", "carbs", "fat", "saturated_fat",
                "unsaturated_fat", "fiber", "sugar", "sodium", "score", "vitamin_highlights", "suggestions"]
        return dict(zip(cols, row))
    else:
        return None
entry = get_entry_by_date(log_date.isoformat())

import matplotlib.pyplot as plt
import numpy as np
import altair as alt

# After your existing code, replace your "Past Logs" display with tabs:

tab1, tab2 = st.tabs(["📅 Nutrition Log", "📈 Averages & Trends"])

with tab1:
    st.markdown("### 📅 Nutrition Details for Selected Date")
    entry = get_entry_by_date(log_date.isoformat())
    if entry:
        metrics = {
            "Calories (kcal)": entry["calories"],
            "Protein (g)": entry["protein"],
            "Carbs (g)": entry["carbs"],
            "Fat (g)": entry["fat"],
            "Saturated Fat (g)": entry["saturated_fat"],
            "Unsaturated Fat (g)": entry["unsaturated_fat"],
            "Fiber (g)": entry["fiber"],
            "Sugar (g)": entry["sugar"],
            "Sodium (mg)": entry["sodium"],
        }
        col1, col2 = st.columns([2, 1])
        with col1:
            for name in metrics:
                st.write(f"**{name}**")
        with col2:
            for value in metrics.values():
                st.write(f"{value}")
        st.markdown(f"<h1 style='text-align:center; color:#4CAF50;'>{entry['score']}/10</h1>", unsafe_allow_html=True)
        if entry["suggestions"]:
            st.markdown("### 💡 Suggestions")
            for sug in entry["suggestions"].split("; "):
                st.write(f"- {sug}")
        if entry["vitamin_highlights"]:
            st.markdown("### 🌟 Vitamin Highlights")
            for vit in entry["vitamin_highlights"].split("\n"):
                st.write(f"- {vit}")
    else:
        st.info("No entry for this date. Paste a response and save to log nutrition here.")

import altair as alt

with tab2:
    st.markdown("### 📊 Running Average Score Trend")
    df = get_all_entries()
    if df.empty:
        st.info("No data to display trends yet.")
    else:
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')

        # Calculate running means (cumulative averages)
        df['running_avg_score'] = df['score'].expanding().mean()
        df['running_avg_calories'] = df['calories'].expanding().mean()
        df['running_avg_protein'] = df['protein'].expanding().mean()
        df['running_avg_carbs'] = df['carbs'].expanding().mean()
        df['running_avg_fat'] = df['fat'].expanding().mean()

        # Altair line chart for running_avg_score only
        chart = alt.Chart(df).mark_line(point=True).encode(
            x='date:T',
            y=alt.Y('running_avg_score:Q', title='Running Avg Score'),
            tooltip=[alt.Tooltip('date:T', title='Date'), alt.Tooltip('running_avg_score:Q', title='Avg Score', format='.2f')],
        ).properties(
            width=700,
            height=400,
            title='Running Average Score Over Time'
        ).interactive()

        st.altair_chart(chart, use_container_width=True)

        # Show all latest averages as numeric metrics below
        latest = df.iloc[-1]
        st.markdown("### 📋 Summary Statistics (All Time)")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Latest Avg Score", f"{latest['running_avg_score']:.2f}/10")
            st.metric("Latest Avg Calories", f"{latest['running_avg_calories']:.0f} kcal")
        with col2:
            st.metric("Latest Avg Protein", f"{latest['running_avg_protein']:.0f} g")
            st.metric("Latest Avg Carbs", f"{latest['running_avg_carbs']:.0f} g")
        with col3:
            st.metric("Latest Avg Fat", f"{latest['running_avg_fat']:.0f} g")
