import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import altair as alt
import json
from openai import OpenAI

def get_ai_analysis(df):
    """
    Get AI analysis of workout history with time period consideration
    
    Args:
        df: pandas DataFrame containing workout data
    """
    try:
        client = OpenAI(api_key=st.secrets["API_KEY"])
        
        start_date = df['date'].min().strftime('%Y-%m-%d')
        end_date = df['date'].max().strftime('%Y-%m-%d')
        total_days = (df['date'].max() - df['date'].min()).days + 1
        total_workouts = len(df)
        days_active = df['date'].nunique()
        muscle_groups = df['muscle_group'].value_counts().to_dict()
        workout_types = df['workout_type'].value_counts().to_dict()
        difficulty_levels = df['difficulty'].value_counts().to_dict()
        
        prompt = f"""
        As a fitness expert, analyze the workout history from {start_date} to {end_date} ({total_days} days):
        - Total exercises performed: {total_workouts}
        - Active days: {days_active}
        - Muscle groups targeted (with frequency): {muscle_groups}
        - Types of workouts performed: {workout_types}
        - Difficulty levels: {difficulty_levels}

        Provide a brief analysis including:
        1. Overall consistency and commitment
        2. Balance of muscle groups (any imbalances?)
        3. Progression in difficulty over this time period
        4. Specific recommendations for improvement based on this time period
        Keep the analysis concise but specific to this user's data.
        Consider the time period when making your analysis - if it's a short period, focus on initial progress. 
        If it's longer, focus on trends and progression.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a knowledgeable fitness instructor analyzing workout data. While output report, address the user as you/your."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        analysis = response.choices[0].message.content
        period_context = f"\nAnalysis Period: {start_date} to {end_date} ({total_days} days)"
        
        return period_context + "\n\n" + analysis
        
    except Exception as e:
        return f"Unable to generate AI analysis: {str(e)}"

def load_workout_log(username, time_period='all'):
    """
    Load and process workout log history with time period filtering
    
    Args:
        username (str): Username to load data for
        time_period (str): 'all', '30d', or '7d' for filtering
    """
    log_file = f"file/workout_log_hist_{username}.json"
    try:
        with open(log_file, 'r') as f:
            memories = json.load(f)
            
        if not memories:
            st.warning("No workout data found. Start working out to see analysis!")
            return None
            
        df = pd.DataFrame(memories)
        df['date'] = pd.to_datetime(df['date'])
        
        # Filter based on time period
        if time_period != 'all':
            today = datetime.now()
            if time_period == '30d':
                cutoff_date = today - timedelta(days=30)
            elif time_period == '7d':
                cutoff_date = today - timedelta(days=7)
            df = df[df['date'] >= cutoff_date]
            
        return df
    except (FileNotFoundError, json.JSONDecodeError):
        st.warning("No workout data found. Start working out to see analysis!")
        return None

def create_progression_chart(df):
    """Create a line chart showing progression for specific exercises over time"""
    if df is None or df.empty:
        return None
        
    # Extract exercise names for selection
    exercise_list = sorted(df['exercise_name'].unique().tolist())
    selected_exercise = st.selectbox('Select Exercise to Track', exercise_list)
    
    # Filter data for selected exercise
    exercise_data = df[df['exercise_name'] == selected_exercise].copy()
    
    # Process the 'lbs/bw_reps' columns to extract numerical values
    def extract_weight(value):
        try:
            # Extract the first number from the string
            import re
            numbers = re.findall(r'\d+', str(value))
            return float(numbers[0]) if numbers else None
        except:
            return None
    
    # Process each set column
    for set_num in [1, 2, 3]:
        col_name = f'lbs/bw_reps for {["first", "second", "third"][set_num-1]} set'
        exercise_data[f'set_{set_num}_weight'] = exercise_data[col_name].apply(extract_weight)
    
    # Prepare data for visualization
    progression_data = pd.melt(
        exercise_data,
        id_vars=['date'],
        value_vars=['set_1_weight', 'set_2_weight', 'set_3_weight'],
        var_name='set',
        value_name='weight'
    )
    
    # Create multi-line chart
    chart = alt.Chart(progression_data).mark_line(point=True).encode(
        x=alt.X('date:T', 
                title='Date',
                axis=alt.Axis(format='%Y-%m-%d')),
        y=alt.Y('weight:Q', 
                title='Weight (lbs)'),
        color=alt.Color('set:N', 
                       title='Set Number',
                       scale=alt.Scale(scheme='category10')),
        tooltip=[
            alt.Tooltip('date:T', title='Date', format='%Y-%m-%d'),
            alt.Tooltip('set:N', title='Set'),
            alt.Tooltip('weight:Q', title='Weight (lbs)')
        ]
    ).properties(
        title=f'Weight Progression for {selected_exercise}',
        width=700,
        height=300
    ).configure_legend(
        orient='bottom'
    )
    
    return chart

def create_workout_type_chart(df):
    """Create a chart showing workout type distribution"""
    if df is None or df.empty:
        return None
        
    workout_counts = df['workout_type'].value_counts()
    
    chart = alt.Chart(workout_counts.reset_index()).mark_bar().encode(
        x=alt.X('workout_type:N', title='Workout Type'),
        y=alt.Y('count:Q', title='Number of Exercises'),
        color=alt.Color('workout_type:N', legend=None)
    ).properties(
        title='Workout Type Distribution'
    )
    
    return chart

def create_muscle_group_chart(df):
    """Create a chart showing muscle group distribution"""
    if df is None or df.empty:
        return None
        
    muscle_counts = df['muscle_group'].value_counts()
    
    chart = alt.Chart(muscle_counts.reset_index()).mark_bar().encode(
        x=alt.X('muscle_group:N', title='Muscle Group'),
        y=alt.Y('count:Q', title='Number of Exercises'),
        color=alt.Color('muscle_group:N', legend=None)
    ).properties(
        title='Muscle Group Distribution'
    )
    
    return chart

def create_daily_workout_count_chart(df):
    """Create a stacked area chart for daily workouts."""
    if df.empty:
        return None
    category = st.radio("Select Category", ["Workout Type", "Muscle Group", "Difficulty"])
    col = category.replace(" ", "_").lower()
    daily_counts = df.groupby(['date', col]).size().unstack(fill_value=0)
    daily_data = daily_counts.stack().reset_index()
    daily_data.columns = ['date', col, 'count']
    return alt.Chart(daily_data).mark_area().encode(
        x='date:T', y='count:Q', color=f'{col}:N'
    ).properties(title=f'Daily Count by {category}')

st.title("📊 Workout Analysis")
if 'username' in st.session_state:
    username = st.session_state.username[0]

    time_period = st.selectbox(
        "Select Time Period",
        options=['All Time', 'Last 30 Days', 'Last 7 Days'],
        key='time_period'
    )

    period_param = {
        'All Time': 'all',
        'Last 30 Days': '30d',
        'Last 7 Days': '7d'
    }[time_period]

    df = load_workout_log(username, period_param)

    if df is not None:
        # Add start date to header
        start_date = df['date'].min().strftime('%Y-%m-%d')
        st.write(f"Tracking since: {start_date}")
        # AI Analysis
        st.subheader("WorkoutBot Analysis")

        if st.button("Generate WorkoutBot Analysis"):
            with st.spinner("Analyzing your workout history..."):
                analysis = get_ai_analysis(df)
                st.markdown(analysis)
        
        st.divider()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Workouts", len(df))
        with col2:
            st.metric("Unique Exercises", df['exercise_name'].nunique())
        with col3:
            st.metric("Days Active", df['date'].nunique())
        

        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Workout Types")
            workout_chart = create_workout_type_chart(df)
            if workout_chart:
                st.altair_chart(workout_chart, use_container_width=True)
        
        with col2:
            st.subheader("Muscle Groups")
            muscle_chart = create_muscle_group_chart(df)
            if muscle_chart:
                st.altair_chart(muscle_chart, use_container_width=True)

        st.subheader("Daily Exercise Distribution")
        daily_stack_chart = create_daily_workout_count_chart(df)
        if daily_stack_chart:
            st.altair_chart(daily_stack_chart, use_container_width=True)

        st.subheader("Exercise Progression Tracking")
        st.write("Track your strength progression for specific exercises over time")
        progression_chart = create_progression_chart(df)
        if progression_chart:
            st.altair_chart(progression_chart, use_container_width=True)
            
        # exercise history
        st.subheader("Exercise History")
        
        # Search for details
        col1, col2, col3 = st.columns(3)
        with col1:
            workout_types = ['All'] + sorted(df['workout_type'].unique().tolist())
            selected_type = st.selectbox('Filter by Workout Type', workout_types)
        
        with col2:
            muscle_groups = ['All'] + sorted(df['muscle_group'].unique().tolist())
            selected_muscle = st.selectbox('Filter by Muscle Group', muscle_groups)
            
        with col3:
            difficulties = ['All'] + sorted(df['difficulty'].unique().tolist())
            selected_difficulty = st.selectbox('Filter by Difficulty', difficulties)
        
        # filters
        filtered_df = df.copy()
        if selected_type != 'All':
            filtered_df = filtered_df[filtered_df['workout_type'] == selected_type]
        if selected_muscle != 'All':
            filtered_df = filtered_df[filtered_df['muscle_group'] == selected_muscle]
        if selected_difficulty != 'All':
            filtered_df = filtered_df[filtered_df['difficulty'] == selected_difficulty]
        
        # filtered data
        display_columns = [
            'date', 'exercise_name', 'muscle_group', 'workout_type', 'difficulty',
            'lbs/bw_reps for first set', 'lbs/bw_reps for second set', 'lbs/bw_reps for third set'
        ]
        
        st.dataframe(
            filtered_df[display_columns].sort_values('date', ascending=False),
            hide_index=True
        )
        
        # Export your data
        if st.button('Export Exercise History'):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="exercise_history.csv",
                mime="text/csv"
            )
else:
    st.warning("Please Login to access your analysis")
