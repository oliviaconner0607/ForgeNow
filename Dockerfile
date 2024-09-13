# Use the official Python image from the Docker Hub
FROM python:3.12

# Set the working directory in the container
WORKDIR /Desktop

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any dependencies specified in requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Ensure the application listens on port 8080
ENV PORT 8080

# Specify the command to run your app using gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8080", "FullMap:app", "--timeout", "120"]