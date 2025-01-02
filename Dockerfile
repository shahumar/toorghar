# Use the official Python 3.11 image as a base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt to the working directory
COPY requirements.txt .

# Install dependencies from the requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire Django project into the container's working directory
COPY . .

RUN python manage.py collectstatic --noinput

# Expose the port that the Django app will run on
EXPOSE 8000

# Set environment variables (optional but recommended)
ENV PYTHONUNBUFFERED 1

# Run the Django development server (or you can use gunicorn for production)
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
