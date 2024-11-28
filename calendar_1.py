import streamlit as st
import streamlit_calendar as stc
from workout import ExerciseMemoryTracker
import pandas as pd
from datetime import datetime, timedelta
import streamlit.components.v1 as components
import json

def render_fullcalendar(events):
    """
    Renders a FullCalendar calendar inside the Streamlit app using a custom HTML+JS component.
    
    Args:
    events: A list of event data (date, title, and description for muscle group).
    """
    # Convert events to a JSON-like string format for embedding
    events_json = str(events).replace("'", '"')  # Use double quotes for JSON compatibility

    # HTML and JavaScript code to render FullCalendar
    html = f"""
    <html>
        <head>
            <!-- FullCalendar CSS -->
            <link href="https://cdn.jsdelivr.net/npm/fullcalendar@3.2.0/dist/fullcalendar.min.css" rel="stylesheet">
            <style>
                .fc-event {{
                    background-color: #007bff;
                    color: white;
                    border: none;
                }}
                .fc-daygrid-event {{
                    cursor: pointer;
                }}
                #calendar {{
                    max-width: 900px;
                    margin: 0 auto;
                    height: 600px;
                    background-color: #f5f5f5;  /* Added background color to identify calendar space */
                }}
            </style>
        </head>
        <body>
            <div id="calendar"></div>

            <!-- FullCalendar JS -->
            <script src="https://cdn.jsdelivr.net/npm/moment@2.24.0/moment.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/fullcalendar@3.2.0/dist/fullcalendar.min.js"></script>

            <script>
                // Debugging: Log event data to check if it's loaded correctly
                console.log("Events Data:", {events_json});
                
                // Prepare events data to be rendered
                var events = {events_json};

                // Initialize FullCalendar after a small delay to ensure the page is fully loaded
                setTimeout(function() {{
                    $('#calendar').fullCalendar({{
                        events: events,
                        eventClick: function(calEvent, jsEvent, view) {{
                            alert('Event: ' + calEvent.title + '\\nMuscle Groups: ' + calEvent.description);
                        }},
                        eventRender: function(event, element) {{
                            console.log('Rendered event:', event);
                        }},
                        dayClick: function(date, jsEvent, view) {{
                            console.log('Date clicked:', date.format());
                        }},
                        viewRender: function(view, element) {{
                            console.log('Calendar view rendered:', view);
                        }}
                    }});
                }}, 500);  // Delay initialization by 500 milliseconds
            </script>
        </body>
    </html>
    """
    
    # Render the HTML and JS code using Streamlit's custom component API
    components.html(html, height=700)

def get_exercise_memories(days=None, muscle_group=None, workout_type=None):
        """
        Retrieve exercise memories with optional filtering.
        
        Args:
            days (int, optional): Number of recent days to retrieve memories from
            muscle_group (str, optional): Filter by specific muscle group
            workout_type (str, optional): Filter by specific workout type
        
        Returns:
            list: Filtered list of exercise memories
        """
        with open(f"file/workout_log_hist_{st.session_state.username[0]}.json", 'r') as f:
            memories = json.load(f)
        
        filtered_memories = memories
        
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
            filtered_memories = [
                memory for memory in filtered_memories 
                if datetime.fromisoformat(memory['date']) >= cutoff_date
            ]
        
        if muscle_group:
            filtered_memories = [
                memory for memory in filtered_memories
                if memory.get('muscle_group', '').lower() == muscle_group.lower()
            ]
        
        if workout_type:
            filtered_memories = [
                memory for memory in filtered_memories
                if memory.get('workout_type', '').lower() == workout_type.lower()
            ]
        
        return filtered_memories

def load_exercise_data():
    """Load and process exercise memory data"""
    user_id = "default_user"  # We can expand this when we implement user authentication
    #memory_tracker = ExerciseMemoryTracker(user_id)
    
    memories = get_exercise_memories(days=30)
    if not memories:
        st.warning("No exercise data found. Start working out to see analysis!")
        return None
    
    df = pd.DataFrame(memories)
    #df['timestamp'] = pd.to_datetime(df['date'])
    #df['date'] = df['date'].dt.date
    return df

def on_date_select(selected_date):
    """Handle date selection and display the muscle group worked on that day"""
    selected_events = [event for event in events if event['date'] == selected_date]
    
    if selected_events:
        muscle_groups = ', '.join([event['muscle_group'] for event in selected_events])
        st.write(f"Muscle groups worked on {selected_date}: {muscle_groups}")
    else:
        st.write("No exercises recorded for this day.")

if 'username' in st.session_state.username:
    st.title("View your workouts in a calendar")

    df = load_exercise_data()

    if df is not None:
        grouped = df.groupby(['date', 'muscle_group']).size().reset_index(name='count')
        events = []
        for _, row in grouped.iterrows():
            events.append({
                'title': row['muscle_group'],
                'start': row['date'], #.strftime('%Y-%m-%d')
                'description': f"{row['muscle_group']}" 
            })

        selected_date = stc.calendar(events=events, callbacks="dateClick")
else:
    st.warning("Login to view your calendar")