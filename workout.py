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

youtube_api_key = "AIzaSyAeNqdqHlm69Xso60E4aL2c9uKu3yKAcyM"
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
            temperature=0.7,
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

st.title("💪 WorkoutBot(Maybe some better name)")
st.write("Chat with me about exercises! I can help you find exercises for specific muscle groups and provide detailed instructions.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input("Ask me anything about exercises..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.write(prompt)

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
                Keep responses concise and engaging."""},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": f"I found some exercises for {muscle_group}. Here are the details:\n{exercise_info}"}
            ]
        else:
            messages = [
                {"role": "system", "content": f"""You are a knowledgeable and friendly fitness instructor.
                Available equipment: {', '.join(get_available_equipment())}."""},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": f"While I couldn't find specific exercises for {muscle_group} in my database, I can provide general fitness advice based on our available equipment."}
            ]
    else:
        messages = [
            {"role": "system", "content": f"""You are a knowledgeable and friendly fitness instructor.
            Available equipment: {', '.join(get_available_equipment())}."""},
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