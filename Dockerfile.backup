# Use an official Python 3.12 runtime as the base image
FROM python:3.12-slim

# Set environment variables to ensure that Python prints directly to terminal
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=main

# Set the working directory for the Python app
WORKDIR /usr/src/app

# Install dependencies for `nvm` and `Node.js`
RUN apt-get update && \
    apt-get install -y curl gnupg build-essential && \
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.4/install.sh | bash && \
    export NVM_DIR="$HOME/.nvm" && \
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" && \
    nvm install --lts && \
    nvm use --lts

# Copy the requirements.txt for Flask dependencies
COPY requirements.txt .

# Install Flask and other Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Install frontend dependencies (node_modules)
WORKDIR /usr/src/app/static
RUN export NVM_DIR="$HOME/.nvm" && \
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" && \
    npm install

# Set working directory back to the project root for running Flask
WORKDIR /usr/src/app

# Expose port 5000 for Flask
EXPOSE 5000

# Run the Flask server
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
