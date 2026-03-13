FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py ./main.py
COPY forms.py ./forms.py
COPY kahvesiz_app ./kahvesiz_app
COPY templates ./templates
COPY static ./static
COPY instance ./instance

EXPOSE 5040

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5040", "main:app"]
