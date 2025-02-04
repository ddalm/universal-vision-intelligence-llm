import cv2
import requests
import base64
import os
import time
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Variables and configurations
API_URL = "https://openrouter.ai/api/v1/chat/completions"
POSTMARK_API_URL = "https://api.postmarkapp.com/email"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
POSTMARK_SERVER_TOKEN = os.getenv("POSTMARK_SERVER_TOKEN")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")
VISION_MODEL = "meta-llama/llama-3.2-11b-vision-instruct:free"
SUMMARY_MODEL = "deepseek/deepseek-r1-distill-llama-70b:free"
PROMPT = "Describe this frame in detail. Be concise and focus on the main elements."
SUMMARY_PROMPT = "Generate a concise summary of the evolution of events that happen across this list of frame descriptions. Focus on the main elements and the evolution of events and what subjects do:"

# File paths
REAL_TIME_FILE = "real_time_stream.json"
MINUTE_REPORT_FILE = "minute_report.json"
HOURLY_REPORT_FILE = "hourly_report.json"
DAILY_REPORT_FILE = "daily_report.json"

# Timing intervals (seconds)
MINUTE_INTERVAL = 60
HOUR_INTERVAL = 3600
DAY_INTERVAL = 86400

def initialize_json_file(file_path, initial_data=None):
    """Create JSON file with initial structure if it doesn't exist"""
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump(initial_data or [], f)

def append_to_json(file_path, data):
    """Append data to a JSON array file"""
    with open(file_path, 'r+') as f:
        try:
            file_data = json.load(f)
        except json.JSONDecodeError:
            file_data = []
        file_data.append(data)
        f.seek(0)
        json.dump(file_data, f, indent=2)

def flush_json_file(file_path):
    """Clear a JSON file while keeping array structure"""
    with open(file_path, 'w') as f:
        json.dump([], f, indent=2)

def generate_summary(source_file, report_file, model, time_window):
    """Generate summary using specified model and save to report file"""
    try:
        with open(source_file, 'r') as f:
            observations = json.load(f)
        
        if not observations:
            return

        summary_prompt = f"{SUMMARY_PROMPT}\n\n{json.dumps(observations, indent=2)}"
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://localhost:3000", #USE CORRECT ADDRESS IN DEPLOYMENT
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [{
                "role": "user",
                "content": [{"type": "text", "text": summary_prompt}]
            }]
        }

        response = requests.post(API_URL, json=payload, headers=headers)
        print("Summary API Response:", response.json())  # Print full response for debugging
        
        if response.status_code == 200:
            summary = response.json()['choices'][0]['message']['content']
            report_data = {
                "start_time": observations[0]['timestamp'],
                "end_time": observations[-1]['timestamp'],
                "summary": summary,
                "model_used": model,
                "time_window": time_window
            }
            
            append_to_json(report_file, report_data)
            flush_json_file(source_file)
            
    except Exception as e:
        print(f"Summary generation error: {e}")
        print("Full Response:", response.json())  # Print full response for debugging

def send_email(subject, html_body, recipient_email):
    """Send an email using Postmark's REST API"""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Postmark-Server-Token": POSTMARK_SERVER_TOKEN
    }

    payload = {
        "From": SENDER_EMAIL,
        "To": recipient_email,
        "Subject": subject,
        "HtmlBody": html_body,
        "MessageStream": "script-llm-summary"
    }

    response = requests.post(POSTMARK_API_URL, json=payload, headers=headers)
    
    if response.status_code == 200:
        print("Email sent successfully.")
    else:
        print(f"Error sending email: {response.status_code} - {response.text}")

def capture_and_describe():
    # Initialize JSON files
    initialize_json_file(REAL_TIME_FILE, [])
    initialize_json_file(MINUTE_REPORT_FILE, [])
    initialize_json_file(HOURLY_REPORT_FILE, [])
    initialize_json_file(DAILY_REPORT_FILE, [])

    # Initialize webcam
    cap = cv2.VideoCapture(1) #please make sure to select correct camera index, usually integrated cameras are 0 or 1 depending on system
    if not cap.isOpened():
        print("Error: Could not open webcam. Check permissions or webcam index.")
        return

    # Timing variables
    last_minute = time.time()
    last_hour = time.time()
    last_day = time.time()

    try:
        while True:
            # Capture frame
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture frame. Retrying...")
                time.sleep(1)
                continue

            # Process image
            _, buffer = cv2.imencode('.jpg', frame)
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')
            data_url = f"data:image/jpeg;base64,{jpg_as_text}"

            # Get description from vision model
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://localhost:3000", #USE CORRECT ADDRESS IN DEPLOYMENT
                "Content-Type": "application/json"
            }

            payload = {
                "model": VISION_MODEL,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PROMPT},
                        {"type": "image_url", "image_url": {"url": data_url}}
                    ]
                }]
            }

            try:
                response = requests.post(API_URL, json=payload, headers=headers)
                print("API Response:", response.json())  # Print full response for debugging
                if response.status_code == 200:
                    description = response.json()['choices'][0]['message']['content']
                    
                    # Store in real-time stream
                    observation = {
                        "timestamp": datetime.utcnow().isoformat(),
                        "description": description
                    }
                    append_to_json(REAL_TIME_FILE, observation)

                    # Display frame
                    display_frame = frame.copy()
                    y = 30
                    for line in description.split('\n'):
                        cv2.putText(display_frame, line, (10, y), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        y += 30
                    cv2.imshow('Webcam View', display_frame)

            except Exception as e:
                print(f"API Request Error: {e}")
                print("Full Response:", response.json())  # Print full response for debugging

            # Generate reports
            current_time = time.time()
            
            # Minute report
            if current_time - last_minute >= MINUTE_INTERVAL:
                generate_summary(REAL_TIME_FILE, MINUTE_REPORT_FILE, SUMMARY_MODEL, "minute")
                last_minute = current_time
                
            # Hourly report
            if current_time - last_hour >= HOUR_INTERVAL:
                generate_summary(MINUTE_REPORT_FILE, HOURLY_REPORT_FILE, SUMMARY_MODEL, "hour")
                last_hour = current_time
                
            # Daily report
            if current_time - last_day >= DAY_INTERVAL:
                generate_summary(HOURLY_REPORT_FILE, DAILY_REPORT_FILE, SUMMARY_MODEL, "day")
                
                # Read latest daily report
                with open(DAILY_REPORT_FILE, 'r') as f:
                    daily_reports = json.load(f)
                
                if daily_reports:
                    latest_summary = daily_reports[-1]
                    subject = f"Daily Summary Report - {latest_summary['start_time']} to {latest_summary['end_time']}"
                    
                    html_body = f"""
                    <html>
                    <body>
                        <h2>Daily Summary Report</h2>
                        <p><strong>Time Window:</strong> {latest_summary['time_window']}</p>
                        <p><strong>Start Time:</strong> {latest_summary['start_time']}</p>
                        <p><strong>End Time:</strong> {latest_summary['end_time']}</p>
                        <p><strong>Summary:</strong></p>
                        <blockquote>{latest_summary['summary']}</blockquote>
                    </body>
                    </html>
                    """

                    send_email(subject, html_body, RECIPIENT_EMAIL)
                
                last_day = current_time

            # Exit on 'q' pressing while camera stream is active focus, else stop with crl + c while focusing on terminal window
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            time.sleep(3)

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Final reports saved before exit")

if __name__ == "__main__":
    if not OPENROUTER_API_KEY:
        print("Error: Please set OPENROUTER_API_KEY environment variable")
    else:
        capture_and_describe()
