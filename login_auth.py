import streamlit as st
import pandas as pd
import numpy as np
import webbrowser as wb
import os

def create_account_or_login(login, user_data):
    if login == 'Sign Up':
        user_account_info = {}
        user_account_info['firstname'] = st.text_input("Enter your first name")
        user_account_info['lastname'] = st.text_input("Enter your last name")
        user_account_info['email'] = st.text_input("Enter your email")
        user_account_info['username'] = st.text_input("Enter a unique Username")
        if user_data['username'].isna().any():
            if user_account_info['username'] in user_data['username'].values:
                st.warning('Username already exists')
            else:
                user_account_info['password'] = st.text_input("Enter a password", type = "password")
                create_account = st.button("Create Account")
                if create_account:
                    if user_account_info['email'] in user_data['email'].values and user_account_info['username'] in user_data['username'].values:
                        st.warning("There is an account with this email and username already")
                    else:
                        user_account_df = pd.DataFrame([user_account_info])
                        user_data = pd.concat([user_data,user_account_df], index = False)
                        st.write(user_data)
                        user_data.to_csv('User_Credentials.csv')
                        st.success("Your account has been successfully created. Please login to access your account")
        else: user_data['username'] = user_data['username']
    if login == 'Login':
        username = st.text_input("Enter your username")
        password = st.text_input("Enter your password", type = 'password')
        login_button = st.button("Login")
        account_reset = st.button("Change username/ password")
        user_data = pd.read_csv("User_Credentials.csv")
        if login_button:
            if password == user_data[user_data['username']==username]['password'].values:
                wb.open('https://workout-project-yvfw4gvl25.streamlit.app/')
            else:
                st.warning("Username and/or password is incorrect")
        elif account_reset:
            email = st.text_input("Enter your email")
            if email:
                username = user_data[user_data['email']==email]['username'].values
                reset_pass = st.write(f"Follow the steps to change your password for username {username}")
                if reset_pass:
                    new_pass = st.text_input("Enter your new password", type = "password")
                    new_pass_conf = st.text_input("Enter your new password again", type = "password")
                    if new_pass_conf == new_pass:
                        st.write("Passwords match")
                        reset_pass_button = st.button("Reset Password")
                        if reset_pass_button:
                            user_data.loc[email]['password'] = new_pass
                    else:
                        st.warning("Passwords do not match")

st.title("Welcome to the workout app")
st.header("Sign up to build workouts or Login to access your account")

login = st.selectbox("Login/ Sign Up", ['Select an option', 'Login', 'Sign Up'])

directory_path = "/workspaces/workout-project/"
csv_files = [file for file in os.listdir(directory_path) if file.endswith('.csv')]
#st.write(csv_files)
if csv_files:
    for file in csv_files:
        if file == "User_Credentials.csv":
            user_data = pd.read_csv("User_Credentials.csv")
            if 'Unnamed:0' in user_data.columns:
                user_data.drop(columns = 'Unnamed:0')
            create_account_or_login(login, user_data)
        else:
            user_df = pd.DataFrame(columns = ['firstname', 'lastname', 'email', 'username', 'password'])
            user_df.to_csv("User_Credentials.csv")
            user_data = pd.read_csv("User_Credentials.csv")
            if 'Unnamed:0' in user_data.columns:
                user_data.drop(columns = 'Unnamed:0')
            create_account_or_login(login, user_data)
else:
    user_df = pd.DataFrame(columns = ['firstname', 'lastname', 'email', 'username', 'password'])
    user_df.to_csv("User_Credentials.csv")
    user_data = pd.read_csv("User_Credentials.csv")
    if 'Unnamed:0' in user_data.columns:
        user_data.drop(columns = 'Unnamed:0')
    create_account_or_login(login, user_data)
