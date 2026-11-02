import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Malaysia State Data Visualisation", page_icon="📊", layout="wide")
st.title("Malaysia: Births, Education & Household Income")
st.caption("Scientific Visualisation Assignment | JIE42403")

STATE_COORDS = {
    "Johor": (1.9, 103.4), "Kedah": (6.1, 100.4), "Kelantan": (5.3, 102.0),
    "Melaka": (2.2, 102.2), "Negeri Sembilan": (2.7, 102.2), "Pahang": (3.8, 103.2),
    "Perak": (4.7, 101.0), "Perlis": (6.5, 100.2), "Pulau Pinang": (5.4, 100.3),
    "Penang": (5.4, 100.3), "Sabah": (5.4, 117.0), "Sarawak": (2.8, 113.7),
    "Selangor": (3.2, 101.5), "Terengganu": (5.2, 103.0),
    "W.P. Kuala Lumpur": (3.14, 101.69), "Kuala Lumpur": (3.14, 101.69),
    "W.P. Labuan": (5.3, 115.2), "Labuan": (5.3, 115.2),
    "W.P. Putrajaya": (2.93, 101.69), "Putrajaya": (2.93, 101.69)
}

def clean_state(s):
    return (s.astype(str).str.strip()
            .replace({"Pulau Pinang": "Penang", "W.P. Kuala Lumpur": "Kuala Lumpur",
                      "W.P. Labuan": "Labuan", "W.P. Putrajaya": "Putrajaya"}))

def numeric(series):
    return pd.to_numeric(series.astype(str).str.replace(",", "", regex=False).str.replace("RM", "", regex=False).str.strip(), errors="coerce")

def load_csv(upload, label):
    if upload is None:
        return None
    try:
        return pd.read_csv(upload)
    except Exception as e:
        st.error(f"Could not read {label}: {e}")
        return None

def find_col(df, candidates):
    lookup = {str(c).strip().lower().replace("_", " "): c for c in df.columns}
    for candidate in candidates:
        key = candidate.lower().replace("_", " ")
        if key in lookup:
            return lookup[key]
    for c in df.columns:
        low = str(c).lower().replace("_", " ")
        if any(k in low for k in candidates):
            return c
    return None

with st.sidebar:
    st.header("Data files")
    birth_file = st.file_uploader("1. Annual live births CSV", type="csv")
    school_file = st.file_uploader("2. School completion CSV", type="csv")
    income_file = st.file_uploader("3. Household income CSV", type="csv")
    st.divider()
    page = st.radio("Navigate", [
        "Overview", "Objective 1: Births & Income",
        "Objective 2: Completion & Income",
        "Objective 3: Births & Completion"
    ])

birth_raw = load_csv(birth_file, "birth dataset")
school_raw = load_csv(school_file, "school completion dataset")
income_raw = load_csv(income_file, "household income dataset")

if not all(x is not None for x in [birth_raw, school_raw, income_raw]):
    st.info("Upload all three CSV files in the sidebar to generate the report pages. The household income CSV is still required.")
    st.markdown("""
    **Expected columns**
    - Births: `state`, `date`, `abs` (live births)
    - School: `state`, `sex`, `date`, `completion` (also ideally `stage`)
    - Income: `state`, `mean income` (and `date`/`year` if available)
    """)
    st.stop()

# Identify and standardise columns
b_state, b_value = find_col(birth_raw, ["state"]), find_col(birth_raw, ["live births", "abs", "births"])
b_date = find_col(birth_raw, ["date", "year"])
s_state, s_value = find_col(school_raw, ["state"]), find_col(school_raw, ["completion rate", "completion"])
s_sex, s_date = find_col(school_raw, ["sex", "gender"]), find_col(school_raw, ["date", "year"])
s_stage = find_col(school_raw, ["stage", "level"])
i_state, i_value = find_col(income_raw, ["state"]), find_col(income_raw, ["mean income", "mean household income", "mean"])
i_date = find_col(income_raw, ["date", "year"])

if not all([b_state, b_value, s_state, s_value, i_state, i_value]):
    st.error("Some required columns were not detected. Please ensure the CSV files contain State, Live Births, Completion Rate, and Mean Income columns.")
    st.write("Detected columns:", {"birth": list(birth_raw.columns), "school": list(school_raw.columns), "income": list(income_raw.columns)})
    st.stop()

birth = birth_raw.copy()
birth["State"] = clean_state(birth[b_state])
birth["Live Births"] = numeric(birth[b_value])
if b_date:
    birth["Year"] = pd.to_datetime(birth[b_date], errors="coerce").dt.year
else:
    birth["Year"] = None
birth = birth.dropna(subset=["State", "Live Births"])
birth = birth[~birth["State"].str.lower().isin(["malaysia", "nan"])]

school = school_raw.copy()
school["State"] = clean_state(school[s_state])
school["Completion Rate"] = numeric(school[s_value])
school["Sex"] = school[s_sex].astype(str).str.title() if s_sex else "Both"
if s_date:
    school["Year"] = pd.to_datetime(school[s_date], errors="coerce").dt.year
else:
    school["Year"] = None
if s_stage:
    stages = sorted(school[s_stage].dropna().astype(str).unique())
    chosen_stage = st.sidebar.selectbox("School stage", stages)
    school = school[school[s_stage].astype(str) == chosen_stage]
school = school.dropna(subset=["State", "Completion Rate"])
school = school[~school["State"].str.lower().isin(["malaysia", "nan"])]

income = income_raw.copy()
income["State"] = clean_state(income[i_state])
income["Mean Income"] = numeric(income[i_value])
if i_date:
    income["Year"] = pd.to_datetime(income[i_date], errors="coerce").dt.year
else:
    income["Year"] = None
income = income.dropna(subset=["State", "Mean Income"])
income = income[~income["State"].str.lower().isin(["malaysia", "nan"])]

# Select most recent year available independently, clearly displayed
def latest_slice(df):
    if "Year" in df and df["Year"].notna().any():
        yr = int(df["Year"].max())
        return df[df["Year"] == yr].copy(), yr
    return df.copy(), None

b, by = latest_slice(birth)
s, sy = latest_slice(school)
i, iy = latest_slice(income)

# Aggregate to one record per state; school records retain sex for gender comparison
b_state = b.groupby("State", as_index=False)["Live Births"].sum()
i_state = i.groupby("State", as_index=False)["Mean Income"].mean()
s_state = s.groupby(["State", "Sex"], as_index=False)["Completion Rate"].mean()
s_both = s_state[s_state["Sex"].str.lower().isin(["both", "all", "total"])]
if not s_both.empty:
    s_overall = s_both.groupby("State", as_index=False)["Completion Rate"].mean()
else:
    s_overall = s_state.groupby("State", as_index=False)["Completion Rate"].mean()

merged = b_state.merge(i_state, on="State", how="inner").merge(s_overall, on="State", how="inner")
if merged.empty:
    st.error("No matching state names across the three datasets. Standardise state names (for example, Penang/Pulau Pinang) and try again.")
    st.stop()

def summary(df, col, label, fmt):
    st.metric(label, fmt.format(df[col].mean()))

def map_points(df, value, title, color_label):
    m = df.copy()
    m["lat"] = m["State"].map(lambda x: STATE_COORDS.get(x, (None, None))[0])
    m["lon"] = m["State"].map(lambda x: STATE_COORDS.get(x, (None, None))[1])
    m = m.dropna(subset=["lat", "lon", value])
    if m.empty:
        st.warning("No recognised Malaysian state names were found for the map.")
        return
    fig = px.scatter_geo(m, lat="lat", lon="lon", color=value, size=value,
                         hover_name="State", hover_data={value:":,.2f", "lat":False, "lon":False},
                         scope="asia", title=title, color_continuous_scale="Viridis",
                         labels={value: color_label})
    fig.update_geos(center={"lat": 4.5, "lon": 109}, lataxis_range=[0, 8], lonaxis_range=[99, 120],
                    showcountries=True, showcoastlines=True, showland=True)
    fig.update_layout(height=520, margin=dict(l=0,r=0,t=55,b=0))
    st.plotly_chart(fig, use_container_width=True)

if page == "Overview":
    st.subheader("Dataset overview")
    st.write("This application combines three state-level datasets: annual live births, school completion rates, and mean household income.")
    c1,c2,c3 = st.columns(3)
    c1.metric("Matched states", merged["State"].nunique())
    c2.metric("Mean live births", f'{merged["Live Births"].mean():,.0f}')
    c3.metric("Mean household income", f'RM {merged["Mean Income"].mean():,.0f}')
    st.caption(f"Latest available years used independently — births: {by or 'not provided'} | school: {sy or 'not provided'} | income: {iy or 'not provided'}. Confirm that the reference periods are comparable before interpreting relationships.")
    st.dataframe(merged.sort_values("State"), use_container_width=True)
    st.info("Use the sidebar to explore the three objectives. Correlation describes association, not causation.")

elif page.startswith("Objective 1"):
    st.header("Objective 1")
    st.write("To identify the relationship between annual live births and household income.")
    a,c = st.columns(2)
    a.metric("Average live births", f'{merged["Live Births"].mean():,.0f}')
    c.metric("Average mean income", f'RM {merged["Mean Income"].mean():,.0f}')
    corr = merged["Live Births"].corr(merged["Mean Income"])
    st.metric("Pearson correlation", f"{corr:.3f}" if pd.notna(corr) else "Not available")
    st.subheader("1. Scatter Plot: Live Births vs Mean Income")
    fig = px.scatter(merged, x="Mean Income", y="Live Births", hover_name="State", trendline="ols",
                     labels={"Mean Income":"Mean household income (RM)", "Live Births":"Annual live births"})
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("2. Malaysia State Map: Annual Live Births")
    map_points(b_state, "Live Births", "Annual live births by state", "Live births")
    st.subheader("3. Horizontal Bar Chart: Mean Income by State")
    fig = px.bar(i_state.sort_values("Mean Income"), x="Mean Income", y="State", orientation="h",
                 labels={"Mean Income":"Mean household income (RM)"})
    st.plotly_chart(fig, use_container_width=True)
    st.write(f"**Interpretation guide:** The scatter plot correlation is {corr:.3f}. A positive value indicates that states with higher mean income tend to have more live births in this dataset; a negative value indicates the opposite. This is an association and does not establish causation.")

elif page.startswith("Objective 2"):
    st.header("Objective 2")
    st.write("To examine the relationship between school completion rates and household income.")
    corr = merged["Completion Rate"].corr(merged["Mean Income"])
    a,c = st.columns(2)
    a.metric("Average completion rate", f'{merged["Completion Rate"].mean():.2f}%')
    c.metric("Pearson correlation", f"{corr:.3f}" if pd.notna(corr) else "Not available")
    st.subheader("4. Malaysia State Map: School Completion Rate")
    map_points(s_overall, "Completion Rate", "School completion rate by state", "Completion rate (%)")
    st.subheader("5. Grouped Bar Chart: Completion Rate by Sex")
    gender = s_state[s_state["Sex"].str.lower().isin(["male", "female"])]
    if gender.empty:
        st.warning("Male/Female categories were not detected. Check the Sex column values.")
    else:
        fig = px.bar(gender, x="State", y="Completion Rate", color="Sex", barmode="group",
                     labels={"Completion Rate":"Completion rate (%)"})
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    st.subheader("6. Scatter Plot with Regression Line: Mean Income vs Completion Rate")
    fig = px.scatter(merged, x="Mean Income", y="Completion Rate", hover_name="State", trendline="ols",
                     labels={"Mean Income":"Mean household income (RM)", "Completion Rate":"Completion rate (%)"})
    st.plotly_chart(fig, use_container_width=True)
    st.write(f"**Interpretation guide:** The Pearson correlation is {corr:.3f}. Describe the direction and strength of the association, and use the grouped bar chart to discuss differences between male and female completion rates.")

else:
    st.header("Objective 3")
    st.write("To analyze the relationship between annual live births and school completion rates.")
    a,c = st.columns(2)
    a.metric("Average live births", f'{merged["Live Births"].mean():,.0f}')
    c.metric("Average completion rate", f'{merged["Completion Rate"].mean():.2f}%')
    corr = merged["Live Births"].corr(merged["Completion Rate"])
    st.metric("Pearson correlation", f"{corr:.3f}" if pd.notna(corr) else "Not available")
    st.subheader("7. Scatter Plot: Live Births vs Completion Rate")
    fig = px.scatter(merged, x="Live Births", y="Completion Rate", hover_name="State", trendline="ols",
                     labels={"Live Births":"Annual live births", "Completion Rate":"Completion rate (%)"})
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("8. Line Chart: Live Births and Completion Rate by State")
    # Normalise both variables to a common 0-100 scale for a meaningful visual comparison
    line_df = merged[["State", "Live Births", "Completion Rate"]].copy()
    for col in ["Live Births", "Completion Rate"]:
        lo, hi = line_df[col].min(), line_df[col].max()
        line_df[col + " (index)"] = 100 * (line_df[col] - lo) / (hi - lo) if hi != lo else 0
    line_long = line_df.melt(id_vars="State", value_vars=["Live Births (index)", "Completion Rate (index)"],
                             var_name="Measure", value_name="Indexed value (0-100)")
    fig = px.line(line_long, x="State", y="Indexed value (0-100)", color="Measure", markers=True)
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Both variables are min-max indexed to 0–100 because they use different units. The index compares relative patterns, not actual values.")
    st.subheader("9. Grouped Bar Chart: Live Births and Completion Rate by State")
    # Separate panels preserve the original units and avoid misleading dual-axis comparisons
    fig = px.bar(merged, x="State", y=["Live Births", "Completion Rate"], barmode="group",
                 facet_col="variable", labels={"value":"Value", "variable":"Measure"})
    fig.update_layout(xaxis_tickangle=-45, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    st.write(f"**Interpretation guide:** The Pearson correlation is {corr:.3f}. Explain whether states with higher live births tend to have higher or lower completion rates. The line chart compares relative state patterns after indexing; the grouped comparison should be read with attention to the different units.")
