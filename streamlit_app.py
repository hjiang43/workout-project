import streamlit as st

workout = st.Page("workout.py", title= "workout")

pg = st.navigation([workout])
st.set_page_config(page_title="Document", page_icon=":material/edit:")
pg.run()