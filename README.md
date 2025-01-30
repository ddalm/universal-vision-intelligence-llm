# Vision Intelligence from Camera Stream

This demo serves as the core building block for creating vision intelligence from a live video stream.

The project takes a camera stream and sends it to a large language model (LLM) which analyzes and describes the scene. Summarized reports are generated in JSON format every minute, hour, and day, detailing the events captured by the camera. A daily summary of the events is then sent via email.

## Features
- Stream video from a camera and analyze the scene using an LLM.
- Generate summarized reports in JSON format.
- Send daily event summaries via email.
- Easily adaptable to different use cases such as video surveillance, retail intelligence, shelf management, logistics, etc.
- Integrable with automated tasks and actions based on the insights generated.

#

## Installation

To install and set up the project, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/ddalm/universal-vision-intelligence-llm
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

This project relies on OpenRouter API with free models (please check availability) for easy and accessible replicability, but just as easily models can be hosted locally via Ollama or similar with minimal code change.
Postmark RESTful API is used to send summaries via e-mail just for demo purposes.

This script can be used and specifically adapted for videosurveillance, retail intelligence, shelf management, logistics, and much more with tailored outputs, as well actions and automations can be implemented accordingly to intelligence generated.

# Attention

+ Make sure the IDE or deployed service has access to the camera device, and that the correct camera source is selected.
+ Adjust the camera source index if necessary. By default, the script accesses the camera with index 1. Change the index accordingly based on your setup.

