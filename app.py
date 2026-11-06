import pandas as pd
import streamlit as st

st.set_page_config(page_title="VipervisionAI - Find the right AI tool", page_icon="🔍")

tools = pd.read_csv("ai_tools.csv")

# --- Top nav and hero banner, like Cypress's example ---
# Nav jumps to the About sections at the bottom. Hero is dark navy with
# a Vee emerald title only: Cypress said she is not loving the green, so
# there is no bright green border, just the emerald accent.
st.markdown(
    "VipervisionAI, AI Tool Matchmaker &nbsp;|&nbsp; "
    "[Home](#top) &nbsp;|&nbsp; "
    "[About the Website](#about-the-website) &nbsp;|&nbsp; "
    "[About the Creators](#about-the-creators)",
    unsafe_allow_html=True,
)
st.markdown(
    "<div style='background-color:#0b1e4b; padding:24px; text-align:center; border-radius:8px;'>"
    "<h1 style='color:#2fd47a; margin:0;'>VipervisionAI</h1>"
    "<p style='color:#ffffff; margin:8px 0 0;'>Find the right AI tools for your small business.</p>"
    "</div>",
    unsafe_allow_html=True,
)

# --- Hero: Vee landing interface, like the Vee image ---
# Vee greets the owner in a chat bubble, then 3 job cards and a stats
# strip. Every number here is real, from ai_tools.csv: 12 tools, 8 jobs,
# prices checked Nov 6, 2026. No invented totals.
# Vee as the mascot, like the Grok bot and Muse avatars in chat: her picture
# is the face of the greeting, Vee on the left, her speech bubble on the
# right, the same layout as the Vee image. vee.png is a tight crop of the
# Vee image, mascot only, no Discover text, no cards, no fake stats.
vee_col, greet_col = st.columns([1, 2])
with vee_col:
    st.image("vee.png", caption="Vee, your guide")
with greet_col:
    with st.chat_message("assistant", avatar="vee.png"):
        st.write("Hi, I am Vee! Tell me your top business goal, and I will find 3 AI tools for you.")
st.write(
    "I am Vee, your guide. I do not guess. "
    "Every tool below is real, with a real price checked on Nov 6, 2026. "
    "Answer 5 questions and I will show you the top 3, with the reason why."
)

st.subheader("What Vee can find for you")
card1, card2, card3 = st.columns(3)
with card1:
    st.write("### Customer Questions")
    st.write("Answer customer questions and reply to reviews in one inbox.")
    st.write("2 tools, for example Podium, Core $399/mo.")
with card2:
    st.write("### Marketing")
    st.write("Send email campaigns and keep customers coming back.")
    st.write("1 tool, for example Mailchimp, free up to 250 contacts.")
with card3:
    st.write("### Bookings")
    st.write("Take bookings online, with reminders and staff calendars.")
    st.write("2 tools, for example Square Appointments, free to start.")

stat1, stat2, stat3 = st.columns(3)
with stat1:
    st.metric("Real tools in the catalog", "12")
with stat2:
    st.metric("Jobs covered", "8")
with stat3:
    st.metric("Prices checked", "Nov 6, 2026")

# --- Quiz: 5 questions, no free text, one card per question ---
# Cards mirror Cypress's example: one bordered card per question, her
# wording, including the employees question. Employees is recorded and
# shown with the result, it does not change the score, because no catalog
# price is set by headcount; per user and per location notes are already
# in each tool's price note.
st.header("Find my tools")

with st.container(border=True):
    st.write("**What type of business do you operate?**")
    business_type = st.selectbox(
        "Select your business type...",
        ["Restaurant / Cafe", "Coffee Shop"],
        label_visibility="collapsed",
    )
with st.container(border=True):
    st.write("**What is your biggest business challenge?**")
    job = st.selectbox(
        "Select your biggest challenge...",
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
        label_visibility="collapsed",
    )
with st.container(border=True):
    st.write("**What is your budget for AI tools?**")
    budget_label = st.selectbox(
        "Select your budget...",
        ["Free only", "Under $20 a month", "Under $50 a month", "Under $100 a month", "Over $100 a month"],
        label_visibility="collapsed",
    )
with st.container(border=True):
    st.write("**How many employees do you have?**")
    employees = st.slider("How many employees do you have?", 1, 50, 1, label_visibility="collapsed")
    st.write(f"You selected: {employees}")
with st.container(border=True):
    st.write("**How comfortable are you with technology?**")
    comfort = st.selectbox(
        "How comfortable are you with technology?",
        ["Keep it simple", "I can learn a bit"],
        label_visibility="collapsed",
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
    st.write(f"Picked for a team of {employees}.")
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

# --- About sections, targets of the top nav ---
st.header("About the Website")
st.write(
    "VipervisionAI is a searchable catalog of 12 real AI tools for restaurants "
    "and coffee shops, with a dumb rule based recommender, not an AI picker. "
    "Answer 5 questions and get your top 3, with the reason why. "
    "Prices checked Nov 6, 2026, with source and date on every tool."
)
st.header("About the Creators")
st.write(
    "Built by The Vipers, Team 62, for the AI for Small Business Hack-A-Thon: "
    "Usman Khan, Cypress, and Will (wls170), team lead."
)

st.write("VipervisionAI, by The Vipers. Prices checked Nov 6, 2026. Prototype link can improve after Nov 8.")
