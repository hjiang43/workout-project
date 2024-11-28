import streamlit as st

login = st.Page("login_auth.py", title = "Login", default = True)
workout = st.Page("workout.py", title= "workout", )
analysis = st.Page("analysis.py", title= "analysis")
calendar = st.Page("calendar_1.py", title = "calendar")

pg = st.navigation([login, workout, analysis, calendar])
st.set_page_config(page_title="Document", page_icon=":material/edit:")
pg.run()