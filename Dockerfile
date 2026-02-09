# Gunakan Python Image yang ringan
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements dan install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy sisa project
COPY . .

# Expose port streamlit default
EXPOSE 8501

# Command untuk menjalankan aplikasi
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]