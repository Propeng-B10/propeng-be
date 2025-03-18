# Use official Python image
FROM python:3.10

# Set working directory in the container
WORKDIR /app

# Copy project files into the container
COPY . .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose the port Django runs on
EXPOSE 8000

# Set environment variables for Django superuser creation
ENV SECRET_KEY=bangabb
ENV DJANGO_SUPERUSER_USERNAME=admin
ENV DJANGO_SUPERUSER_EMAIL=admin@example.com
ENV DJANGO_SUPERUSER_PASSWORD=adminpassword

# Run migrations, update deployment timestamp, collect static files, and start Django server
CMD sh -c "
    python manage.py migrate && \
    python manage.py shell -c 'from simak.models import DeploymentInfo; DeploymentInfo.objects.all().delete(); DeploymentInfo.objects.create();' && \
    python manage.py collectstatic --noinput && \
    python manage.py shell -c 'from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username=\"admin\").exists() or User.objects.create_superuser(\"admin\", \"admin@example.com\", \"adminpassword\")' && \
    python manage.py runserver 0.0.0.0:8000
"