# Use the official Python 3.9 image as the base
FROM python:3.14.0rc1-slim

# Set the working directory to /app
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY . .

# Expose port 8080 for the Flask application
EXPOSE 8080

# Define the command to run the Flask application
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "--timeout", "0", "app:app"]


