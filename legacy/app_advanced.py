from flask import Flask, render_template, jsonify, request
import sqlite3
from datetime import datetime
import pandas as pd
from advanced_predictor import AdvancedSuperLigPredictor
from betting_system import BettingRecommendationSystem
import os

app = Flask(__name__)

DB_PATH = '/Users/ogunayran/CascadeProjects/windsurf-project-6/superlig_full.db'
predictor = AdvancedSuperLigPredictor(DB_PATH)
betting_system = BettingRecommendationSystem(DB_PATH)

try:
    predictor.load_model('/Users/ogunayran/CascadeProjects/windsurf-project-6/superlig_model.pkl')
    print("Model loaded successfully!")
except:
    print("Model not found. Please train the model first by running: python advanced_predictor.py")

@app.route('/')
def index():
    return render_template('index_advanced.html')

@app.route('/api/predictions')
def get_predictions():
    try:
        predictions = predictor.predict_upcoming_matches()
        return jsonify(predictions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/safe-coupon')
def get_safe_coupon():
    try:
        coupon = betting_system.generate_safe_coupon()
        return jsonify(coupon)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/risky-coupon')
def get_risky_coupon():
    try:
        coupon = betting_system.generate_risky_coupon()
        return jsonify(coupon)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/daily-tips')
def get_daily_tips():
    try:
        date_str = request.args.get('date')
        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d')
        else:
            date = datetime.now()
        
        tips = betting_system.get_daily_tips(date)
        return jsonify(tips)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/team-analysis/<team_name>')
def get_team_analysis(team_name):
    try:
        analysis = betting_system.analyze_team_performance(team_name)
        if analysis:
            return jsonify(analysis)
        else:
            return jsonify({'error': 'Team not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/match-detail')
def get_match_detail():
    try:
        home_team = request.args.get('home_team')
        away_team = request.args.get('away_team')
        
        if not home_team or not away_team:
            return jsonify({'error': 'Missing team parameters'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM teams WHERE name LIKE ? OR normalized_name LIKE ?', 
                      (f'%{home_team}%', f'%{home_team.upper()}%'))
        home_result = cursor.fetchone()
        
        cursor.execute('SELECT id FROM teams WHERE name LIKE ? OR normalized_name LIKE ?', 
                      (f'%{away_team}%', f'%{away_team.upper()}%'))
        away_result = cursor.fetchone()
        
        conn.close()
        
        if not home_result or not away_result:
            return jsonify({'error': 'Team not found'}), 404
        
        home_team_id = home_result[0]
        away_team_id = away_result[0]
        
        recommendation = betting_system.get_betting_recommendation(home_team_id, away_team_id)
        
        return jsonify(recommendation)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM matches')
        total_matches = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM teams')
        total_teams = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT season) FROM matches')
        total_seasons = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT MIN(match_datetime), MAX(match_datetime) 
            FROM matches 
            WHERE match_datetime IS NOT NULL
        ''')
        date_range = cursor.fetchone()
        
        conn.close()
        
        return jsonify({
            'total_matches': total_matches,
            'total_teams': total_teams,
            'total_seasons': total_seasons,
            'date_range': {
                'start': date_range[0],
                'end': date_range[1]
            },
            'model_accuracy': predictor.model_accuracy if predictor.model else 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/teams')
def get_teams():
    try:
        conn = sqlite3.connect(DB_PATH)
        query = 'SELECT id, name FROM teams ORDER BY name'
        teams_df = pd.read_sql_query(query, conn)
        conn.close()
        
        return jsonify(teams_df.to_dict('records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
