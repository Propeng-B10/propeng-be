# official Python image
FROM python:3.10

WORKDIR /app

# Copy project files into the container
COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements2.txt

EXPOSE 8000

# Run migrations, collect static files, create superuser, and start Django
CMD ["sh", "-c", "\
    python manage.py collectstatic --noinput && \
    python manage.py migrate && \
    python manage.py shell -c \"\
        from django.contrib.auth import get_user_model; \
        User = get_user_model(); \
        User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists() or \
        User.objects.create_superuser('$DJANGO_SUPERUSER_USERNAME', '$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD')\" && \
    python manage.py runserver 0.0.0.0:8000"]




    