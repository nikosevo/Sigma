import streamlit as st
import sqlite3
import openai
from openai import OpenAI
import datetime
import os

# === SETUP OPENAI API ===
# openai.api_key = os.getenv("OPENAI_API_KEY")  # or replace with your key directly (not recommended)

# === DATABASE SETUP ===
conn = sqlite3.connect("food_log.db")
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS logs (
    date TEXT PRIMARY KEY,
    input TEXT,
    calories INTEGER,
    protein INTEGER,
    carbs INTEGER,
    fat INTEGER,
    fiber INTEGER,
    score INTEGER,
    feedback TEXT
)
''')
conn.commit()

# === GPT PROMPT FUNCTION ===
def analyze_food_input(food_text):
    prompt = f"""
Here is what I ate today: {food_text}

Please estimate:
- Total calories
- Macronutrients (protein, fat, carbs, fiber)
- Health score from 1 to 10
- Short feedback on diet quality

Return the result in this JSON format:
{{
  "calories": ...,
  "protein": ...,
  "carbs": ...,
  "fat": ...,
  "fiber": ...,
  "score": ...,
  "feedback": "..."
}}
"""

    client = OpenAI()

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )

    content = response.choices[0].message.content
    
    try:
        data = eval(content.strip())
        return data
    except:
        st.error("GPT response was malformed.")
        return None

# === STREAMLIT UI ===
st.set_page_config(page_title="Daily Food Logger", layout="centered")
st.title("🥗 Sigma")

# --- DATE PICKER ---
selected_date = st.date_input("Select date", value=datetime.date.today())

# --- INPUT BOX ---
food_input = st.text_area("What did you eat today?", placeholder="e.g. chicken, rice, salad, 1 protein bar")

# --- SUBMIT BUTTON ---
if st.button("Log Today’s Food"):
    if not food_input.strip():
        st.warning("Please enter some food items.")
    else:
        with st.spinner("Analyzing your day..."):
            gpt_result = analyze_food_input(food_input)

        if gpt_result:
            # Save to DB
            cursor.execute('''
            INSERT OR REPLACE INTO logs (date, input, calories, protein, carbs, fat, fiber, score, feedback)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(selected_date),
                food_input.strip(),
                gpt_result['calories'],
                gpt_result['protein'],
                gpt_result['carbs'],
                gpt_result['fat'],
                gpt_result['fiber'],
                gpt_result['score'],
                gpt_result['feedback']
            ))
            conn.commit()
            st.success("Logged successfully!")

# === VIEW EXISTING ENTRY ===
st.subheader("📅 View Existing Log")

cursor.execute("SELECT * FROM logs WHERE date = ?", (str(selected_date),))
row = cursor.fetchone()
if row:
    st.markdown(f"""
    **Input**: {row[1]}  
    **Calories**: {row[2]} kcal  
    **Protein**: {row[3]}g  
    **Carbs**: {row[4]}g  
    **Fat**: {row[5]}g  
    **Fiber**: {row[6]}g  
    **Health Score**: {row[7]}/10  
    **Feedback**: {row[8]}
    """)
else:
    st.info("No entry for this date.")

