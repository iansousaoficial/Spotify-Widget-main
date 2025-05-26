from flask import Flask, request, redirect, jsonify
from flask_cors import CORS
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time

app = Flask(__name__)
CORS(app)

CLIENT_ID = '4c65b2f777f543eda5e2d448ad8c4e3f'
CLIENT_SECRET = 'aac5bc0105a64f16b78de9ba149729d8'
REDIRECT_URI = 'http://127.0.0.1:8888/callback'
SCOPE = 'user-read-currently-playing user-read-playback-state'

sp_oauth = SpotifyOAuth(client_id=CLIENT_ID,
                        client_secret=CLIENT_SECRET,
                        redirect_uri=REDIRECT_URI,
                        scope=SCOPE,
                        cache_path=".cache")

spotify = None

def get_spotify():
    """Retorna uma instância autenticada do Spotify, se possível."""
    global spotify
    if spotify:
        return spotify

    token_info = sp_oauth.get_cached_token()
    if token_info:
        spotify = spotipy.Spotify(auth=token_info["access_token"])
        return spotify
    return None

@app.route("/")
def index():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route("/callback")
def callback():
    global spotify
    code = request.args.get("code")
    token_info = sp_oauth.get_access_token(code)
    access_token = token_info["access_token"]
    spotify = spotipy.Spotify(auth=access_token)
    return "✅ Autenticado com sucesso! Pode fechar essa aba."

@app.route("/status")
def status():
    sp = get_spotify()
    if not sp:
        return jsonify({"error": "Não autenticado"}), 401

    try:
        current = sp.current_playback()
    except spotipy.exceptions.SpotifyException:
        return jsonify({"error": "Token expirado ou inválido"}), 401

    if current and current.get("item"):
        item = current["item"]
        duration_ms = item.get("duration_ms", 0)
        progress_ms = current.get("progress_ms", 0)
        is_playing = current.get("is_playing", False)
        timestamp = int(time.time() * 1000)

        return jsonify({
            "name": item["name"],
            "artist": ", ".join([a["name"] for a in item["artists"]]),
            "album": item["album"]["name"],
            "cover": item["album"]["images"][0]["url"],
            "is_playing": is_playing,
            "duration": duration_ms,
            "progress": progress_ms,
            "timestamp": timestamp
        })
    else:
        return jsonify({"name": None})

if __name__ == "__main__":
    app.run(port=8888)
