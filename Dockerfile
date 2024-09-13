# Use an official Python 3.12 runtime as the base image
FROM python:3.12-slim

# Set environment variables to ensure that Python prints directly to terminal
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=main

# Set the working directory for the Python app
WORKDIR /usr/src/app

# Install dependencies for Node.js
RUN apt-get update && \
    apt-get install -y curl gnupg build-essential && \
    curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && \
    apt-get install -y nodejs

# Copy package.json and package-lock.json to the appropriate directory
COPY package.json package-lock.json /usr/src/app/

# Set working directory to where the package.json is located
WORKDIR /usr/src/app

# Install Node.js dependencies
RUN npm install

# Copy Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Expose port 5000 for Flask
EXPOSE 5000
