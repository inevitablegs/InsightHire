# interviewers/utils.py
import os
from groq import Groq
import pdfplumber
import requests

def extract_text_from_pdf(pdf_file_path):
    try:
        with pdfplumber.open(pdf_file_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""  # Extract text from each page
            return text.strip()
    except Exception as e:
        return f"Error reading PDF file: {e}"

def generate_interview_questions(pdf_file_path):
    # Initialize the Groq client with API key
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    # Extract text from the PDF resume
    resume_content = extract_text_from_pdf(pdf_file_path)
    if resume_content.startswith("Error"):
        return resume_content  # Return error message if PDF reading fails

    # Template for generating interview questions
    template = (
        "You are an experienced interviewer tasked with generating well-structured and insightful interview questions based on the candidate's resume content: {resume_content}. "
        "Your questions should be relevant, professionally phrased, and reflect real-world interview standards.\n\n"

        "1. General Skills-Based Questions:\n"
        "   - Generate a total of **12 questions** assessing the candidate's general professional and soft skills.\n"
        "   - Categorize the questions as follows:\n"
        "     - **3 Easy** questions: Basic, introductory-level questions.\n"
        "     - **3 Medium** questions: More in-depth, practical application-based questions.\n"
        "     - **3 Hard** questions: Complex scenarios requiring problem-solving.\n"
        "     - **3 Extreme Hard** questions: Highly challenging, requiring deep critical thinking.\n\n"

        "2. Technical Skills-Based Questions:\n"
        "   - Generate a total of **12 questions** targeting the candidate’s expertise in programming languages, tools, frameworks, or technologies.\n"
        "   - Categorize the questions as follows:\n"
        "     - **3 Easy** questions: Basic theoretical or conceptual questions.\n"
        "     - **3 Medium** questions: Practical application or troubleshooting scenarios.\n"
        "     - **3 Hard** questions: Advanced, multi-step problem-solving questions.\n"
        "     - **3 Extreme Hard** questions: Expert-level questions involving optimization, architecture, or real-world challenges.\n\n"

        "3. Project-Based Questions:\n"
        "   - Generate a total of **12 questions** specifically about the projects mentioned in the resume.\n"
        "   - Focus on the candidate’s role, technologies used, key challenges, and solutions.\n"
        "   - Categorize the questions as follows:\n"
        "     - **3 Easy** questions: Basic inquiries about project details.\n"
        "     - **3 Medium** questions: Deeper discussions on implementation and impact.\n"
        "     - **3 Hard** questions: Critical problem-solving and technical choices.\n"
        "     - **3 Extreme Hard** questions: Strategic, high-level decision-making challenges.\n\n"

        "4. Behavioral Questions:\n"
        "   - Generate a total of **12 questions** focusing on the candidate’s experience, teamwork, leadership, and problem-solving skills.\n"
        "   - Categorize the questions as follows:\n"
        "     - **3 Easy** questions: Basic situational and self-reflective questions.\n"
        "     - **3 Medium** questions: More complex, experience-driven questions.\n"
        "     - **3 Hard** questions: Handling high-pressure situations and conflicts.\n"
        "     - **3 Extreme Hard** questions: Strategic leadership and ethical dilemma scenarios.\n\n"

        "5. Formatting Rules:\n"
        "   - Organize the questions into clearly labeled sections: 'General Skills Questions', 'Technical Questions', 'Project Questions', and 'Behavioral Questions'.\n"
        "   - Under each section, label the questions clearly by difficulty: 'Easy', 'Medium', 'Hard', and 'Extreme Hard'.\n"
        "   - Do not include any additional comments, explanations, or introductory text beyond the specified instructions.\n"
        "   - If the resume content is invalid or insufficient, return an empty string ('').\n"
        "   - make the test markdown friendly\n"
    )

    # Format the template with the resume content
    prompt = template.format(resume_content=resume_content)

    try:
        # Send request to the Groq API using the formatted prompt
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Groq model choice
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,  # Lower temperature for more focused questions
            max_tokens=4096,
            top_p=1,
            stream=True,
            stop=None,
        )

        # Collect streaming response progressively
        response_chunks = []
        for message in completion:
            chunk = message.choices[0].delta.content or ""
            response_chunks.append(chunk)  # Append each chunk to the list

        # Join all chunks into a complete response
        full_response = "".join(response_chunks)
        return full_response.strip()

    except Exception as e:
        return f"Error generating interview questions: {e}"
    




def schedule_meeting(topic, start_time, zoom_account_id, zoom_client_id, zoom_client_secret):
    # Get OAuth Token
    def get_zoom_access_token():
        url = "https://zoom.us/oauth/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = {
            "grant_type": "account_credentials",
            "account_id": zoom_account_id
        }
        auth = (zoom_client_id, zoom_client_secret)

        response = requests.post(url, headers=headers, data=payload, auth=auth)

        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print("Error getting access token:", response.text)
            return None

    # Schedule the meeting
    access_token = get_zoom_access_token()
    if not access_token:
        return None

    url = "https://api.zoom.us/v2/users/me/meetings"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "topic": topic,
        "type": 2,
        "start_time": start_time,
        "duration": 30,  # 30-minute meeting
        "timezone": "UTC",
        "settings": {
            "host_video": True,
            "participant_video": True,
            "mute_upon_entry": True,
            "waiting_room": False
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 201:
        return response.json()["join_url"]
    else:
        print("Error scheduling meeting:", response.text)
        return None
    




def transcribe_audio(audio_file_path):
    """Transcribes an audio file and analyzes the interview using LLaMA."""
    
    # Initialize Groq Client
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    # Step 1: Transcribe the Audio
    try:
        with open(audio_file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="distil-whisper-large-v3-en",
                file=audio_file,
                response_format="text"
            ).strip()
    except Exception as e:
        return f"Error transcribing audio: {e}"

    # Step 2: Analyze the Interview using LLaMA
    llama_prompt = f"""
You are an AI-powered interview evaluator assisting the interviewer in assessing a candidate's responses.  
The following is an automatically transcribed interview transcript, with raw and unprocessed text.  
Your task is to extract key insights, assess the quality of responses, and provide a structured evaluation based on the given criteria.
and also provide asked important question and candidate's answer. 

**Interview Transcript (raw):**  
{transcription}  

**Evaluation Criteria:**  
1. **Confidence & Delivery:** Assess whether the candidate speaks with confidence, assurance, and clarity. Explain why you believe they were (or were not) confident based on tone, hesitation, or assertiveness.  
2. **Relevance & Accuracy:** Evaluate whether the candidate’s responses align with the question. Provide reasons if their response was off-topic, partially correct, or completely accurate.  
3. **Coherence & Logical Flow:** Determine if the candidate’s thoughts are structured and make sense. Justify this based on their ability to present ideas sequentially and logically.  
4. **Overall Impression:** Provide a qualitative summary of the candidate’s performance, supported by specific examples from their responses.  
5. **Key Observations:** Highlight any notable strengths or weaknesses, explaining why they stood out.  

Please format your response in a detailed manner. Also, this is interviewer-tailored, so do not provide recommendations for the candidate.  

"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": llama_prompt}],
            temperature=0.7,
            max_tokens=4096
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating interview analysis: {e}"
