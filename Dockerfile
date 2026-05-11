# Gunakan Python 3.11 versi slim (Ubuntu-based)
FROM python:3.11-slim

# Install Tesseract dan library sistem yang dibutuhkan
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set folder kerja
WORKDIR /app

# Copy requirements dan install library Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy semua file bot ke dalam server
COPY . .

# Jalankan bot
CMD ["python", "main.py"]
