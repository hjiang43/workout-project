import streamlit as st

workout = st.Page("workout.py", title= "workout")
analysis = st.Page("analysis.py", title= "analysis")

pg = st.navigation([workout, analysis])
st.set_page_config(page_title="Document", page_icon=":material/edit:")
pg.run()