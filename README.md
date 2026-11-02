# Scientific Visualisation Streamlit App

## Files required
Upload these three CSV files using the sidebar:
1. Annual live births: columns `state`, `date` (optional), `abs` or `live births`.
2. School completion: columns `state`, `sex`, `date` (optional), `completion` or `completion rate`; `stage` is optional.
3. Household income: columns `state`, `mean income` (optional `date`/`year`).

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Important
- `arts_faculty_data.csv` is not used for these objectives.
- The application uses the latest available year independently in each dataset. Check that reference years/stages are comparable before drawing conclusions.
- State-level maps use approximate state-centre coordinates (symbol map), not official administrative boundary polygons.
- Correlation is association, not causation.
