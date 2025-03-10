FROM python:3.10

WORKDIR /app

# Salin hanya requirements.txt terlebih dahulu untuk caching yang lebih efisien
COPY requirements.txt /app/

RUN pip install -r requirements.txt

# Salin seluruh proyek setelah dependencies terinstall
COPY . /app/

# Pindah ke direktori Django yang berisi manage.py
WORKDIR /app/propeng-be

RUN python manage.py migrate

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
