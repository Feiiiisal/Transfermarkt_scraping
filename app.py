# app.py

import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
from datetime import datetime
import logging

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("spotify_data_api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

# Database configuration using separate environment variables
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT', '5432')  # Default PostgreSQL port is 5432
DB_NAME = os.getenv('DB_NAME')

if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
    logger.error("Database configuration is incomplete. Please check your environment variables.")
    raise Exception("Database configuration is incomplete. Please check your environment variables.")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database and migration engine
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Define Models

class Artist(db.Model):
    __tablename__ = 'artists'
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    genres = db.Column(db.String)
    popularity = db.Column(db.Integer)
    followers = db.Column(db.Integer)
    uri = db.Column(db.String)

    albums = db.relationship('Album', backref='artist', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'genres': self.genres,
            'popularity': self.popularity,
            'followers': self.followers,
            'uri': self.uri
        }

class Album(db.Model):
    __tablename__ = 'albums'
    id = db.Column(db.String, primary_key=True)
    artist_id = db.Column(db.String, db.ForeignKey('artists.id'), nullable=False)
    name = db.Column(db.String, nullable=False)
    album_type = db.Column(db.String)
    release_date = db.Column(db.Date)
    release_date_precision = db.Column(db.String)
    total_tracks = db.Column(db.Integer)
    uri = db.Column(db.String)

    tracks = db.relationship('Track', backref='album', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'artist_id': self.artist_id,
            'name': self.name,
            'album_type': self.album_type,
            'release_date': self.release_date,
            'release_date_precision': self.release_date_precision,
            'total_tracks': self.total_tracks,
            'uri': self.uri
        }

class Track(db.Model):
    __tablename__ = 'tracks'
    id = db.Column(db.String, primary_key=True)
    album_id = db.Column(db.String, db.ForeignKey('albums.id'), nullable=False)
    name = db.Column(db.String, nullable=False)
    track_number = db.Column(db.Integer)
    duration_ms = db.Column(db.Integer)
    explicit = db.Column(db.Boolean)
    uri = db.Column(db.String)
    is_local = db.Column(db.Boolean)

    def to_dict(self):
        return {
            'id': self.id,
            'album_id': self.album_id,
            'name': self.name,
            'track_number': self.track_number,
            'duration_ms': self.duration_ms,
            'explicit': self.explicit,
            'uri': self.uri,
            'is_local': self.is_local
        }

# Routes

@app.route('/')
def index():
    return "Welcome to the Spotify Data API!"

# CRUD operations for Artists

@app.route('/artists', methods=['POST'])
def add_artist():
    data = request.get_json()
    if not data:
        logger.warning("No input data provided for adding artist.")
        return jsonify({"error": "No input data provided"}), 400

    try:
        artist = Artist(
            id=data.get('id'),
            name=data.get('name'),
            genres=data.get('genres'),
            popularity=data.get('popularity'),
            followers=data.get('followers'),
            uri=data.get('uri')
        )
        db.session.add(artist)
        db.session.commit()
        logger.info(f"Artist added successfully: {artist.name}")
        return jsonify({"message": "Artist added successfully"}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding artist: {e}")
        return jsonify({"error": str(e)}), 400

@app.route('/artists', methods=['GET'])
def get_artists():
    try:
        artists = Artist.query.all()
        output = [artist.to_dict() for artist in artists]
        logger.info("Fetched all artists successfully.")
        return jsonify(output), 200
    except Exception as e:
        logger.error(f"Error fetching artists: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/artists/<id>', methods=['GET'])
def get_artist(id):
    try:
        artist = Artist.query.get(id)
        if not artist:
            logger.warning(f"Artist not found: {id}")
            return jsonify({"error": "Artist not found"}), 404

        logger.info(f"Fetched artist: {artist.name}")
        return jsonify(artist.to_dict()), 200
    except Exception as e:
        logger.error(f"Error fetching artist {id}: {e}")
        return jsonify({"error": str(e)}), 500

# CRUD operations for Albums

@app.route('/albums', methods=['POST'])
def add_album():
    data = request.get_json()
    if not data:
        logger.warning("No input data provided for adding album.")
        return jsonify({"error": "No input data provided"}), 400

    try:
        release_date = parse_release_date(data.get('release_date'))
        album = Album(
            id=data.get('id'),
            artist_id=data.get('artist_id'),
            name=data.get('name'),
            album_type=data.get('album_type'),
            release_date=release_date,
            release_date_precision=data.get('release_date_precision'),
            total_tracks=data.get('total_tracks'),
            uri=data.get('uri')
        )
        db.session.add(album)
        db.session.commit()
        logger.info(f"Album added successfully: {album.name}")
        return jsonify({"message": "Album added successfully"}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding album: {e}")
        return jsonify({"error": str(e)}), 400

@app.route('/albums', methods=['GET'])
def get_albums():
    try:
        albums = Album.query.all()
        output = [album.to_dict() for album in albums]
        logger.info("Fetched all albums successfully.")
        return jsonify(output), 200
    except Exception as e:
        logger.error(f"Error fetching albums: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/albums/<id>', methods=['GET'])
def get_album(id):
    try:
        album = Album.query.get(id)
        if not album:
            logger.warning(f"Album not found: {id}")
            return jsonify({"error": "Album not found"}), 404

        logger.info(f"Fetched album: {album.name}")
        return jsonify(album.to_dict()), 200
    except Exception as e:
        logger.error(f"Error fetching album {id}: {e}")
        return jsonify({"error": str(e)}), 500

# CRUD operations for Tracks

@app.route('/tracks', methods=['POST'])
def add_track():
    data = request.get_json()
    if not data:
        logger.warning("No input data provided for adding track.")
        return jsonify({"error": "No input data provided"}), 400

    try:
        track = Track(
            id=data.get('id'),
            album_id=data.get('album_id'),
            name=data.get('name'),
            track_number=data.get('track_number'),
            duration_ms=data.get('duration_ms'),
            explicit=data.get('explicit'),
            uri=data.get('uri'),
            is_local=data.get('is_local')
        )
        db.session.add(track)
        db.session.commit()
        logger.info(f"Track added successfully: {track.name}")
        return jsonify({"message": "Track added successfully"}), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding track: {e}")
        return jsonify({"error": str(e)}), 400

@app.route('/tracks', methods=['GET'])
def get_tracks():
    try:
        tracks = Track.query.all()
        output = [track.to_dict() for track in tracks]
        logger.info("Fetched all tracks successfully.")
        return jsonify(output), 200
    except Exception as e:
        logger.error(f"Error fetching tracks: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/tracks/<id>', methods=['GET'])
def get_track(id):
    try:
        track = Track.query.get(id)
        if not track:
            logger.warning(f"Track not found: {id}")
            return jsonify({"error": "Track not found"}), 404

        logger.info(f"Fetched track: {track.name}")
        return jsonify(track.to_dict()), 200
    except Exception as e:
        logger.error(f"Error fetching track {id}: {e}")
        return jsonify({"error": str(e)}), 500

# Data Loading Endpoint (Removed CSV loading as per user request)
# If you still want to keep it for flexibility, you can modify it to accept JSON data instead.

# Utility Functions

def parse_release_date(date_str):
    try:
        if len(date_str) == 4:
            return datetime.strptime(date_str, "%Y").date()
        elif len(date_str) == 7:
            return datetime.strptime(date_str, "%Y-%m").date()
        elif len(date_str) == 10:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            return None
    except Exception as e:
        logger.error(f"Error parsing release date '{date_str}': {e}")
        return None

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
