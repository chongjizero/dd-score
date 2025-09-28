# Dockerfile for NASDAQ 100 Drawdown Scripts with Web Dashboard

# Use a slim Python base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install required dependencies including cron and supervisor for multi-process
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir yfinance pandas numpy flask matplotlib

# Copy the scripts into the container
COPY initial_script.py /app/initial_script.py
COPY update_script.py /app/update_script.py
COPY app.py /app/app.py
COPY supervisord.conf /app/supervisord.conf
COPY templates/ /app/templates/

# Create a directory for data persistence
VOLUME /app/data

# Set environment variables for email (these can be overridden at runtime)
ENV SENDER_EMAIL=$SENDER_EMAIL
ENV SENDER_PASSWORD=$SENDER_PASSWORD
ENV RECEIVER_EMAIL=$RECEIVER_EMAIL
ENV TZ=Asia/Seoul

# Create cron job to run update_script.py daily at 9 AM (PATH 추가)
RUN echo "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" > /etc/cron.d/update_script_cron \
    && echo "0 9 * * * python /app/update_script.py >> /app/cron.log 2>&1" >> /etc/cron.d/update_script_cron \
    && chmod 0644 /etc/cron.d/update_script_cron \
    && crontab /etc/cron.d/update_script_cron

# Ensure cron logs are writable
RUN touch /app/cron.log && chmod 0666 /app/cron.log

# Create static folder for images
RUN mkdir -p /app/static/images

# Supervisor config for running cron and Flask together
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose Flask port
EXPOSE 5000

# Start supervisor (runs cron and Flask)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]