import pyttsx3
import logging
from utilities import WeatherNews, SOSSystem

logger = logging.getLogger(__name__)

#hemke
class Announcer:
    def __init__(self, config):
        self.config = config
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        self.last_announcement = ""
        self.weather_news = WeatherNews(config)
        self.sos_system = SOSSystem()

    def announce_startup_info(self):
        """Announce startup information including weather and news."""
        weather_info = self.weather_news.get_weather()
        # You can specify the location you want to get news for
        #news_info = self.weather_news.get_news(location="Amaravathi", country="in")
        startup_message = f"{weather_info}. "#{news_info}"
        logger.info("Announcing startup information")
        self.announce(startup_message)

    def announce(self, text: str):
        if text != self.last_announcement:
            logger.info(f"Announcing: {text}")
            self.engine.say(text)
            self.engine.runAndWait()
            self.last_announcement = text

    def send_sos(self):
        result = self.sos_system.send_sos()
        self.announce(result)