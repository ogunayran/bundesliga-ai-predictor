# ⚽ Bundesliga Match Predictor

Advanced machine learning system for predicting German Bundesliga football match outcomes with 64.9% accuracy.

## 🎯 Features

- **Ensemble ML Model**: Gradient Boosting + Random Forest with 49+ features
- **Real-time Data**: Live scores and match data from OpenLigaDB API
- **Advanced Analytics**: xG (Expected Goals), form analysis, momentum tracking
- **Interactive Dashboard**: Modern web interface with live predictions
- **Poisson Score Prediction**: Statistical score forecasting
- **Power Rankings**: Team strength analysis based on multiple metrics

## 📊 Model Performance

- **Overall Accuracy**: 64.9%
- **Home Win Prediction**: 71% precision, 87% recall
- **Draw Prediction**: 51% precision, 47% recall
- **Away Win Prediction**: 64% precision, 46% recall

## 🏗️ Architecture

```
bundesliga-ai-predictor/
├── src/                    # Core prediction modules
│   ├── predictor.py       # Base ML predictor (Gradient Boosting + Random Forest)
│   ├── ensemble_predictor.py  # Ensemble model combining multiple predictors
│   ├── advanced_models.py # Poisson and advanced statistical models
│   ├── statistics.py      # Advanced statistics (xG, momentum, form)
│   ├── analyzer.py        # Match and team analysis
│   └── player_stats.py    # Player performance tracking
├── templates/             # Web interface templates
├── models/                # Trained ML models
├── data/                  # Match databases
├── server.py             # Web server
├── setup.py              # Database setup and data collection
└── requirements.txt      # Python dependencies
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/ogunayran/bundesliga-ai-predictor.git
cd bundesliga-ai-predictor

# Install dependencies
pip install -r requirements.txt

# Setup database and collect data
python setup.py

# Train the model (optional - pre-trained model included)
python -c "from src.predictor import BundesligaPredictor; p = BundesligaPredictor('data/bundesliga.db'); p.train_model(); p.save_model('models/bundesliga_model.pkl')"
```

### Run the Server

```bash
python server.py
```

Visit `http://localhost:8096` to see the predictions dashboard.

## 🤖 Model Features (49 Total)

### Performance Metrics (18 features)
- Win rates over last 3, 5, and 10 matches
- Goals scored/conceded averages
- Clean sheet percentages
- Home/away specific performance

### Form & Momentum (6 features)
- Recent form (last 3 matches)
- Performance trends (improving/declining)
- Form differential between teams
- Momentum indicators

### League Position (3 features)
- Current points
- Points differential
- League ranking

### Head-to-Head (4 features)
- Historical matchup results
- Average goals in H2H matches
- Win/draw/loss distribution

### Goal Statistics (12 features)
- Goal difference over multiple timeframes
- Scoring trends
- Defensive strength
- Attack efficiency

### Other (6 features)
- Home advantage factor
- Tactical matchup indicators
- Season progression effects

## 📈 API Endpoints

- `GET /` - Main dashboard
- `GET /api/predictions` - Current week predictions
- `GET /api/live-scores` - Live match scores
- `GET /api/standings` - League table
- `GET /api/power-rankings` - Team strength rankings
- `GET /api/top-scorers` - Goal scorers leaderboard

## 🔬 Technical Details

### Machine Learning Models

1. **Gradient Boosting Classifier**
   - 300 estimators
   - Learning rate: 0.05
   - Max depth: 5
   - Optimized for balanced classes

2. **Random Forest Classifier**
   - 300 estimators
   - Max depth: 10
   - Class weight balancing
   - Feature importance tracking

3. **Poisson Score Predictor**
   - Statistical score forecasting
   - Team-specific goal distributions
   - Historical performance weighting

### Data Sources

- **OpenLigaDB API**: Real-time Bundesliga data
- **Historical Matches**: 855+ matches (3 seasons: 2022-23, 2023-24, 2025-26)
- **Team Statistics**: Comprehensive performance metrics
- **Match Results**: Detailed score and event data

## 📝 Usage Examples

### Predict a Single Match

```python
from src.predictor import BundesligaPredictor

predictor = BundesligaPredictor('data/bundesliga.db')
predictor.load_model('models/bundesliga_model.pkl')

# Predict Bayern Munich vs Borussia Dortmund
prediction = predictor.predict_match(home_team_id=1, away_team_id=2)
print(f"Prediction: {prediction['prediction']}")
print(f"Confidence: {prediction['confidence']:.1%}")
print(f"Probabilities: {prediction['probabilities']}")
```

### Get Current Week Predictions

```python
from src.ensemble_predictor import BundesligaUltimatePredictor

predictor = BundesligaUltimatePredictor('data/bundesliga.db')
predictions = predictor.predict_upcoming_matches()

for match in predictions:
    print(f"{match['home_team']} vs {match['away_team']}")
    print(f"  Prediction: {match['prediction']} ({match['confidence']:.1%})")
    print(f"  Score: {match['predicted_score']}")
```

## 🎨 Web Interface

The web dashboard provides:
- **Live Predictions**: Current matchweek forecasts with confidence scores
- **Match Analysis**: Detailed breakdown of prediction factors
- **Team Statistics**: Performance metrics and trends
- **Historical Data**: Past predictions and accuracy tracking
- **Power Rankings**: Dynamic team strength ratings

## 🔧 Configuration

Edit `server.py` to customize:
- Port number (default: 8096)
- API refresh intervals
- Model parameters
- Feature weights

## 📊 Model Accuracy Breakdown

| Outcome | Precision | Recall | F1-Score | Support |
|---------|-----------|--------|----------|---------|
| Home Win | 71% | 87% | 78% | 78 |
| Draw | 51% | 47% | 49% | 43 |
| Away Win | 64% | 46% | 53% | 50 |
| **Overall** | **65%** | **65%** | **64%** | **171** |

## 🚧 Future Improvements

To reach 80%+ accuracy:
- [ ] Add 5-10 seasons of historical data (2000+ matches)
- [ ] Integrate player injury data
- [ ] Include weather conditions
- [ ] Add referee statistics
- [ ] Track transfer window impacts
- [ ] Consider European competition fatigue

## 📄 License

This project is for educational purposes. Not intended for real betting use.

## 🤝 Contributing

Contributions welcome! Please feel free to submit issues and pull requests.

## 📧 Contact

For questions or collaboration: [GitHub Issues](https://github.com/ogunayran/bundesliga-ai-predictor/issues)

---

**Note**: Football match prediction is inherently uncertain. This model provides statistical probabilities based on historical data and should not be used as the sole basis for betting decisions.
