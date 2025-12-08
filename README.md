# Sentiment Analysis and Entity Recognition with Gemini 2.5 Flash

This Flask application leverages the power of the Gemini 2.5 Flash model to analyze the sentiment of text and identify entities within it. It provides a user-friendly interface for inputting text and receiving detailed analysis results.

## Features

- **Sentiment Analysis**: Accurately determines the sentiment of the input text, classifying it into categories such as very positive, positive, slightly positive, neutral, slightly negative, negative, and very negative.
- **Entity Recognition**: Identifies and extracts key entities from the text, such as names of people, locations, organizations, and products.
- **Automatic Labeling**: Automatically assigns relevant labels to the identified entities, such as "product quality (positive)", "service (negative)", etc.
- **Detailed Explanations**: Provides clear explanations for the assigned sentiment and labels, offering insights into the model's reasoning.
- **User-Friendly Interface**: Built with Flask, the application offers a simple and intuitive web interface for interacting with the model.
- **Error Handling**: Implements robust error handling to gracefully manage potential issues such as exceeding the character limit (1000 characters) or invalid model responses.
- **Sentry Integration**: Integrated with Sentry for error tracking and performance monitoring, ensuring application stability and reliability.

## Technologies Used

- **Python**: The primary programming language used for developing the application.
- **Flask**: A lightweight web framework for building the user interface and handling requests.
- **Vertex AI**: Google Cloud's machine learning platform, used for accessing the Gemini 2.5 Flash model.
- **Gemini 2.5 Flash**: A powerful generative AI model used for sentiment analysis and entity recognition.
- **Sentry**: An error tracking and performance monitoring tool.

## Prerequisites

Before running the application, ensure you have the following installed:

- Python 3.7 or higher
- Flask
- Vertex AI Python SDK
- Sentry SDK

You will also need a Google Cloud project with the Vertex AI API enabled and a Sentry account with a DSN configured.
