import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ------------------------------------------------------------
# Page setup and visual theme
# ------------------------------------------------------------
st.set_page_config(
    page_title="Malaysia State Data Visualisation",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp { background: #F5F8FC; }
    [data-testid="stHeader"] { background: rgba(245,248,252,0.92); }
    [data-testid="stSidebar"] { background: #102A56; }
    [data-testid="stSidebar"] * { color: #F4F7FC !important; }
    [data-testid="stSidebar"] [data-baseweb="select"] * { color: #172B4D !important; }
    .main-title {
        font-size: 2.15rem; font-weight: 800; color: #142D55;
        letter-spacing: -0.7px; margin-bottom: 0.1rem;
    }
    .subtitle { color: #64748B; font-size: 0.96rem; margin-bottom: 1.1rem; }
    .section-kicker {
        color: #2672C9; font-size: 0.76rem; font-weight: 800;
        letter-spacing: 1.2px; text-transform: uppercase;
    }
    .insight-card {
        background: #EAF2FC; border-left: 4px solid #2672C9;
        border-radius: 10px; padding: 15px 18px; color: #18365F;
        margin: 8px 0 16px 0;
    }
    .small-note { color: #64748B; font-size: 0.82rem; }
    div[data-testid="stMetric"] {
        background: #FFFFFF; border: 1px solid #E3EAF3;
        border-radius: 13px; padding: 14px 16px;
        box-shadow: 0 2px 9px rgba(20,45,85,0.04);
    }
    div[data-testid="stMetricLabel"] { color: #64748B; }
    div[data-testid="stMetricValue"] { color: #163B70; }
    div[data-testid="stPlotlyChart"] {
        background: #FFFFFF; border: 1px solid #E5EBF3;
        border-radius: 13px; padding: 8px;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background: #E8EFF8; border-radius: 8px 8px 0 0;
        padding: 9px 16px; color: #18365F;
    }
</style>
""", unsafe_allow_html=True)

NAVY = "#173B70"
BLUE = "#2878C8"
LIGHT_BLUE = "#8AB6E8"
TEAL = "#2A9D8F"
ORANGE = "#E9A23B"
MUTED = "#64748B"
CHART_TEMPLATE = "plotly_white"

st.markdown('<div class="main-title">Malaysia: Births, Education & Household Income</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Scientific Visualisation Assignment · JIE42403 · State-level analysis</div>', unsafe_allow_html=True)

STATE_COORDS = {
    "Johor": (1.9, 103.4), "Kedah": (6.1, 100.4), "Kelantan": (5.3, 102.0),
    "Melaka": (2.2, 102.2), "Negeri Sembilan": (2.7, 102.2), "Pahang": (3.8, 103.2),
    "Perak": (4.7, 101.0), "Perlis": (6.5, 100.2), "Penang": (5.4, 100.3),
    "Sabah": (5.4, 117.0), "Sarawak": (2.8, 113.7), "Selangor": (3.2, 101.5),
    "Terengganu": (5.2, 103.0), "Kuala Lumpur": (3.14, 101.69),
    "Labuan": (5.3, 115.2), "Putrajaya": (2.93, 101.69),
}

def clean_state(series):
    return (series.astype(str).str.strip()
            .replace({
                "Pulau Pinang": "Penang", "W.P. Kuala Lumpur": "Kuala Lumpur",
                "W.P. Labuan": "Labuan", "W.P. Putrajaya": "Putrajaya",
            }))

def numeric(series):
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False)
        .str.replace("RM", "", regex=False).str.replace("%", "", regex=False).str.strip(),
        errors="coerce",
    )

def find_col(df, candidates):
    normalised = {str(c).strip().lower().replace("_", " "): c for c in df.columns}
    for candidate in candidates:
        key = candidate.lower().replace("_", " ")
        if key in normalised:
            return normalised[key]
    for col in df.columns:
        low = str(col).lower().replace("_", " ")
        if any(candidate.lower().replace("_", " ") in low for candidate in candidates):
            return col
    return None

def load_csv(upload, label):
    if upload is None:
        return None
    try:
        return pd.read_csv(upload)
    except Exception as exc:
        st.error(f"Unable to read {label}: {exc}")
        return None

def latest_slice(df):
    if "Year" in df.columns and df["Year"].notna().any():
        year = int(df["Year"].max())
        return df[df["Year"] == year].copy(), year
    return df.copy(), None

def style_fig(fig, height=430):
    fig.update_layout(
        template=CHART_TEMPLATE, height=height,
        margin=dict(l=22, r=22, t=55, b=35),
        font=dict(family="Arial", color="#334155", size=12),
        title=dict(font=dict(size=16, color=NAVY), x=0.02, xanchor="left"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FFFFFF",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#E9EEF5", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#E9EEF5", zeroline=False)
    return fig

def show_map(df, value_col, title, color_label):
    map_df = df.copy()
    map_df["Latitude"] = map_df["State"].map(lambda state: STATE_COORDS.get(state, (None, None))[0])
    map_df["Longitude"] = map_df["State"].map(lambda state: STATE_COORDS.get(state, (None, None))[1])
    map_df = map_df.dropna(subset=["Latitude", "Longitude", value_col])
    if map_df.empty:
        st.warning("No recognised Malaysian state names are available for the map.")
        return
    fig = px.scatter_geo(
        map_df, lat="Latitude", lon="Longitude", color=value_col, size=value_col,
        hover_name="State", hover_data={value_col: ":,.2f", "Latitude": False, "Longitude": False},
        scope="asia", color_continuous_scale=["#DCEBFA", "#78A9DF", "#174A86"],
        labels={value_col: color_label}, title=title, size_max=24,
    )
    fig.update_geos(
        center={"lat": 4.5, "lon": 109}, lataxis_range=[0, 8], lonaxis_range=[99, 120],
        showcountries=True, showcoastlines=True, showland=True,
        landcolor="#F0F4F8", countrycolor="#CBD5E1",
    )
    fig.update_layout(
        template=CHART_TEMPLATE, height=490, margin=dict(l=0, r=0, t=55, b=0),
        paper_bgcolor="rgba(0,0,0,0)", title=dict(font=dict(size=16, color=NAVY), x=0.02),
        coloraxis_colorbar=dict(title=color_label),
    )
    st.plotly_chart(fig, use_container_width=True)

def correlation_text(value, var_a, var_b):
    if pd.isna(value):
        return "The correlation could not be calculated because there are insufficient valid observations."
    strength = ("very weak" if abs(value) < 0.20 else
                "weak" if abs(value) < 0.40 else
                "moderate" if abs(value) < 0.60 else
                "strong" if abs(value) < 0.80 else "very strong")
    direction = "positive" if value > 0 else "negative" if value < 0 else "no linear"
    if value == 0:
        return f"The Pearson correlation is {value:.3f}, indicating no linear association between {var_a} and {var_b} in the selected data."
    return (f"The Pearson correlation is {value:.3f}, indicating a {strength} {direction} linear association "
            f"between {var_a} and {var_b}. This describes association, not causation.")

def section_heading(kicker, title, description=None):
    st.markdown(f'<div class="section-kicker">{kicker}</div>', unsafe_allow_html=True)
    st.subheader(title)
    if description:
        st.caption(description)

# ------------------------------------------------------------
# Sidebar: upload, filtering and navigation
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## DATA EXPLORER")
    st.caption("Upload the three assignment datasets")
    birth_file = st.file_uploader("01 · Annual live births", type="csv")
    school_file = st.file_uploader("02 · School completion", type="csv")
    income_file = st.file_uploader("03 · Household income", type="csv")
    st.divider()
    page = st.radio(
        "NAVIGATION",
        ["Overview", "Objective 1 · Births & Income",
         "Objective 2 · Completion & Income", "Objective 3 · Births & Completion"],
    )

birth_raw = load_csv(birth_file, "annual live births dataset")
school_raw = load_csv(school_file, "school completion dataset")
income_raw = load_csv(income_file, "household income dataset")

if not all(df is not None for df in [birth_raw, school_raw, income_raw]):
    st.info("Upload all three CSV files using the sidebar to generate the visualisation dashboard.")
    st.markdown("""
    **Required information**
    - Births: state, live births (ABS), and date/year if available
    - School: state, completion rate, sex, and date/year if available
    - Household income: state and median or mean household income
    """)
    st.stop()

# ------------------------------------------------------------
# Detect columns and prepare data
# ------------------------------------------------------------
b_state_col = find_col(birth_raw, ["state"])
b_value_col = find_col(birth_raw, ["live births", "abs", "births"])
b_date_col = find_col(birth_raw, ["date", "year"])

s_state_col = find_col(school_raw, ["state"])
s_value_col = find_col(school_raw, ["completion rate", "completion"])
s_sex_col = find_col(school_raw, ["sex", "gender"])
s_date_col = find_col(school_raw, ["date", "year"])
s_stage_col = find_col(school_raw, ["stage", "level"])

i_state_col = find_col(income_raw, ["state"])
# Prefer median household income if the dataset contains it; otherwise use mean.
i_value_col = find_col(income_raw, ["median household income", "median income", "median"])
income_measure = "Median household income" if i_value_col else "Mean household income"
if i_value_col is None:
    i_value_col = find_col(income_raw, ["mean household income", "mean income", "mean"])
i_date_col = find_col(income_raw, ["date", "year"])

if not all([b_state_col, b_value_col, s_state_col, s_value_col, i_state_col, i_value_col]):
    st.error("Some required columns were not detected. Check that the CSV files contain State, Live Births, Completion Rate, and a household income measure.")
    with st.expander("Show detected CSV columns"):
        st.write({
            "Birth dataset": list(birth_raw.columns),
            "School dataset": list(school_raw.columns),
            "Income dataset": list(income_raw.columns),
        })
    st.stop()

birth = birth_raw.copy()
birth["State"] = clean_state(birth[b_state_col])
birth["Live Births"] = numeric(birth[b_value_col])
birth["Year"] = pd.to_datetime(birth[b_date_col], errors="coerce").dt.year if b_date_col else pd.NA
birth = birth.dropna(subset=["State", "Live Births"])
birth = birth[~birth["State"].str.lower().isin(["malaysia", "nan", ""])]
birth = birth[birth["Live Births"] >= 0]

school = school_raw.copy()
school["State"] = clean_state(school[s_state_col])
school["Completion Rate"] = numeric(school[s_value_col])
school["Sex"] = school[s_sex_col].astype(str).str.strip().str.title() if s_sex_col else "Both"
school["Year"] = pd.to_datetime(school[s_date_col], errors="coerce").dt.year if s_date_col else pd.NA
school = school.dropna(subset=["State", "Completion Rate"])
school = school[~school["State"].str.lower().isin(["malaysia", "nan", ""])]
school = school[school["Completion Rate"].between(0, 100)]

income = income_raw.copy()
income["State"] = clean_state(income[i_state_col])
income[income_measure] = numeric(income[i_value_col])
income["Year"] = pd.to_datetime(income[i_date_col], errors="coerce").dt.year if i_date_col else pd.NA
income = income.dropna(subset=["State", income_measure])
income = income[~income["State"].str.lower().isin(["malaysia", "nan", ""])]
income = income[income[income_measure] >= 0]

# Optional school-stage filter
with st.sidebar:
    if s_stage_col:
        stage_options = sorted(school[s_stage_col].dropna().astype(str).unique().tolist())
        selected_stage = st.selectbox("SCHOOL STAGE", ["All stages"] + stage_options)
        if selected_stage != "All stages":
            school = school[school[s_stage_col].astype(str) == selected_stage]

birth_latest, birth_year = latest_slice(birth)
school_latest, school_year = latest_slice(school)
income_latest, income_year = latest_slice(income)

birth_by_state = birth_latest.groupby("State", as_index=False)["Live Births"].sum()
income_by_state = income_latest.groupby("State", as_index=False)[income_measure].median()
school_by_sex = school_latest.groupby(["State", "Sex"], as_index=False)["Completion Rate"].mean()
both_rows = school_by_sex[school_by_sex["Sex"].str.lower().isin(["both", "all", "total"])]
if not both_rows.empty:
    school_overall = both_rows.groupby("State", as_index=False)["Completion Rate"].mean()
else:
    school_overall = school_by_sex.groupby("State", as_index=False)["Completion Rate"].mean()

merged = (
    birth_by_state.merge(income_by_state, on="State", how="inner")
    .merge(school_overall, on="State", how="inner")
)
if merged.empty:
    st.error("No matching state names were found across the three datasets. Check state naming consistency.")
    st.stop()

# Interactive state filter: apply the same selected states to all objectives.
all_states = sorted(merged["State"].unique().tolist())
with st.sidebar:
    st.divider()
    selected_states = st.multiselect("FILTER STATES", all_states, default=all_states)
if not selected_states:
    st.warning("Select at least one state in the sidebar to display the analysis.")
    st.stop()

merged = merged[merged["State"].isin(selected_states)].copy()
birth_view = birth_by_state[birth_by_state["State"].isin(selected_states)].copy()
income_view = income_by_state[income_by_state["State"].isin(selected_states)].copy()
school_view = school_overall[school_overall["State"].isin(selected_states)].copy()
school_sex_view = school_by_sex[school_by_sex["State"].isin(selected_states)].copy()

period_text = (
    f"Births: {birth_year or 'not stated'} · "
    f"School: {school_year or 'not stated'} · "
    f"Income: {income_year or 'not stated'}"
)
st.caption(f"Selected states: {len(selected_states)} of {len(all_states)} · {period_text}")
if len({y for y in [birth_year, school_year, income_year] if y is not None}) > 1:
    st.warning("The latest available year is selected independently for each dataset. Check that the reference periods are comparable before interpreting relationships.")

# ------------------------------------------------------------
# Dashboard pages
# ------------------------------------------------------------
if page == "Overview":
    section_heading("DASHBOARD OVERVIEW", "A snapshot of Malaysia by state",
                    "Explore how births, school completion and household income vary across the selected states.")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("States included", f"{merged['State'].nunique()}")
    k2.metric("Average live births", f"{merged['Live Births'].mean():,.0f}")
    k3.metric(f"Average {income_measure.lower()}", f"RM {merged[income_measure].mean():,.0f}")
    k4.metric("Average completion", f"{merged['Completion Rate'].mean():.1f}%")

    left, right = st.columns([1.05, 1])
    with left:
        fig = px.bar(
            income_view.sort_values(income_measure), x=income_measure, y="State",
            orientation="h", color=income_measure, color_continuous_scale=["#C9DDF3", NAVY],
            title=f"{income_measure} by state",
            labels={income_measure: "Household income (RM)", "State": ""},
        )
        fig.update_layout(coloraxis_showscale=False)
        style_fig(fig, max(400, 30 * len(income_view) + 100))
        st.plotly_chart(fig, use_container_width=True)
    with right:
        show_map(birth_view, "Live Births", "Geographical distribution of live births", "Live births")

    section_heading("DATA TABLE", "State-level summary", "Use this table to compare the three measures across selected states.")
    display = merged.rename(columns={income_measure: income_measure + " (RM)"})
    st.dataframe(
        display.sort_values("State").style.format({
            "Live Births": "{:,.0f}",
            income_measure + " (RM)": "RM {:,.0f}",
            "Completion Rate": "{:.2f}%",
        }),
        use_container_width=True, hide_index=True,
    )
    st.markdown('<div class="insight-card"><b>How to read this dashboard</b><br>Bar charts compare values between states, maps show geographical patterns, and scatter plots examine relationships between two numerical variables. Correlation does not prove causation.</div>', unsafe_allow_html=True)

elif page.startswith("Objective 1"):
    section_heading("OBJECTIVE 01", "Births & household income",
                    "To identify the relationship between annual live births and household income.")
    corr = merged["Live Births"].corr(merged[income_measure])
    c1, c2, c3 = st.columns(3)
    c1.metric("Average annual live births", f"{merged['Live Births'].mean():,.0f}")
    c2.metric(f"Average {income_measure.lower()}", f"RM {merged[income_measure].mean():,.0f}")
    c3.metric("Pearson correlation (r)", f"{corr:.3f}" if pd.notna(corr) else "N/A")

    left, right = st.columns([1.2, 0.8])
    with left:
        section_heading("2D VISUALISATION", "Scatter plot: births vs household income",
                        "Each point represents one state. Hover over a point to identify the state.")
        fig = px.scatter(
            merged, x=income_measure, y="Live Births", hover_name="State",
            trendline="ols" if len(merged) >= 3 else None,
            color_discrete_sequence=[BLUE],
            labels={income_measure: f"{income_measure} (RM)", "Live Births": "Annual live births"},
        )
        fig.update_traces(marker=dict(size=11, opacity=0.82, line=dict(width=1, color="white")))
        style_fig(fig, 430)
        st.plotly_chart(fig, use_container_width=True)
    with right:
        section_heading("GEOSPATIAL", "Live births across Malaysia",
                        "Larger and darker markers indicate higher values.")
        show_map(birth_view, "Live Births", "Annual live births by state", "Live births")

    section_heading("STATE COMPARISON", f"{income_measure} ranking",
                    "A sorted horizontal bar chart makes state ranking easier to compare.")
    ranked = income_view.sort_values(income_measure, ascending=True)
    fig = px.bar(
        ranked, x=income_measure, y="State", orientation="h", text_auto=",.0f",
        color=income_measure, color_continuous_scale=["#D9E8F7", "#2878C8", NAVY],
        labels={income_measure: "Household income (RM)", "State": ""},
    )
    fig.update_layout(coloraxis_showscale=False)
    style_fig(fig, max(390, 30 * len(ranked) + 100))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f'<div class="insight-card"><b>Interpretation</b><br>{correlation_text(corr, "annual live births", income_measure.lower())}</div>', unsafe_allow_html=True)

elif page.startswith("Objective 2"):
    section_heading("OBJECTIVE 02", "School completion & household income",
                    "To examine the relationship between school completion rates and household income.")
    corr = merged["Completion Rate"].corr(merged[income_measure])
    c1, c2, c3 = st.columns(3)
    c1.metric("Average completion rate", f"{merged['Completion Rate'].mean():.2f}%")
    c2.metric(f"Average {income_measure.lower()}", f"RM {merged[income_measure].mean():,.0f}")
    c3.metric("Pearson correlation (r)", f"{corr:.3f}" if pd.notna(corr) else "N/A")

    left, right = st.columns([1, 1])
    with left:
        section_heading("GEOSPATIAL", "School completion by state")
        show_map(school_view, "Completion Rate", "School completion rate by state", "Completion rate (%)")
    with right:
        section_heading("CATEGORY COMPARISON", "Completion rate by sex",
                        "Grouped bars compare male and female completion rates where those categories exist.")
        gender = school_sex_view[school_sex_view["Sex"].str.lower().isin(["male", "female"])]
        if gender.empty:
            st.info("Male/Female categories were not detected in the Sex column.")
        else:
            fig = px.bar(
                gender, x="State", y="Completion Rate", color="Sex", barmode="group",
                color_discrete_map={"Male": BLUE, "Female": ORANGE},
                labels={"Completion Rate": "Completion rate (%)", "State": ""},
            )
            fig.update_layout(xaxis_tickangle=-40)
            style_fig(fig, 470)
            st.plotly_chart(fig, use_container_width=True)

    section_heading("2D VISUALISATION", "Scatter plot: income vs completion rate",
                    "The regression line helps show the overall direction of the relationship.")
    fig = px.scatter(
        merged, x=income_measure, y="Completion Rate", hover_name="State",
        trendline="ols" if len(merged) >= 3 else None,
        color_discrete_sequence=[TEAL],
        labels={income_measure: f"{income_measure} (RM)", "Completion Rate": "Completion rate (%)"},
    )
    fig.update_traces(marker=dict(size=11, opacity=0.82, line=dict(width=1, color="white")))
    style_fig(fig, 430)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f'<div class="insight-card"><b>Interpretation</b><br>{correlation_text(corr, income_measure.lower(), "school completion rate")}</div>', unsafe_allow_html=True)

else:
    section_heading("OBJECTIVE 03", "Births & school completion",
                    "To analyse the relationship between annual live births and school completion rates.")
    corr = merged["Live Births"].corr(merged["Completion Rate"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Average annual live births", f"{merged['Live Births'].mean():,.0f}")
    c2.metric("Average completion rate", f"{merged['Completion Rate'].mean():.2f}%")
    c3.metric("Pearson correlation (r)", f"{corr:.3f}" if pd.notna(corr) else "N/A")

    section_heading("2D VISUALISATION", "Scatter plot: live births vs completion rate",
                    "Each point represents a state; use hover to inspect its values.")
    fig = px.scatter(
        merged, x="Live Births", y="Completion Rate", hover_name="State",
        trendline="ols" if len(merged) >= 3 else None,
        color_discrete_sequence=[ORANGE],
        labels={"Live Births": "Annual live births", "Completion Rate": "Completion rate (%)"},
    )
    fig.update_traces(marker=dict(size=11, opacity=0.82, line=dict(width=1, color="white")))
    style_fig(fig, 430)
    st.plotly_chart(fig, use_container_width=True)

    left, right = st.columns(2)
    with left:
        section_heading("STATE COMPARISON", "Annual live births by state")
        fig = px.bar(
            birth_view.sort_values("Live Births"), x="Live Births", y="State",
            orientation="h", color_discrete_sequence=[BLUE],
            labels={"Live Births": "Annual live births", "State": ""},
        )
        style_fig(fig, max(390, 30 * len(birth_view) + 100))
        st.plotly_chart(fig, use_container_width=True)
    with right:
        section_heading("STATE COMPARISON", "School completion by state")
        fig = px.bar(
            school_view.sort_values("Completion Rate"), x="Completion Rate", y="State",
            orientation="h", color_discrete_sequence=[TEAL],
            labels={"Completion Rate": "Completion rate (%)", "State": ""},
        )
        style_fig(fig, max(390, 30 * len(school_view) + 100))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown(f'<div class="insight-card"><b>Interpretation</b><br>{correlation_text(corr, "annual live births", "school completion rate")}</div>', unsafe_allow_html=True)

# ------------------------------------------------------------
# Method notes and data quality transparency
# ------------------------------------------------------------
with st.expander("Data preparation & visualisation methods"):
    st.markdown(f"""
    - **Filtering:** the dashboard allows selection of states and, where available, school stage.
    - **Data cleaning:** numeric values are converted to numbers; missing values and national-total rows are excluded.
    - **Aggregation:** live births are summed by state; household income and completion values are aggregated by state.
    - **Income measure:** **{income_measure}** was selected automatically when that column is present; otherwise the dashboard uses mean household income.
    - **Visual encoding:** scatter plots show relationships, horizontal bars support ranking, and geographical markers show state distribution.
    - **Statistical interpretation:** Pearson correlation measures linear association only. It does not establish causation.
    - **Time period:** the latest year is selected separately for each dataset when a year/date column is available.
    """)
st.caption("Scientific Visualisation · JIE42403 | Use the charts together with the data period and aggregation notes when writing your findings.")
