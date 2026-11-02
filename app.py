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
