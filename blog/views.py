import requests
from django.shortcuts import render

BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {
    "x-rapidapi-key": "5a66037bbb5dbd160f1d96d29a3b4214",
    "x-rapidapi-host": "v3.football.api-sports.io"
}

def fetch_live_matches():
    url = f"{BASE_URL}/matches"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return {"response": []}  # Return empty response in case of an error

def live_matches(request):
    data = fetch_live_matches()
    return render(request, 'blog/matches.html', {'matches': data['response']})
