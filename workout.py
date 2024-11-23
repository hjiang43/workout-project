import streamlit as st
import requests
import googleapiclient.discovery
from openai import OpenAI
from typing import List, Dict
import pandas as pd

best_practices= '''
    This guide provides a step-by-step approach to creating an effective workout:
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

# Define Classes
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

@st.cache_data



# ----- Create Functions -----
def load_equipment_data():
    try:
        df = pd.read_csv('file/workout_equipments.csv')
        return df.to_dict('records')
    except Exception as e:
        st.error(f"Error loading equipment data: {str(e)}")
        return []

def get_exercise_info(muscle) -> List[Dict]:
    """Fetch exercise information from API Ninjas."""
    url = "https://api.api-ninjas.com/v1/exercises"
    headers = {"X-Api-Key": API_NINJAS_KEY}
    params = {"muscle": muscle.lower(), "difficulty":'intermediate'} # this should be a dropdown

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

# Load equipments data
equipment_data = load_equipment_data()
#print(equipment_data) # check

def search_yt(query, max_results = 1, page_token = None): # I changed max results
    yt_request = st.session_state.youtube_client.search().list(
        part = "snippet", # search by keyword
        maxResults = max_results, 
        pageToken = page_token,
        q = query + ' form', # I changed this

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

def get_yt_info(search_response):
    for search_result in search_response.search_results:
        result = f'Title: {search_result.title}. URL: https://www.youtube.com/watch?v={search_result.video_id}'
        return result
    

def chat_completion_request(messages,stream=True, tools=None, tool_choice=None, model='gpt-4o-mini'):
    try:
        response = client.chat.completions.create(
            model=model,
            messages = messages,
            tools=tools,
            tool_choice = tool_choice,
            stream = stream
            )
        return response
    except Exception as e:
        st.write("Unable to generate ChatCompletion response")
        st.write(f"Exception: {e}")
        return e


def extract_muscle_group(text: str) -> list:
    """Extract muscle group from user input using OpenAI."""
    try:
        prompt = [
            {"role": "system", "content": '''
            ONLY Assign one or more muscles groups. 
            The only possible muscles groups are: "abdominals, abductors, adductors, biceps, calves, chest, forearms, glutes, hamstrings, lats, lower_back, middle_back, neck, quadriceps, traps, triceps".
            Return the muscle groups separated by a space, for example: "biceps triceps" or "chest".
            If you cannot assign any muscle groups return nothing ''            
            '''},
            {"role": "user", "content": text}
        ]
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=prompt,
            temperature=0,
            stream=False
        )
        # Convert the space-separated string into a list
        muscle_groups = response.choices[0].message.content.lower().split()
        return [group for group in muscle_groups if group]  # Ensure no empty strings
    except Exception:
        return "none"


# ----- Define Tools -----
tools = [
    # {'type': 'function',
    #  'function':{
    #     "name": "recommend_equipment_exercises",
    #     "description": "Get exercise recommendations based on available equipment",
    #     "parameters": {
    #         "type": "object",
    #         "properties": {
    #             "equipment": {
    #                 "type": "string",
    #                 "description": "The exercise equipment to use",
    #                 "enum": get_available_equipment()
    #             },
    #             "muscle_group": {
    #                 "type": "string",
    #                 "description": "Target muscle group for the exercise"
    #             }
    #         },
    #         "required": ["equipment", "muscle_group"]
    #     }
    # }},
    {'type' : 'function',
     'function':{
        "name": "get_tips",
        "description": "Get best practices of creating a workout and exercising in general including exercises, sets, reps, duration, frequency, etc."
    }}
]


st.title("💪 WorkoutBot")
st.write("Chat with me about exercises! I can help you find exercises for specific muscle groups and provide detailed instructions.")

client = OpenAI(api_key=st.secrets["API_KEY"])
API_NINJAS_KEY = st.secrets["API_KEY_N"]

if "messages" not in st.session_state:
    st.session_state.messages = []


youtube_api_key = st.secrets['YT_API_KEY']
if 'youtube_client' not in st.session_state:
    st.session_state.youtube_client = googleapiclient.discovery.build(
        serviceName = 'youtube',
        version = 'v3',
        developerKey= youtube_api_key)



for msg in st.session_state.messages:
    st.chat_message(msg['role']).write(msg['content'])

if prompt := st.chat_input("Ask me anything about exercises..."):
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})


    # conversation history buffer (maybe later)
    messages_to_pass = st.session_state.messages.copy()

    system_message = {'role':'system',
                'content':\
                f"""
                You are a knowledgeable and friendly fitness instructor. 
                Keep responses concise and engaging.
                """}

    messages_to_pass.insert(0,system_message)

    # first llm call
    response = chat_completion_request(messages_to_pass, stream = False, tools = tools, tool_choice="auto")
    response_message = response.choices[0].message

    # Call tool if tools needds to be called
    tool_calls = response_message.tool_calls
    #st.write(tool_calls)
    if tool_calls:
        # If true the model will return the name of the tool / function to call and the arguments
        tool_call_id = tool_calls[0].id
        tool_function_name = tool_calls[0].function.name

        if tool_function_name == 'get_tips':
            tips_info = best_practices
        else:
            st.write(f'Error: function {tool_function_name} does not exist')
    else:
        tips_info = " "

    #st.write('tips info:'+tips_info) # test

    muscle_group_list = extract_muscle_group(prompt)
    st.write( muscle_group_list) # test

    # Get exercise information
    exercise_info = {}
    for muscle_group in muscle_group_list:
        exercises = get_exercise_info(muscle_group)
        #st.write(exercises)
        for ex in exercises[:3]:
            name = ex['name']
            difficulty = ex['difficulty']
            equipment = ex['equipment']
            #exercise_info[name]= f"difficulty: {difficulty}, equipment needed: {equipment}, Here are some instructional videos:\n{get_yt_info(search_yt(name))}"
            exercise_info[name]= f"difficulty: {difficulty}, equipment needed: {equipment}, type {ex['type']}, Here are some instructional videos:\n"
            #st.write(get_yt_info(search_yt(name))) # test


    system_message = {'role':'system',
                'content':\
                f"""
                You are a knowledgeable and friendly fitness instructor. 
                Keep responses concise and engaging.

                Available equipment: {', '.join(get_available_equipment())}. 
                useful tips to generate workouts: {tips_info}
                useful exercise info: {exercise_info}

                """}

    messages_to_pass.pop(0) # deleating the first SM
    messages_to_pass.insert(0,system_message)
    st.write(messages_to_pass)

    # Get stream response
    stream = chat_completion_request(messages_to_pass)

    # Write Stream
    with st.chat_message('assistant'):
        responses = st.write_stream(stream)
    # Append Messages.
    st.session_state.messages.append({'role':'assistant','content':responses})



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





# # Change logs
# - search_yt: I changed the max results to 1 and changed the query to + form
# - get_yt_info: to get the info from the videos, title and url as string
# - extract_muscle_group: now returns a list of muscle groups

# # things to talk about
# - Get available equipment function to tools
# - delete "recommend_equipment_exercises" from tools. it is not used
# - change functions to tool calls (extract muscle group, get exercise info)
# - Query the ninja API with other parameters like type or difficulty
# - Do the YT api call only for the final exercises, not for all of the ninja api ex. 
# - conversation history