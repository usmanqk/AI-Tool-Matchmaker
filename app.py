from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="VipervisionAI | Find the right AI tool",
    page_icon="🔍",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "ai_tools.csv"
VEE_FILE = BASE_DIR / "vee.png"
EXPECTED_TOOL_COUNT = 12
PRICE_CHECK_DATE = "Nov 6, 2026"

REQUIRED_COLUMNS = [
    "tool_name",
    "business_type",
    "challenge",
    "free_price",
    "monthly_cost",
    "price_note",
    "effort",
    "pros",
    "cons",
    "website",
    "source",
    "checked_date",
]

BUDGET_CAP = {
    "Free only": 0,
    "Under $20 a month": 20,
    "Under $50 a month": 50,
    "Under $100 a month": 100,
    "Over $100 a month": float("inf"),
}

JOBS = [
    "Reviews",
    "Customer Questions",
    "Social media",
    "Marketing",
    "Bookings",
    "Daily operations",
    "Scheduling",
    "Accounting",
]

BUSINESS_TYPES = ["Restaurant / Cafe", "Coffee Shop"]
BUDGET_OPTIONS = list(BUDGET_CAP)
COMFORT_OPTIONS = ["Keep it simple", "I can learn a bit"]


@st.cache_data
def load_tools(path):
    data = pd.read_csv(path)
    missing = [column for column in REQUIRED_COLUMNS if column not in data.columns]
    if missing:
        raise ValueError("The catalog is missing required columns: " + ", ".join(missing))
    data = data.copy()
    data["free_price"] = pd.to_numeric(data["free_price"], errors="coerce")
    data["monthly_cost"] = pd.to_numeric(data["monthly_cost"], errors="coerce")
    data["business_type"] = data["business_type"].fillna("")
    data["challenge"] = data["challenge"].fillna("")
    if data["tool_name"].isna().any() or data["tool_name"].duplicated().any():
        raise ValueError("Every catalog tool must have one unique name.")
    return data


try:
    tools = load_tools(DATA_FILE)
except (FileNotFoundError, pd.errors.ParserError, ValueError) as error:
    st.error("The tool catalog could not be loaded. Check ai_tools.csv and try again.")
    st.caption(str(error))
    st.stop()

if len(tools) != EXPECTED_TOOL_COUNT:
    st.warning(
        f"The catalog currently contains {len(tools)} tools. "
        f"The contest demonstration expects {EXPECTED_TOOL_COUNT}."
    )


def business_tools(data, business_type):
    """Return tools whose catalog business type includes the selected type."""
    return data[
        data["business_type"].apply(
            lambda value: business_type in [part.strip() for part in str(value).split(",")]
        )
    ].copy()


def price_fits(row, cap):
    """Check whether a published free starting option or monthly price fits."""
    if pd.notna(row["free_price"]) and row["free_price"] == 0:
        return True
    if pd.isna(row["monthly_cost"]):
        return False
    return float(row["monthly_cost"]) <= cap


def score_tools(data, job, cap, comfort):
    """Explainable rule based score: job fit 3, price fit 2, effort fit 1."""
    scored = []
    for _, row in data.iterrows():
        if row["challenge"] != job:
            continue

        score = 3
        breakdown = {
            "Job fit": 3,
            "Price fit": 0,
            "Effort fit": 0,
        }
        reasons = [f"Matches your job: {job}"]

        if price_fits(row, cap):
            score += 2
            breakdown["Price fit"] = 2
            if pd.notna(row["free_price"]) and row["free_price"] == 0:
                reasons.append("Has a free starting option")
            else:
                reasons.append(
                    f"Published monthly price is ${float(row['monthly_cost']):,.2f}"
                )
        elif pd.isna(row["monthly_cost"]):
            reasons.append("Price is quote only, so budget fit cannot be confirmed")
        else:
            reasons.append("Published starting price is above your selected budget")

        if row["effort"] == "Easy":
            score += 1
            breakdown["Effort fit"] = 1
            reasons.append("Setup is marked easy in the catalog")
        elif row["effort"] == "Medium" and comfort == "I can learn a bit":
            score += 1
            breakdown["Effort fit"] = 1
            reasons.append("Medium setup matches your comfort level")
        elif row["effort"] == "Medium":
            reasons.append("Setup is medium and may need extra learning")

        scored.append(
            {
                "score": score,
                "tool": row,
                "reasons": reasons,
                "breakdown": breakdown,
            }
        )

    # Stable alphabetical order makes equal scores reproducible.
    scored.sort(key=lambda item: (-item["score"], str(item["tool"]["tool_name"]).casefold()))
    return scored


def show_tool_link(url):
    """Display a readable link without exposing a raw URL as page text."""
    st.markdown(f"[Visit provider website]({url})")


def show_tool_result(item, number):
    tool = item["tool"]
    st.markdown(f"#### {number}. {tool['tool_name']}")
    st.write(f"**Fit score:** {item['score']} out of 6")
    st.write(
        "Score breakdown: "
        f"job fit {item['breakdown']['Job fit']} out of 3, "
        f"price fit {item['breakdown']['Price fit']} out of 2, "
        f"effort fit {item['breakdown']['Effort fit']} out of 1."
    )
    st.write(f"**Price:** {tool['price_note']}")
    st.write(f"**Setup:** {tool['effort']}")
    st.write("**Why it matched:** " + "; ".join(item["reasons"]))
    st.write(f"**What it does well:** {tool['pros']}")
    st.write(f"**What to check:** {tool['cons']}")
    show_tool_link(tool["website"])
    st.caption(
        f"Price checked {PRICE_CHECK_DATE}. "
        "Verify the current plan with the provider before purchase."
    )
    st.markdown(f"[Source details](https://{tool['source']})")


def show_first_week_plan(tool):
    st.subheader(f"Your first week with {tool['tool_name']}")
    st.write("1. Visit the provider website and review the current plan and terms.")
    st.write("2. Check whether the tool works with the systems your business already uses.")
    st.write("3. Test one real task with a small amount of work before relying on it.")
    st.write("4. After seven days, compare the time saved and the actual cost.")
    st.caption(
        "This is an adoption checklist. VipervisionAI does not create accounts, "
        "connect systems, or purchase tools for you."
    )


def build_starter_stack(pool, cap, comfort):
    """Top scoring tool for up to three different jobs, same rules as the quiz."""
    stack = []
    for job in JOBS:
        ranked = score_tools(pool, job, cap, comfort)
        if ranked:
            stack.append({"job": job, "item": ranked[0]})
        if len(stack) == 3:
            break
    return stack


def show_starter_stack(pool, budget_label, comfort):
    stack = build_starter_stack(pool, BUDGET_CAP[budget_label], comfort)
    if not stack:
        return
    st.subheader("Your starter stack")
    st.write(
        "One top tool for each of up to three different jobs, "
        "scored with the same rules as your quiz answers."
    )
    monthly_total = 0.0
    quote_only = False
    rows = []
    for entry in stack:
        tool = entry["item"]["tool"]
        st.write(
            f"**{tool['tool_name']}** for {entry['job']}: "
            f"{tool['price_note']}. Score "
            f"{entry['item']['score']} out of 6."
        )
        show_tool_link(tool["website"])
        rows.append(
            {
                "Tool": tool["tool_name"],
                "Job": entry["job"],
                "Price": tool["price_note"],
                "Website": tool["website"],
            }
        )
        if pd.isna(tool["monthly_cost"]):
            quote_only = True
        else:
            monthly_total += float(tool["monthly_cost"])
    total_line = f"Estimated monthly total: ${monthly_total:,.0f}."
    if quote_only:
        total_line += " A quote only tool is not counted in this total."
    st.write(total_line)
    st.caption("Monthly total uses published starting prices only.")
    stack_csv = pd.DataFrame(rows).to_csv(index=False)
    st.download_button(
        "Download your starter stack",
        data=stack_csv,
        file_name="vipervision-starter-stack.csv",
        mime="text/csv",
    )


# Navigation and hero
st.markdown(
    "<div id='top'></div>"
    "VipervisionAI, AI Tool Matchmaker &nbsp;|&nbsp; "
    "[Home](#top) &nbsp;|&nbsp; "
    "[About the Website](#about-the-website) &nbsp;|&nbsp; "
    "[About the Creators](#about-the-creators)",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div style="background-color:#0b1e4b; padding:24px; text-align:center;
                border-radius:8px;">
      <h1 style="color:#2fd47a; margin:0;">VipervisionAI</h1>
      <p style="color:#ffffff; margin:8px 0 0;">
        Find the right AI tools for your small business.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

vee_col, greet_col = st.columns([1, 2])
with vee_col:
    if VEE_FILE.exists():
        st.image(str(VEE_FILE), caption="Vee, your guide", use_container_width=True)
with greet_col:
    with st.chat_message(
        "assistant", avatar=str(VEE_FILE) if VEE_FILE.exists() else "assistant"
    ):
        st.write(
            "Hi, I am Vee! Tell me your top business goal, "
            "and I will help you compare up to three real AI tools."
        )
    st.write(
        "Answer five questions to see a ranked shortlist with a clear score "
        "breakdown, real catalog prices, and practical next steps."
    )

st.subheader("What Vee can help you explore")
card1, card2, card3 = st.columns(3)
with card1:
    st.markdown("#### Customer questions")
    st.write("Review replies and customer conversations.")
    st.caption("Catalog examples include Google Business Profile and Podium.")
with card2:
    st.markdown("#### Marketing")
    st.write("Email campaigns and social content.")
    st.caption("Catalog examples include Mailchimp and Canva.")
with card3:
    st.markdown("#### Bookings and operations")
    st.write("Online bookings, scheduling, and daily tasks.")
    st.caption("Catalog examples include Square Appointments and Homebase.")

stat1, stat2, stat3 = st.columns(3)
with stat1:
    st.metric("Real tools in the catalog", len(tools))
with stat2:
    st.metric("Jobs covered", tools["challenge"].nunique())
with stat3:
    st.metric("Prices checked", PRICE_CHECK_DATE)


# Recommendation questionnaire
st.header("Find my tools")
st.write(
    "Choose the answers that best describe your business. "
    "The score is a rule based fit guide, not a customer rating."
)

with st.form("recommendation_form"):
    with st.container(border=True):
        st.write("**1. What type of business do you operate?**")
        business_type = st.selectbox(
            "Business type",
            BUSINESS_TYPES,
            label_visibility="collapsed",
        )
    with st.container(border=True):
        st.write("**2. What is your biggest business challenge?**")
        job = st.selectbox("Business challenge", JOBS, label_visibility="collapsed")
    with st.container(border=True):
        st.write("**3. What is your budget for AI tools?**")
        budget_label = st.selectbox(
            "Monthly budget",
            BUDGET_OPTIONS,
            label_visibility="collapsed",
        )
    with st.container(border=True):
        st.write("**4. How many employees do you have?**")
        employees = st.slider(
            "Number of employees",
            1,
            50,
            1,
            label_visibility="collapsed",
        )
    with st.container(border=True):
        st.write("**5. How comfortable are you with technology?**")
        comfort = st.selectbox(
            "Technology comfort",
            COMFORT_OPTIONS,
            label_visibility="collapsed",
        )
    submitted = st.form_submit_button("Find my tools", type="primary")

if submitted:
    cap = BUDGET_CAP[budget_label]
    pool = business_tools(tools, business_type)
    ranked = score_tools(pool, job, cap, comfort)
    st.session_state["recommendation_results"] = {
        "business_type": business_type,
        "job": job,
        "budget_label": budget_label,
        "employees": employees,
        "comfort": comfort,
        "ranked_names": [item["tool"]["tool_name"] for item in ranked[:3]],
    }

if "recommendation_results" in st.session_state:
    result = st.session_state["recommendation_results"]
    pool = business_tools(tools, result["business_type"])
    ranked = score_tools(
        pool,
        result["job"],
        BUDGET_CAP[result["budget_label"]],
        result["comfort"],
    )
    st.subheader("Your best matching tools")
    st.write(
        f"Matched to {result['business_type']} and {result['job']}, "
        f"for a team of {result['employees']}."
    )
    st.info(
        "How the score works: job fit is worth 3 points, price fit is worth "
        "2 points, and effort fit is worth 1 point. Equal scores are listed "
        "alphabetically. A score is not a review or a guarantee of results."
    )
    if not ranked:
        st.warning(
            "No catalog tools are listed for this job and business type. "
            "Try another job to explore the current catalog."
        )
    else:
        for index, item in enumerate(ranked[:3], start=1):
            with st.container(border=True):
                show_tool_result(item, index)
        show_first_week_plan(ranked[0]["tool"])
        show_starter_stack(pool, result["budget_label"], result["comfort"])


# Catalog
st.header("Catalog: all tools")
st.write(
    f"The catalog contains {len(tools)} tools. Prices were checked "
    f"{PRICE_CHECK_DATE}. Provider prices and terms can change."
)
catalog_col1, catalog_col2 = st.columns([1, 2])
with catalog_col1:
    job_filter = st.selectbox("Filter by job", ["All"] + sorted(tools["challenge"].unique()))
with catalog_col2:
    business_filter = st.selectbox("Filter by business", ["All"] + BUSINESS_TYPES)

shown = tools.copy()
if job_filter != "All":
    shown = shown[shown["challenge"] == job_filter]
if business_filter != "All":
    shown = business_tools(shown, business_filter)

st.caption(f"Showing {len(shown)} catalog tools.")
for _, tool in shown.iterrows():
    with st.container(border=True):
        st.markdown(f"#### {tool['tool_name']}")
        st.write(f"**Job:** {tool['challenge']}  |  **Business:** {tool['business_type']}")
        st.write(f"**Price:** {tool['price_note']}  |  **Setup:** {tool['effort']}")
        st.write(f"**What it does well:** {tool['pros']}")
        st.write(f"**What to check:** {tool['cons']}")
        show_tool_link(tool["website"])
        st.caption(f"Price checked {PRICE_CHECK_DATE}.")
        st.markdown(f"[Source details](https://{tool['source']})")


# Comparison
st.header("Compare up to three tools")
picked = st.multiselect(
    "Choose tools to compare",
    tools["tool_name"].tolist(),
    max_selections=3,
)
if picked:
    compare = tools[tools["tool_name"].isin(picked)][
        ["tool_name", "challenge", "price_note", "effort", "pros", "cons"]
    ].rename(
        columns={
            "tool_name": "Tool",
            "challenge": "Job",
            "price_note": "Price",
            "effort": "Setup",
            "pros": "What it does well",
            "cons": "What to check",
        }
    )
    st.dataframe(compare, use_container_width=True, hide_index=True)


# Return on investment calculator
st.header("Is it worth it? ROI calculator")
st.write(
    "Use your own estimates to explore a possible return. "
    "The time reduction is an assumption, not a measured result."
)
hours = st.slider("Hours per week spent on this task", 0, 40, 5)
value = st.slider("Value of your time, dollars per hour", 10, 100, 25)
reduction = st.slider("Assumed time reduction, percent", 0, 80, 30)
tool_price = st.slider("Tool price, dollars per month", 0, 500, 0)

monthly_time_value = hours * value * 4.33
estimated_savings = monthly_time_value * reduction / 100
estimated_net = estimated_savings - tool_price

roi1, roi2, roi3 = st.columns(3)
with roi1:
    st.metric("Monthly time value", f"${monthly_time_value:,.0f}")
with roi2:
    st.metric("Estimated monthly savings", f"${estimated_savings:,.0f}")
with roi3:
    st.metric("Estimated net monthly benefit", f"${estimated_net:,.0f}")
st.caption(
    "This estimate excludes setup time, taxes, fees, and changes in demand. "
    "Use the provider price and your own measured results before making a decision."
)


# Chat helper uses the same deterministic scoring rules
with st.expander("Ask Vee in chat"):
    st.write(
        "I use the same catalog and scoring rules as the questionnaire. "
        "I do not invent tools, prices, or reviews."
    )
    chat_business = st.selectbox(
        "What type of business do you run?",
        BUSINESS_TYPES,
        key="chat_business",
    )
    chat_job = st.selectbox("What is your top job?", JOBS, key="chat_job")
    chat_budget = st.selectbox(
        "What is your budget?",
        BUDGET_OPTIONS,
        key="chat_budget",
    )
    chat_comfort = st.selectbox(
        "How comfortable are you with technology?",
        COMFORT_OPTIONS,
        key="chat_comfort",
    )
    if st.button("Ask Vee", key="ask_vee"):
        chat_pool = business_tools(tools, chat_business)
        chat_ranked = score_tools(
            chat_pool,
            chat_job,
            BUDGET_CAP[chat_budget],
            chat_comfort,
        )
        if chat_ranked:
            st.write("Here are the strongest catalog matches for your answers.")
            for index, item in enumerate(chat_ranked[:3], start=1):
                with st.container(border=True):
                    show_tool_result(item, index)
        else:
            st.info(
                "I found no catalog match for that job and business type. "
                "Try another job to explore the current tools."
            )


# Research and methodology
with st.expander("Research and scoring method"):
    st.write(
        "The current catalog contains the tools listed above for restaurants "
        "and coffee shops. Each entry includes a job category, business type, "
        "setup effort, price note, provider website, source, and price check date."
    )
    st.write(
        "The fit score uses three visible rules. Job fit contributes 3 points "
        "when the catalog job matches. Price fit contributes 2 points when a "
        "published free starting option or monthly cost fits the selected budget. "
        "Effort fit contributes 1 point when the setup level matches the selected "
        "technology comfort."
    )
    st.write(
        "A quote only price is not treated as a confirmed budget fit. The score "
        "is a platform fit estimate, not an independent performance rating, "
        "customer review, or guarantee."
    )
    st.write(
        "Sources and dates are shown with each catalog entry. Provider pricing "
        "should be checked again before purchase."
    )
    free_count = int((tools["free_price"] == 0).sum())
    quote_count = int(tools["monthly_cost"].isna().sum())
    one_tool_jobs = sorted(
        job
        for job, count in tools["challenge"].value_counts().items()
        if count == 1
    )
    st.write(
        f"How we researched: the catalog covers {len(tools)} tools across "
        f"{tools['challenge'].nunique()} jobs, from {tools['source'].nunique()} "
        f"sources, all checked {PRICE_CHECK_DATE}. {free_count} tools have a "
        f"free starting option and {quote_count} is quote only. "
        f"{len(one_tool_jobs)} jobs have one catalog tool each: "
        f"{', '.join(one_tool_jobs)}."
    )


# Architecture and future work
with st.expander("How the prototype works and what comes next"):
    st.write(
        "**Current prototype:** the CSV catalog supplies tool details and "
        "published prices. The questionnaire filters by business type and job. "
        "A deterministic Python function calculates the fit score and reasons. "
        "The catalog, comparison view, ROI calculator, and chat helper use "
        "the same catalog data."
    )
    st.write(
        "**Scalability path:** keep catalog records separate from scoring logic, "
        "add validated tool records and business categories, and test scoring "
        "rules as the catalog grows. The current prototype does not claim "
        "production scale or live provider integrations."
    )
    st.write(
        "**Sixteen week direction:** research more small business types, "
        "validate compatibility with the systems they already use, explore "
        "multi tool workflows, and assess relevant Small Business Administration "
        "resources before adding integrations."
    )


# Free help beyond software
st.header("Free help beyond software")
st.write(
    "These free resources can help a small business owner beyond the tools "
    "above. VipervisionAI does not run them and does not receive anything "
    "from them."
)
st.markdown("[Find local SBA help](https://www.sba.gov/local-assistance)")
st.markdown("[SCORE business mentoring](https://www.score.org)")
st.markdown("[SBA resource partners](https://www.sba.gov/partners)")


# About sections
st.header("About the Website")
st.write(
    "VipervisionAI helps restaurants and coffee shops discover, compare, "
    "and explore adoption steps for AI tools. It includes a searchable catalog, "
    "a transparent rule based fit recommender, comparison, and an ROI estimate. "
    "It is not an AI picker and does not claim to deploy tools."
)

st.header("About the Creators")
st.write(
    "Built by The Vipers, Team 62, for the AI for Small Business Hackathon: "
    "Usman, Natalie, and Will, team lead."
)

st.caption(
    f"VipervisionAI, by The Vipers. Prices checked {PRICE_CHECK_DATE}. "
    "The prototype can continue improving after the video submission."
)
