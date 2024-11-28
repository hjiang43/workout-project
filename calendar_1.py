import streamlit as st
import streamlit_calendar as stc
from workout import ExerciseMemoryTracker
import pandas as pd

import streamlit.components.v1 as components

def render_fullcalendar(events):
    """
    Renders a FullCalendar calendar inside the Streamlit app using a custom HTML+JS component.
    
    Args:
    events: A list of event data (date, title, and description for muscle group).
    """
    html = f"""
    <html>
        <head>
            <!-- FullCalendar CSS -->
            <link href="https://cdn.jsdelivr.net/npm/fullcalendar@3.2.0/dist/fullcalendar.min.css" rel="stylesheet">
            <style>
                .fc-event {
                    'background-color': #007bff;
                    color: white;
                    border: none;
                }
                .fc-daygrid-event {
                    'cursor': pointer;
                }
            </style>
        </head>
        <body>
            <div id="calendar"></div>
            
            <!-- FullCalendar JS -->
            <script src="https://cdn.jsdelivr.net/npm/moment@2.24.0/moment.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/fullcalendar@3.2.0/dist/fullcalendar.min.js"></script>
            
            <script>
                // Prepare events data to be rendered
                var events = {events};

                // Initialize the FullCalendar
                $('#calendar').fullCalendar({
                    events: events,
                    eventClick: function(calEvent, jsEvent, view) {
                        alert('Event: ' + calEvent.title + '\\nMuscle Groups: ' + calEvent.description);
                    }
                });
            </script>
        </body>
    </html>
    """
    
    # Render HTML and JS code using Streamlit's custom component API
    components.html(html, height=600)


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

def on_date_select(selected_date):
    """Handle date selection and display the muscle group worked on that day"""
    selected_events = [event for event in events if event['date'] == selected_date]
    
    if selected_events:
        muscle_groups = ', '.join([event['muscle_group'] for event in selected_events])
        st.write(f"Muscle groups worked on {selected_date}: {muscle_groups}")
    else:
        st.write("No exercises recorded for this day.")

st.title("View your workouts in a calendar")

df = load_exercise_data()

st.write(df)

if df is not None:
    grouped = df.groupby(['date', 'muscle_group']).size().reset_index(name='count')
    events = [
        {'date': row['date'].strftime('%Y-%m-%d'), 'muscle_group': row['muscle_group']}
        for _, row in grouped.iterrows()
    ]
    st.write(events)

    render_fullcalendar(events)
    # Pass the events to the calendar component
    '''
    selected_date = stc.calendar(events=events, callbacks="dateClick")
    st.write(selected_date['dateClick']['date'][:10])
    st.write(events[2]['date'])
    if selected_date:
        selected_events = [event for event in events if event['date'] == selected_date['dateClick']['date'][:9]]
        
        if selected_events:
            muscle_groups = ', '.join([event['muscle_group'] for event in selected_events])
            st.write(f"Muscle groups worked on {selected_date}: {muscle_groups}")
        else:
            st.write("No exercises recorded for this day.")
    #stc.calendar(events=events, callbacks={"select": on_date_select})
    '''