# 1. Base Image
FROM python:3.10-bookworm

# 2. Set up working directory and environment variables
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Install System Dependencies for ODBC (Final Method)
# This combined block handles dependencies, GPG keys, and EULA acceptance
RUN apt-get update && \
    apt-get install -y curl gnupg lsb-release && \
    mkdir -p /etc/apt/keyrings && \
    curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /etc/apt/keyrings/microsoft.gpg && \
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list && \
    # This is the most important part: run the install with the EULA variable
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 unixodbc-dev && \
    # Clean up to reduce final image size
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 4. Install Python Dependencies
COPY requirements2.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements2.txt

# 5. Copy the rest of the application code
COPY . .

# 6. Copy and set up the entrypoint script
COPY entrypoint.sh .
RUN chmod +x /app/entrypoint.sh

# 7. Expose the port Gunicorn will run on
EXPOSE 8000

# 8. Set the entrypoint script to run on container start
ENTRYPOINT ["/app/entrypoint.sh"]

# 9. Set the default command to start the Gunicorn server
CMD ["gunicorn", "simak.wsgi:application", "--bind", "0.0.0.0:8000", "--timeout", "300"]