import pandas as pd
import streamlit as st

st.set_page_config(page_title="VipervisionAI - Find the right AI tool", page_icon="🔍")

tools = pd.read_csv("ai_tools.csv")

st.title("VipervisionAI")
st.write("Find the right AI tool for your small business, in minutes.")
st.write(
    "Hi, I am Vee, your guide. I do not guess. "
    "Every tool below is real, with a real price checked on Nov 6, 2026. "
    "Answer 4 questions and I will show you the top 3, with the reason why."
)

# --- Quiz: 4 questions, no free text ---
st.header("Find my tools")

business_type = st.selectbox(
    "What type of business are you?",
    ["Restaurant / Cafe", "Coffee Shop"],
)
job = st.selectbox(
    "What is your top job?",
    [
        "Reviews",
        "Customer Questions",
        "Social media",
        "Marketing",
        "Bookings",
        "Daily operations",
        "Scheduling",
        "Accounting",
    ],
)
budget_label = st.selectbox(
    "What is your budget?",
    ["Free only", "Under $20 a month", "Under $50 a month", "Under $100 a month", "Over $100 a month"],
)
comfort = st.selectbox(
    "How comfortable are you with new apps?",
    ["Keep it simple", "I can learn a bit"],
)

BUDGET_CAP = {
    "Free only": 0,
    "Under $20 a month": 20,
    "Under $50 a month": 50,
    "Under $100 a month": 100,
    "Over $100 a month": 100000,
}


def price_fits(row, cap):
    """True if the tool can be started within the budget."""
    if pd.notna(row["free_price"]) and row["free_price"] == 0:
        return True
    if pd.isna(row["monthly_cost"]):
        return False
    return row["monthly_cost"] <= cap


def score_tools(df, job, cap, comfort):
    scored = []
    for _, row in df.iterrows():
        score = 0
        reasons = []
        if row["challenge"] != job:
            continue
        score += 3
        reasons.append(f"Matches your job: {job}")
        if price_fits(row, cap):
            score += 2
            if pd.notna(row["free_price"]) and row["free_price"] == 0:
                reasons.append("Costs $0 to start")
            else:
                reasons.append(f"Costs ${row['monthly_cost']:.0f}/mo, fits your budget")
        if row["effort"] == "Easy":
            score += 1
            reasons.append("Setup is easy")
        elif row["effort"] == "Medium" and comfort == "I can learn a bit":
            score += 1
            reasons.append("Setup is medium, and you can learn a bit")
        scored.append((score, row, reasons))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


if st.button("Find my tools"):
    cap = BUDGET_CAP[budget_label]
    pool = tools[tools["business_type"].str.contains(business_type, na=False)]
    ranked = score_tools(pool, job, cap, comfort)
    st.subheader("Your top 3 tools")
    if not ranked:
        st.warning("No matching tools found. Try another job or budget.")
    else:
        for score, tool, reasons in ranked[:3]:
            st.write(f"### {tool['tool_name']}  —  score {score}/6")
            st.write(f"Price: {tool['price_note']}")
            st.write(f"Setup: {tool['effort']}")
            st.write(f"Why: {'; '.join(reasons)}")
            st.write(f"Good: {tool['pros']}")
            st.write(f"Watch out: {tool['cons']}")
            st.write(f"Website: {tool['website']}")
            st.write(f"Price checked: {tool['checked_date']}, source: {tool['source']}")
        top = ranked[0][1]
        st.subheader(f"Your first week with {top['tool_name']}")
        st.write("1. Open the website above and create the free account.")
        st.write("2. Add your business name, address, and hours.")
        st.write("3. Do one real job with it this week, for example answer one review or post one menu.")
        st.write("4. Check after 7 days: did it save you time? If yes, keep it. If no, try the next tool.")

# --- Catalog ---
st.header("Catalog: all 12 tools")
st.write("Prices checked Nov 6, 2026. Check the maker site again before you pay.")
job_filter = st.selectbox("Filter by job", ["All"] + sorted(tools["challenge"].unique().tolist()))
shown = tools if job_filter == "All" else tools[tools["challenge"] == job_filter]
for _, tool in shown.iterrows():
    st.write(f"### {tool['tool_name']}")
    st.write(f"Job: {tool['challenge']}  |  Business: {tool['business_type']}")
    st.write(f"Price: {tool['price_note']}  |  Setup: {tool['effort']}")
    st.write(f"Good: {tool['pros']}  |  Watch out: {tool['cons']}")
    st.write(f"Website: {tool['website']}  |  Source: {tool['source']}")

# --- Compare ---
st.header("Compare up to 3 tools")
picked = st.multiselect(
    "Pick tools to compare",
    tools["tool_name"].tolist(),
    max_selections=3,
)
if picked:
    compare = tools[tools["tool_name"].isin(picked)][
        ["tool_name", "challenge", "price_note", "effort", "pros", "cons"]
    ]
    st.dataframe(compare, use_container_width=True)

# --- ROI calculator: Will's idea, 4 sliders ---
st.header("Is it worth it? ROI calculator")
st.write("4 sliders. No AI, just your numbers.")
hours = st.slider("Hours per week spent on this task", 0, 40, 5)
value = st.slider("Value of your time, $ per hour", 10, 100, 25)
reduction = st.slider("Assumed time reduction, %", 0, 80, 30)
tool_price = st.slider("Price of the AI tool, $ per month", 0, 500, 0)
money_spent = hours * value * 4.33
saved = money_spent * reduction / 100
net = saved - tool_price
st.write(f"You spend about ${money_spent:,.0f} a month of your time on this task.")
st.write(f"At {reduction}% less time, you save about ${saved:,.0f} a month.")
st.write(f"Estimated net monthly benefit: ${net:,.0f} after the tool price.")

# --- Dumb chatbot helper ---
with st.expander("Find my tools in chat — Vee, the guide"):
    st.write(
        "Vee here. I run the same quiz, in chat form, using the same 12 tools. "
        "I never invent a tool or a price."
    )
    chat_job = st.selectbox(
        "What is your top job?",
        ["Reviews", "Customer Questions", "Social media", "Marketing", "Bookings", "Daily operations", "Scheduling", "Accounting"],
        key="chat_job",
    )
    chat_budget = st.selectbox(
        "What is your budget?",
        ["Free only", "Under $20 a month", "Under $50 a month", "Under $100 a month", "Over $100 a month"],
        key="chat_budget",
    )
    if st.button("Ask Vee", key="ask_vee"):
        cap = BUDGET_CAP[chat_budget]
        ranked = score_tools(tools, chat_job, cap, comfort)
        if ranked:
            for score, tool, reasons in ranked[:3]:
                st.write(f"{tool['tool_name']} — score {score}/6 — {tool['price_note']} — {'; '.join(reasons)}")
        else:
            st.write("I found no tool for that job and budget. Try a higher budget or another job.")

st.write("VipervisionAI, by The Vipers. Prices checked Nov 6, 2026. Prototype link can improve after Nov 8.")
