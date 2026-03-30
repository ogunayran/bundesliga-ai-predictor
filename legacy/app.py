from flask import Flask, render_template, jsonify
import sqlite3
from datetime import datetime
import pandas as pd
from data_collector import SuperLigDataCollector
from predictor import SuperLigPredictor

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/predictions')
def get_predictions():
    try:
        predictor = SuperLigPredictor()
        predictions = predictor.get_current_predictions()
        return jsonify(predictions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/standings')
def get_standings():
    try:
        collector = SuperLigDataCollector()
        standings = collector.get_current_standings()
        return jsonify(standings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/matches')
def get_matches():
    try:
        collector = SuperLigDataCollector()
        matches = collector.get_upcoming_matches()
        return jsonify(matches)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
