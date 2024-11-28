import streamlit as st
import pandas as pd
from workout import ExerciseMemoryTracker
from datetime import datetime

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
    st.write("Today's Date: ", str(datetime.now().date()))

    if df is not None:
        df['date'] = df['date'].apply(lambda x: x.strftime('%Y-%m-%d'))
        df_today = df[df['date'] == str(datetime.now().date())]
        data_for_editor = df_today[['date', 'exercise_name', 'muscle_group']]
        username_column = ["sskashya"] * len(data_for_editor)
        data_for_editor.insert(0, 'username', username_column)
        data_for_editor['lbs for second set'] = ""  
        data_for_editor['lbs for third set'] = ""  
        
        edited_df = st.data_editor(data_for_editor, use_container_width=False)
else:
    st.warning("Please login before recording your workouts")