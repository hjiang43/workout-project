import streamlit as st
import pandas as pd
from workout import ExerciseMemoryTracker
from datetime import datetime
import json
import os

def load_exercise_data(username):
    """
    Load and process exercise memory data for a specific user
    
    Args:
        username (str): Username from session state
    """
    memory_tracker = ExerciseMemoryTracker(username)
    
    # Get last xx days of exercise data, default is 30
    memories = memory_tracker.get_exercise_memories(days=30)
    if not memories:
        st.warning("No exercise data found. Start working out to see analysis!")
        return None
    
    df = pd.DataFrame(memories)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    return df

if 'username' in st.session_state:
    username = st.session_state.username[0]
    df = load_exercise_data(username)
    st.title("Log your workouts here")
    st.write("Today's Date: ", str(datetime.now().date()))

    if df is not None:
        df['date'] = df['date'].apply(lambda x: x.strftime('%Y-%m-%d'))
        df_today = df[df['date'] == str(datetime.now().date())]
        data_for_editor = df_today[['date', 'exercise_name', 'muscle_group', 'workout_type', 'difficulty']]
        username_column = [username] * len(data_for_editor)
        data_for_editor.insert(0, 'username', username_column)
        data_for_editor['lbs/bw_reps for first set'] = ""
        data_for_editor['lbs/bw_reps for second set'] = ""  
        data_for_editor['lbs/bw_reps for third set'] = ""  
        
        edited_df = st.data_editor(
            data_for_editor,
            column_config={
                "workout_type": st.column_config.SelectboxColumn(
                    "Workout Type",
                    options=['cardio', 'olympic_weightlifting', 'plyometrics', 'powerlifting', 'strength', 'stretching', 'strongman'],
                    required=True
                ),
                "difficulty": st.column_config.SelectboxColumn(
                    "Difficulty",
                    options=['beginner', 'intermediate', 'expert'],
                    required=True
                )
            },
            use_container_width=False
        )
        
        save = st.button(icon=":material/save:", label="Save")
        if save:
            os.makedirs('file', exist_ok=True)
            log_file = f"file/workout_log_hist_{username}.json"
            
            if not os.path.exists(log_file):
                memories = []
            else:
                with open(log_file, 'r') as f:
                    try:
                        memories = json.load(f)
                    except json.JSONDecodeError:
                        memories = []

            updated_data = edited_df.to_dict(orient='records')
        
            for record in updated_data:
                workout_hist = {
                    "username": record['username'],
                    "date": str(datetime.now().date()),
                    "exercise_name": record['exercise_name'],
                    "muscle_group": record['muscle_group'],
                    "workout_type": record['workout_type'],
                    "difficulty": record['difficulty'],
                    "lbs/bw_reps for first set": record['lbs/bw_reps for first set'],
                    "lbs/bw_reps for second set": record['lbs/bw_reps for second set'],
                    "lbs/bw_reps for third set": record['lbs/bw_reps for third set']
                }
                memories.append(workout_hist)

            with open(log_file, 'w') as f:
                json.dump(memories, f, indent=2)
            st.success("Workout successfully saved")

else:
    st.warning("Please login before recording your workouts")