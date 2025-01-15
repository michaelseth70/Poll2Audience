import os
import uuid
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Database Configuration
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///my_audience_pulse.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ============================
# Models
# ============================
class Survey(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String, nullable=False)
    options = db.relationship('Option', backref='survey', lazy=True)

class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.String, db.ForeignKey('survey.id'), nullable=False)
    visible_text = db.Column(db.String, nullable=False)
    hyperlink = db.Column(db.String, nullable=False)
    response_count = db.Column(db.Integer, default=0)

class OptionSuggestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(255), unique=True, nullable=False)

# ============================
# Routes
# ============================
@app.route('/')
def home():
    return redirect(url_for('create_survey'))

@app.route('/create', methods=['GET', 'POST'])
def create_survey():
    suggestions = OptionSuggestion.query.with_entities(OptionSuggestion.text).all()

    if request.method == 'POST':
        title = request.form.get('title')
        custom_options = request.form.getlist('option_text')

        if not title:
            flash("Survey question is required.", "danger")
            return redirect(url_for('create_survey'))

        options = [opt.strip() for opt in custom_options if opt.strip()]
        if len(options) < 2:
            flash("You must define at least two options for your pulse.", "danger")
            return redirect(url_for('create_survey'))

        survey = Survey(title=title)
        db.session.add(survey)
        db.session.flush()

        for text in options:
            option = Option(survey_id=survey.id, visible_text=text, hyperlink="")
            db.session.add(option)
            db.session.flush()

            option.hyperlink = url_for('respond', survey_id=survey.id, option_id=option.id, _external=True)
            db.session.commit()

            if not OptionSuggestion.query.filter_by(text=text).first():
                db.session.add(OptionSuggestion(text=text))

        db.session.commit()

        # Redirect directly to the survey view page
        return redirect(url_for('view_survey', survey_id=survey.id))

    return render_template('create_survey.html', autocomplete_suggestions=[s[0] for s in suggestions])

@app.route('/survey/<survey_id>', methods=['GET'])
def view_survey(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    return render_template('view_survey.html', survey=survey)

@app.route('/respond/<survey_id>/<int:option_id>', methods=['POST'])
def respond(survey_id, option_id):
    option = Option.query.filter_by(survey_id=survey_id, id=option_id).first()
    if not option:
        return jsonify({"error": "Invalid option"}), 404

    option.response_count += 1
    db.session.commit()

    return jsonify({"new_count": option.response_count}), 200

# ============================
# Initialize Database
# ============================
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
