import streamlit as st
import pandas as pd
import webbrowser as wb
import os

def create_account(login, user_data):
    if login == 'Sign Up':
        user_account_info = {}
        user_account_info['firstname'] = st.text_input("Enter your first name")
        user_account_info['lastname'] = st.text_input("Enter your last name")
        user_account_info['email'] = st.text_input("Enter your email")
        user_account_info['username'] = st.text_input("Enter a unique Username")

        if user_account_info['username'] in user_data['username'].values:
            st.warning('Username already exists')
        else:
            user_account_info['password'] = st.text_input("Enter a password", type="password")
            create_account = st.button("Create Account")
            if create_account:
                if user_account_info['email'] in user_data['email'].values:
                    st.warning("There is an account with this email already")
                else:
                    user_account_df = pd.DataFrame([user_account_info])
                    user_data = pd.concat([user_data, user_account_df], index = False)
                    user_data.to_csv('User_Credentials.csv', index=False)
                    success = st.success("Your account has been successfully created. Please login to access your account")
    return success

def login_attempt(login, user_data):
    if login == 'Login':
        username = st.text_input("Enter your username")
        password = st.text_input("Enter your password", type='password')
        login_button = st.button("Login")
        account_reset = st.button("Change username/ password")
        if login_button:
            user_row = user_data[user_data['username'] == username]
            if not user_row.empty:
                if str(password) == str(user_row['password'].values[0]):
                    wb.open('https://workout-project-yvfw4gvl25.streamlit.app/', new = 0, autoraise=True)
            else:
                st.warning("Username and/or password is incorrect")
            
        elif account_reset:
            email = st.text_input("Enter your email to reset password")
            if email:
                user_row = user_data[user_data['email'] == email]
                if not user_row.empty:
                    username = user_row['username'].values[0]
                    st.write(f"Follow the steps to change your password for username {username}")
                    new_pass = st.text_input("Enter your new password", type="password")
                    new_pass_conf = st.text_input("Enter your new password again", type="password")
                    if new_pass_conf == new_pass:
                        st.write("Passwords match")
                        reset_pass_button = st.button("Reset Password")
                        if reset_pass_button:
                            user_data.loc[user_data['email'] == email, 'password'] = new_pass
                            user_data.to_csv('User_Credentials.csv', index=False)
                            st.success("Password reset successfully!")
                    else:
                        st.warning("Passwords do not match")
    return username

st.title("Welcome to the workout app")
st.header("Sign up to build workouts or Login to access your account")

login = st.selectbox("Login/ Sign Up", ['Select an option', 'Login', 'Sign Up'])

directory_path = "/workspaces/workout-project/"
csv_files = [file for file in os.listdir(directory_path) if file.endswith('.csv')]

if "User_Credentials.csv" in csv_files:
    user_data = pd.read_csv("User_Credentials.csv")
else:
    user_data = pd.DataFrame(columns=['firstname', 'lastname', 'email', 'username', 'password'])
    user_data.to_csv("User_Credentials.csv", index=False)

if login == 'Sign Up':
    create_account(login, user_data)
elif login == 'Login':
    user = login_attempt(login, user_data)
    if 'username' not in st.session_state:
        st.session_state.username = user
