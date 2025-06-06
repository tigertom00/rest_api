# Use the official Python runtime image
FROM python:3.13  

# Create the app directory
RUN mkdir /app

# Set the working directory inside the container
WORKDIR /app

# Set environment variables 
# Prevents Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
#Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1 

# Upgrade pip
RUN pip install --upgrade pip 

# Copy the Django project  and install dependencies
COPY requirements.txt  /app/

# run this command to install all dependencies 
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Django project to the container
COPY . /app/

ENV SECRET_KEY=dummykey

RUN python manage.py collectstatic --noinput

# Expose the Django port
EXPOSE 8555

# Run Django’s development server
CMD ["gunicorn", "srv.wsgi:application", "--bind", "0.0.0.0:8555"]