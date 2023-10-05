# Use the official Python image as the base image
FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Copy the client.py file to the working directory
COPY src/client.py /app/

# Install the required dependencies
RUN pip install aiortc opencv-python-headless numpy

# Expose the required port
EXPOSE 8080

# Run the client.py script when the container starts
CMD ["python", "src/client.py"]