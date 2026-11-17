import requests
import json
from datetime import datetime
from twilio.rest import Client
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import cv2
from collections import deque
from datetime import datetime, timedelta
import numpy as np
logger = logging.getLogger(__name__)


class WeatherNews:
    def __init__(self, config):
        self.weather_api_key = config.weather_api_key
        self.news_api_key = config.news_api_key
        self.weather_base_url = "http://api.weatherapi.com/v1/current.json"
        self.news_base_url = "https://newsapi.org/v2/top-headlines"



    def get_weather(self):  # Default city
        """Fetch current weather information from the WeatherAPI."""
        try:
            response = requests.get(f"http://api.weatherapi.com/v1/current.json?key={self.weather_api_key}&q=auto:ip")
            response.raise_for_status()  # Raise an error for bad responses
            data = response.json()
            location = "Vijayawada,Amaravathi"
            temperature = data['current']['temp_c']
            condition = data['current']['condition']['text']
            weather_info = f"Current weather in {location}: {temperature}°C, {condition}."
            logger.info("Weather info retrieved successfully.")
            return weather_info
        except Exception as e:
            logger.error(f"Failed to get weather information: {e}")
            return "Weather information is not available."

    def get_news(self, location="Amaravathi", country="in", num_headlines=3):
        try:
            # First attempt: Try to get location-specific news
            params = {
                'apiKey': self.news_api_key,
                'q': location,  # Add location as a search query
                'language': 'en',
                'pageSize': num_headlines,
                'sortBy': 'publishedAt'  # Get the latest news first
            }

            response = requests.get('https://newsapi.org/v2/everything', params=params)
            data = response.json()

            # If we find location-specific news, return it
            if 'articles' in data and data['articles']:
                headlines = [article['title'] for article in data['articles'][:num_headlines]]
                news_summary = f"Top headlines from {location}: " + ". ".join(headlines)
                logger.info("Location-specific news retrieved successfully.")
                return news_summary

            # Second attempt: If no location-specific news, fall back to regional news
            params = {
                'apiKey': self.ews_api_key,
                'country': country,
                'pageSize': num_headlines,
                'q': 'Andhra Pradesh'  # Add state-level search
            }

            response = requests.get(self.news_base_url, params=params)
            data = response.json()

            if 'articles' in data and data['articles']:
                headlines = [article['title'] for article in data['articles'][:num_headlines]]
                news_summary = f"Regional headlines (no specific {location} news found): " + ". ".join(headlines)
                logger.info("Regional news retrieved successfully.")
                return news_summary

            return f"No news headlines available for {location}"

        except Exception as e:
            logger.error(f"News API error: {e}")
            return "Unable to fetch news headlines"

class SOSSystem:
    def __init__(self):
        # Email configuration
        self.last_cleanup = datetime.now()
        self.email_username = 'nithinjambula89@gmail.com'
        self.email_password = 'njmr izng bzrm dkbo'
        self.emergency_contacts = [
            'nithinjambula44@gmail.com',
        ]
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587

        # Add missing attributes
        self.object_history = deque(maxlen=100)
        self.trigger_words = {
            "help", "emergency", "sos", "danger",
            "police", "ambulance", "medical", "accident"
        }

    def send_sos(self):
        try:
            location = self.get_location()
            if not location:
                return "Could not determine location"

            msg = MIMEMultipart('related')
            msg['Subject'] = 'EMERGENCY ALERT - SOS'
            msg['From'] = self.email_username
            
            html_content = self._create_html_content(location, list(self.object_history))
            msg.attach(MIMEText(html_content, 'html'))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_username, self.email_password)
                
                for recipient in self.emergency_contacts:
                    msg['To'] = recipient
                    server.send_message(msg)

            return f"Emergency alert sent successfully to: {', '.join(self.emergency_contacts)}"

        except Exception as e:
            logger.error(f"SOS error: {e}")
            return f"Failed to send emergency alert: {str(e)}"

    def get_location(self):
        try:
            response = requests.get('https://ipinfo.io')
            data = response.json()
            loc = data.get('loc', '').split(',')
            if len(loc) == 2:
                return {'latitude': loc[0], 'longitude': loc[1]}
            return None
        except Exception as e:
            logger.error(f"Location error: {e}")
            return None

    def _create_html_content(self, location, objects_data):
        """Create HTML email content with object details"""
        maps_link = f"https://www.google.com/maps?q={location['latitude']},{location['longitude']}"
        
        html = f"""
        <html>
        <body>
        <h2>EMERGENCY ALERT!</h2>
        <p>Location: <a href="{maps_link}">View on Maps</a></p>
        <h3>Recent Detected Objects:</h3>
        <table border="1">
            <tr>
                <th>Object</th>
                <th>Distance</th>
                <th>Time Detected</th>
                <th>Threat Level</th>
            </tr>
        """
        
        for obj in objects_data:
            html += f"""
            <tr>
                <td>{obj['object'].class_name}</td>
                <td>{obj['object'].distance:.1f}cm</td>
                <td>{obj['timestamp'].strftime('%H:%M:%S')}</td>
                <td>{getattr(obj['object'], 'threat_level', 'Unknown')}</td>
            </tr>
            """
        
        html += "</table></body></html>"
        return html

    def add_detected_object(self, obj, frame):
        """Store detected object with timestamp and frame"""
        current_time = datetime.now()
        self.object_history.append({
            'object': obj,
            'timestamp': current_time,
            'frame': frame
        })
        
        # Cleanup old objects
        if (current_time - self.last_cleanup) > timedelta(minutes=1):
            self._cleanup_old_objects()
            self.last_cleanup = current_time

    def _cleanup_old_objects(self):
        """Remove objects older than 1 minute"""
        current_time = datetime.now()
        self.object_history = deque(
            [item for item in self.object_history 
             if (current_time - item['timestamp']) <= timedelta(minutes=1)],
            maxlen=100
        )

    def handle_voice_command(self, command: str):
        """Handle voice commands and trigger SOS if needed"""
        command = command.lower().strip()
        if any(word in command for word in self.trigger_words):
            return self.send_sos()
        return None