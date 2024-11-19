import streamlit as st
import requests
import googleapiclient.discovery
from openai import OpenAI
from typing import List, Dict
import pandas as pd

@st.cache_data
class Search_Result:
    def __init__(self, search_result) -> None:
        self.video_id = search_result['id']['videoId']
        self.title = search_result['snippet']['title']
        self.description = search_result['snippet']['description']
        self.thumbnails = search_result['snippet']['thumbnails']['default']['url']

class Search_Response:
    def __init__(self, search_response) -> None:
        self.prev_page_token = search_response.get('prevPageToken')
        self.next_page_token = search_response.get('nextPageToken')

        items = search_response.get('items')

        self.search_results = []
        for item in items:
            search_result = Search_Result(item)
            self.search_results.append(search_result)

def load_equipment_data():
    try:
        df = pd.read_csv('file/workout_equipments.csv')
        return df.to_dict('records')
    except Exception as e:
        st.error(f"Error loading equipment data: {str(e)}")
        return []

if "messages" not in st.session_state:
    st.session_state.messages = []

client = OpenAI(api_key=st.secrets["API_KEY"])
API_NINJAS_KEY = st.secrets["API_KEY_N"]
equipment_data = load_equipment_data()

youtube_api_key = st.secrets['YT_API_KEY']
if 'youtube_client' not in st.session_state:
    st.session_state.youtube_client = googleapiclient.discovery.build(
        serviceName = 'youtube',
        version = 'v3',
        developerKey= youtube_api_key)

def get_exercise_info(muscle: str) -> List[Dict]:
    """Fetch exercise information from API Ninjas."""
    url = "https://api.api-ninjas.com/v1/exercises"
    headers = {"X-Api-Key": API_NINJAS_KEY}
    params = {"muscle": muscle.lower()}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching exercise data: {str(e)}")
        return []

def get_available_equipment() -> List[str]:
    """Get list of available equipment from CSV."""
    return [item["Equipment Name"] for item in equipment_data]

def get_equipment_purpose(equipment_name: str) -> str:
    """Get purpose of specific equipment."""
    for item in equipment_data:
        if item["Equipment Name"].lower() == equipment_name.lower():
            return item["Purpose"]
    return "Purpose not found"

def search_yt(query, max_results = 3, page_token = None):
    yt_request = st.session_state.youtube_client.search().list(
        part = "snippet", # search by keyword
        maxResults = max_results, 
        pageToken = page_token,
        q = query,
        videoCaption = 'closedCaption', # Only including videos with caption. 
        type = 'video'
    )
    yt_response = yt_request.execute()
    search_response = Search_Response(yt_response)
    return search_response

def display_yt_results(search_response):
    for search_result in search_response.search_results:
        #st.write(f'Video ID: {search_result.video_id}')
        st.write(f'Title: {search_result.title}')
        st.write(f'Description: {search_result.description}')
        st.write(f'URL: https://www.youtube.com/watch?v={search_result.video_id}')

functions = [
    {
        "name": "recommend_equipment_exercises",
        "description": "Get exercise recommendations based on available equipment",
        "parameters": {
            "type": "object",
            "properties": {
                "equipment": {
                    "type": "string",
                    "description": "The exercise equipment to use",
                    "enum": get_available_equipment()
                },
                "muscle_group": {
                    "type": "string",
                    "description": "Target muscle group for the exercise"
                }
            },
            "required": ["equipment", "muscle_group"]
        }
    },
    {
        "name": "get_tips",
        "description": "Get best practices of creating a workout including exercises, sets, reps, reps, duration, frequency, etc."
    }
]

def generate_chat_response(messages: List[Dict], stream=True) -> str:
    """Generate response using OpenAI's API with streaming support."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            functions=functions,
            function_call="auto",
            max_tokens=500,
            temperature=0,
            stream=stream
        )
        
        if stream:
            placeholder = st.empty()
            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
            return full_response
        else:
            return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        return "I'm having trouble generating a response right now. Please try again."

def extract_muscle_group(text: str) -> str:
    """Extract muscle group from user input using OpenAI."""
    try:
        prompt = [
            {"role": "system", "content": "You are a fitness expert. Extract the muscle group from the following text. Reply with ONLY the muscle group name. If no muscle group is mentioned, reply with 'none'."},
            {"role": "user", "content": text}
        ]
        response = client.chat.completions.create(
            model="gpt-4",
            messages=prompt,
            max_tokens=50,
            temperature=0,
            stream=False
        )
        return response.choices[0].message.content.lower()
    except Exception:
        return "none"
    

best_practices= '''
    This guide provides a step-by-step approach to creating an effective workout plan tailored to your goals, whether you aim to lose weight, build muscle, or improve endurance. Here's a summary with key details:
    Step 1: Define Your Goals
    •	Weight Loss: Aim for a calorie deficit (0.5–1% of body weight per week).
    •	Muscle Gain: Aim for a calorie surplus (0.25–0.5% of body weight per week).
    •	Goals shape your workout and nutrition strategy.
    Step 2: Design Your Exercises
    •	Start simple with full-body workouts 2–3 times per week.
    •	Focus on compound movements (target multiple muscles at once) for efficiency:
    o	Quads: Squats, lunges.
    o	Hamstrings/Glutes: Deadlifts, hip raises.
    o	Push (Chest, Shoulders, Triceps): Push-ups, bench press.
    o	Pull (Back, Biceps): Pull-ups, rows.
    •	Add isolation exercises as you advance for targeted muscle development.
    Step 3: Sets and Reps
    •	Beginners: 2–5 sets, 5–15 reps per exercise.
    •	Guidelines:
    o	8–15 reps for fat burning and muscle building.
    o	5–10 reps for strength.
    •	Adjust weight if reps are too easy or too hard.
    •	Total workout: 10–20 sets (all exercises combined).
    Step 4: Rest Between Sets
    •	Rest based on intensity:
    o	Heavy lifting (1–3 reps): 3–5 minutes.
    o	Moderate weight (8–12 reps): 1–2 minutes.
    o	Endurance (13+ reps): Enough to maintain good form.
    Step 5: How Much Weight to Lift
    •	Start light and focus on proper form.
    •	Use the "2-for-2 rule": Increase weight if you can do 2 extra reps beyond your target.
    •	Beginners: Increase by 2–5 lbs (upper body) or 5–10 lbs (lower body).
    •	Advanced: Increase by 5–10 lbs (upper) or 10–15 lbs (lower).
    Step 6: Duration of Workout
    •	Aim for 45 minutes to 1 hour, including:
    o	Warm-up: 5–10 minutes (e.g., biking, jumping jacks).
    o	Exercise: 10–20 sets of total work.
    o	Cool-down/stretch: 5–10 minutes.
    •	Less time? Increase intensity.
    Step 7: Weekly Frequency
    •	2–3 full-body workouts per week for beginners.
    •	Allow 48 hours of recovery between workouts for muscle rebuilding.
    Key Tips
    1.	Consistency is crucial—choose a plan you can stick to.
    2.	Progressive overload: Aim to lift heavier or do more reps over time.
    3.	Combine strength training with proper nutrition for best results.
    4.	Stretch after workouts to improve flexibility and recovery.
'''

st.title("💪 WorkoutBot(Maybe some better name)")
st.write("Chat with me about exercises! I can help you find exercises for specific muscle groups and provide detailed instructions.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input("Ask me anything about exercises..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.write(prompt)


    # Initial message
    messages = [
                {"role": "system", "content": f"""You are a knowledgeable and friendly fitness instructor. 
                Keep responses concise and engaging."""},
                {"role": "user", "content": prompt},
            ]
    
    response = generate_chat_response(messages)

    # ------
    # determine if a tool has been called
    tool_calls = response.tool_calls
    #st.write(response_message) # test
    if tool_calls:
        # If true the model will return the name of the tool / function to call and the arguments
        tool_call_id = tool_calls[0].id
        tool_function_name = tool_calls[0].function.name

        if tool_function_name == 'get_tips':
            useful_info = best_practices
        else:
            st.write(f'Error: function {tool_function_name} does not exist')
    else:
        useful_info = ''
    # -----



    # This deletes the conversation history
    muscle_group = extract_muscle_group(prompt)

    if muscle_group != "none":
        exercises = get_exercise_info(muscle_group)
        if exercises:
            exercise_info = "\n".join([
                f"• {ex['name']}: {ex['instructions'][:100]}...\n Here are some videos:\n{display_yt_results(search_yt(ex))}" 
                for ex in exercises[:3]
            ])

            messages = [
                {"role": "system", "content": f"""You are a knowledgeable and friendly fitness instructor. 
                Available equipment: {', '.join(get_available_equipment())}. 
                Provide helpful, encouraging advice about exercises and suggest exercises using available equipment. 
                Keep responses concise and engaging.
                useful info: {useful_info}"""},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": f"I found some exercises for {muscle_group}. Here are the details:\n{exercise_info}"}
            ]
        else:
            messages = [
                {"role": "system", "content": f"""You are a knowledgeable and friendly fitness instructor.
                Available equipment: {', '.join(get_available_equipment())}.
                useful info: {useful_info}"""},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": f"While I couldn't find specific exercises for {muscle_group} in my database, I can provide general fitness advice based on our available equipment."}
            ]
    else:
        messages = [
            {"role": "system", "content": f"""You are a knowledgeable and friendly fitness instructor.
            Available equipment: {', '.join(get_available_equipment())}.
            useful info: {useful_info}"""},
            {"role": "user", "content": prompt}
        ]





    with st.chat_message("assistant"):
        response = generate_chat_response(messages)
        st.session_state.messages.append({"role": "assistant", "content": response})

with st.sidebar:
    st.header("💡 Tips")
    st.write("""
    - Ask for specific muscle groups like biceps, chest, or abs
    - Ask for exercise recommendations and instructions
    - Ask for exercise frequency and intensity
    """)
    
    st.header("🏋️‍♂️ Available Equipment")
    equipment_df = pd.DataFrame(equipment_data)
    st.dataframe(equipment_df, hide_index=True)