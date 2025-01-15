import os
import uuid
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify, session
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


@app.route('/respond/<survey_id>/<option_id>', methods=['POST'])
def respond(survey_id, option_id):
    survey = Survey.query.get(survey_id)
    if not survey:
        return jsonify({'error': 'Survey not found'}), 404

    # Initialize the session data for this survey if it doesn't exist
    if 'voted_surveys' not in session:
        session['voted_surveys'] = {}

    # Check if the user has already voted
    previous_option_id = session['voted_surveys'].get(survey_id)
    if previous_option_id:
        if previous_option_id == option_id:
            return jsonify({'error': 'already_voted'}), 400  # Already voted for this option
        else:
            # Transfer vote from previous option to the new one
            previous_option = Option.query.get(previous_option_id)
            if previous_option:
                previous_option.response_count -= 1

    # Register the new vote
    option = Option.query.get(option_id)
    if not option or option.survey_id != survey_id:
        return jsonify({'error': 'Invalid option'}), 400

    option.response_count += 1
    session['voted_surveys'][survey_id] = option_id  # Store the new vote in the session
    db.session.commit()

    return jsonify({'new_count': option.response_count})

# ============================
# Initialize Database
# ============================
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
