import streamlit as st
import pandas as pd
from workout import ExerciseMemoryTracker
from datetime import datetime
import json
import os

def load_exercise_data():
    """Load and process exercise memory data"""
    user_id = "default_user"  # We can expand this when we implement user authentication
    memory_tracker = ExerciseMemoryTracker(user_id)
    
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
    df = load_exercise_data()
    st.title("Log your workouts here")
    st.write("Today's Date: ", str(datetime.now().date()))

    if df is not None:
        df['date'] = df['date'].apply(lambda x: x.strftime('%Y-%m-%d'))
        df_today = df[df['date'] == str(datetime.now().date())]
        data_for_editor = df_today[['date', 'exercise_name', 'muscle_group']]
        username_column = [st.session_state.username] * len(data_for_editor)
        data_for_editor.insert(0, 'username', username_column)
        data_for_editor['lbs/bw_reps for first set'] = ""
        data_for_editor['lbs/bw_reps for second set'] = ""  
        data_for_editor['lbs/bw_reps for third set'] = ""  
        
        edited_df = st.data_editor(data_for_editor, use_container_width=False)
        save = st.button(icon = ":material/save:", label = "Save")
        if save:
            os.makedirs('file', exist_ok=True)
            if not os.path.exists(f"file/workout_log_hist_{st.session_state.username[0]}.json"):
                memories = []
            else:
                with open(f"file/workout_log_hist_{st.session_state.username[0]}.json", 'r') as f:
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
                    "lbs/bw_reps for first set": record['lbs/bw_reps for first set'],
                    "lbs/bw_reps for second set": record['lbs/bw_reps for second set'],
                    "lbs/bw_reps for third set" : record['lbs/bw_reps for third set']
                }
                memories.append(workout_hist)

            with open(f"file/workout_log_hist_{st.session_state.username[0]}.json", 'w') as f:
                json.dump(memories, f, indent=2)
            st.success("Workout successfully saved")

else:
    st.warning("Please login before recording your workouts")