import json
import asyncio
import requests
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache
from datetime import datetime

BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-rapidapi-key": "5a66037bbb5dbd160f1d96d29a3b4214",
    "x-rapidapi-host": "v3.football.api-sports.io"
}


def fetch_matches(filter_by_live=False):
    """Fetch today's matches or live matches with Redis caching"""
    cache_key = 'live_matches' if filter_by_live else 'todays_matches'
    cached_data = cache.get(cache_key)
    if cached_data:
        print("🚀 Using cached data from Redis")
        return cached_data

    if filter_by_live:
        url = f"{BASE_URL}/fixtures?live=all"
    else:
        today = datetime.now().strftime("%Y-%m-%d")
        url = f"{BASE_URL}/fixtures?date={today}"

    response = requests.get(url, headers=HEADERS)
    data = response.json()

    print("📡 Fetching new data from API")
    cache.set(cache_key, data, timeout=300)
    return data


class LiveMatchConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("✅ WebSocket connected!")
        await self.accept()

        # Start sending data every 30 seconds
        self.send_task = asyncio.create_task(self.send_match_updates())

    async def disconnect(self, close_code):
        print("❌ WebSocket disconnected.")
        if hasattr(self, 'send_task'):
            self.send_task.cancel()

    async def send_match_updates(self):
        while True:
            # Fetch today's matches and live matches
            todays_matches = fetch_matches(filter_by_live=False)
            live_matches = fetch_matches(filter_by_live=True)

            todays_data = self.process_match_data(todays_matches)
            live_data = self.process_match_data(live_matches)

            await self.send(text_data=json.dumps({
                'todays_matches': todays_data,
                'live_matches': live_data
            }))

            await asyncio.sleep(30)  # Send updates every 30 seconds

    def process_match_data(self, matches_data):
        matches = []
        for match in matches_data.get('response', []):
            fixture = match['fixture']
            home = match['teams']['home']
            away = match['teams']['away']
            goals = match['goals']
            status = fixture['status']

            match_data = {
                'home_team': home['name'],
                'away_team': away['name'],
                'home_goals': goals['home'],
                'away_goals': goals['away'],
                'status': status['long'],
                'elapsed_time': status.get('elapsed'),
                'date': fixture['date'][:10],
                'venue': fixture['venue']['name'] if fixture['venue'] else None,
                'competition': match['league']['name']
            }
            matches.append(match_data)
        return matches
