# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Install system dependencies
# ffmpeg is required for yt-dlp to merge streams
# python3-tk is required for the folder dialog (though might not work in headless Docker without X11)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create the downloads directory
RUN mkdir -p downloads

# Make port 5000 available
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Run the application
CMD ["python", "app.py"]
