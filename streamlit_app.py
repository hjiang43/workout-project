import streamlit as st

login = st.Page("login_auth.py", title = "Login", default = True)
workout = st.Page("workout.py", title= "workout", )

pg = st.navigation([login, workout])
st.set_page_config(page_title="Document", page_icon=":material/edit:")
pg.run()