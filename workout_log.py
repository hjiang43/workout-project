import streamlit as st
import pandas as pd
from workout import ExerciseMemoryTracker
from datetime import datetime
import json
import os


def load_exercise_data(username):
    """
    Load and process exercise data directly from workout log history.
    
    Args:
        username (str): Username from session state.
    """
    try:
        log_file = f"file/workout_log_hist_{username}.json"

        with open(log_file, 'r') as f:
            memories = json.load(f)
        
        if not memories:
            return None

        df = pd.DataFrame(memories)

        df['date'] = pd.to_datetime(df['date'])

        required_columns = [
            'username', 'date', 'exercise_name', 'muscle_group', 
            'workout_type', 'difficulty', 
            'lbs/bw_reps for first set',
            'lbs/bw_reps for second set', 
            'lbs/bw_reps for third set'
        ]
        
        for col in required_columns:
            if col not in df.columns:
                df[col] = "NA"
                
        return df
        
    except FileNotFoundError:
        return None
    except Exception as e:
        st.error(f"Error loading workout data: {str(e)}")
        return None

def create_editable_log(df, username, muscle_list):
    """Create an editable workout log interface"""
    if df is None:
        return None

    if 'username' not in df.columns:
        df.insert(0, 'username', username)

    edited_df = st.data_editor(
        df,
        column_config={
            "muscle_group": st.column_config.SelectboxColumn(
                "Muscle Group",
                options=muscle_list,
                required=True
            ),
            "workout_type": st.column_config.SelectboxColumn(
                "Workout Type",
                options=['cardio', 'olympic_weightlifting', 'plyometrics', 
                        'powerlifting', 'strength', 'stretching', 'strongman'],
                required=True
            ),
            "difficulty": st.column_config.SelectboxColumn(
                "Difficulty",
                options=['beginner', 'intermediate', 'expert'],
                required=True
            ),
            "exercise_name": st.column_config.TextColumn(
                "Exercise Name",
                required=True
            ),
            "lbs/bw_reps for first set": st.column_config.TextColumn(
                "First Set (lbs/bw_reps)"
            ),
            "lbs/bw_reps for second set": st.column_config.TextColumn(
                "Second Set (lbs/bw_reps)"
            ),
            "lbs/bw_reps for third set": st.column_config.TextColumn(
                "Third Set (lbs/bw_reps)"
            )
        },
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True
    )
    
    return edited_df
    
if 'username' in st.session_state:
    username = st.session_state.username[0]
    df = load_exercise_data(username)
    st.title("Log Your Workouts Here")
    st.write("Today's Date: ", str(datetime.now().date()))

    muscle_list_df = pd.read_csv('file/muscle_list.csv')
    equipment_df = pd.read_csv('file/workout_equipments.csv')

    muscle_list = muscle_list_df['muscle'].tolist()
    equipment_list = equipment_df['Equipment Name'].tolist()

    if df is not None:
        df['date'] = df['date'].apply(lambda x: x.strftime('%Y-%m-%d'))
        df_today = df[df['date'] == str(datetime.now().date())]
        data_for_editor = df_today[['date', 'exercise_name', 'muscle_group', 'workout_type', 'difficulty']]
        username_column = [username] * len(data_for_editor)
        data_for_editor.insert(0, 'username', username_column)
        data_for_editor['lbs/bw_reps for first set'] = "NA"
        data_for_editor['lbs/bw_reps for second set'] = "NA"  
        data_for_editor['lbs/bw_reps for third set'] = "NA"  
        
        edited_df = st.data_editor(
            data_for_editor,
            column_config={
                "muscle_group": st.column_config.SelectboxColumn(
                    "Muscle Group",
                    options=muscle_list,
                    required=True
                ),
                "workout_type": st.column_config.SelectboxColumn(
                    "Workout Type",
                    options=['cardio', 'olympic_weightlifting', 'plyometrics', 'powerlifting', 'strength', 'stretching', 'strongman'],
                    required=True
                ),
                "difficulty": st.column_config.SelectboxColumn(
                    "Difficulty",
                    options=['beginner', 'intermediate', 'expert'],
                    required=True
                ),
                "exercise_name": st.column_config.TextColumn("Exercise Name")
            },
            use_container_width=True
        )

        save = st.button("Save Log", icon="💾")
        if save:
            os.makedirs('file', exist_ok=True)
            log_file = f"file/workout_log_hist_{username}.json"

            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    try:
                        memories = json.load(f)
                    except json.JSONDecodeError:
                        memories = []
            else:
                memories = []

            updated_data = edited_df.to_dict(orient='records')
            for record in updated_data:
                workout_hist = {
                    "username": record['username'],
                    "date": record['date'],
                    "exercise_name": record['exercise_name'],
                    "muscle_group": record['muscle_group'],
                    "workout_type": record['workout_type'],
                    "difficulty": record['difficulty'],
                    "lbs/bw_reps for first set": record['lbs/bw_reps for first set'],
                    "lbs/bw_reps for second set": record['lbs/bw_reps for second set'],
                    "lbs/bw_reps for third set": record['lbs/bw_reps for third set']
                }

                memories = [
                    memory for memory in memories
                    if not (
                        memory['exercise_name'] == workout_hist['exercise_name'] and
                        memory['date'] == workout_hist['date']
                    )
                ]
                memories.append(workout_hist)

            with open(log_file, 'w') as f:
                json.dump(memories, f, indent=2)
            st.success("Workout log successfully saved!")

    st.write("---")

    st.subheader("Add New Log")
    with st.form("add_log"):
        exercise_name = st.text_input("Exercise Name")
        muscle_group = st.selectbox("Muscle Group", options=muscle_list)
        workout_type = st.selectbox(
            "Workout Type", 
            options=['cardio', 'olympic_weightlifting', 'plyometrics', 'powerlifting', 'strength', 'stretching', 'strongman']
        )
        difficulty = st.selectbox("Difficulty", options=['beginner', 'intermediate', 'expert'])
        equipment_used = st.selectbox("Equipment Used", options=equipment_list)
        first_set = st.text_input("First Set (lbs/bw_reps)")
        second_set = st.text_input("Second Set (lbs/bw_reps)")
        third_set = st.text_input("Third Set (lbs/bw_reps)")

        submitted = st.form_submit_button("Add Log")
        if submitted:
            new_log = {
                "username": username,
                "date": str(datetime.now().date()),
                "exercise_name": exercise_name,
                "muscle_group": muscle_group,
                "workout_type": workout_type,
                "difficulty": difficulty,
                "equipment_used": equipment_used,
                "lbs/bw_reps for first set": first_set,
                "lbs/bw_reps for second set": second_set,
                "lbs/bw_reps for third set": third_set
            }
            log_file = f"file/workout_log_hist_{username}.json"
            os.makedirs('file', exist_ok=True)

            # Load existing logs and append
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    try:
                        memories = json.load(f)
                    except json.JSONDecodeError:
                        memories = []
            else:
                memories = []
            
            memories.append(new_log)
            with open(log_file, 'w') as f:
                json.dump(memories, f, indent=2)
            st.success("Log added successfully!")

    st.subheader("Delete Logs")
    if df is not None:
        delete_index = st.multiselect(
            "Select rows to delete:",
            options=edited_df.index.tolist(),
            format_func=lambda x: f"{edited_df.loc[x, 'exercise_name']} on {edited_df.loc[x, 'date']}"
        )

        if st.button("Delete Selected Logs"):
            log_file = f"file/workout_log_hist_{username}.json"
            with open(log_file, 'r') as f:
                memories = json.load(f)

            memories = [
                memory for memory in memories
                if not any(
                    edited_df.loc[i, 'exercise_name'] == memory['exercise_name'] and
                    edited_df.loc[i, 'date'] == memory['date']
                    for i in delete_index
                )
            ]

            with open(log_file, 'w') as f:
                json.dump(memories, f, indent=2)
            st.success("Selected logs deleted successfully!")
        
    if df is not None:
        st.divider()
        
        st.subheader("Edit Complete Workout History")
        st.write("Edit any previous workout entries in your log.")
        edited_df = create_editable_log(df, username, muscle_list)
        
        save_edits = st.button("Save All Changes", icon="💾", key="save_edits")
        if save_edits and edited_df is not None:
            os.makedirs('file', exist_ok=True)
            log_file = f"file/workout_log_hist_{username}.json"

            updated_data = edited_df.to_dict(orient='records')

            with open(log_file, 'w') as f:
                json.dump(updated_data, f, indent=2)
            st.success("Your workout history has been successfully updated!")
else:
    st.warning("Please login before recording your workouts.")
