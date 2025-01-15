{% extends "base.html" %}

{% block content %}
<div class="row">
    <!-- Survey Title and Description Section -->
    <div class="col s12 m8 offset-m2">
        <div class="card teal lighten-5" style="margin-bottom: 30px; padding: 20px;">
            <h4 class="card-title" style="margin-bottom: 10px; text-align: center;">{{ survey.title }}</h4>
            <p style="font-size: 16px; color: #555; text-align: center;">
                {{ survey.description if survey.description else "Here's a quick poll for you. Please choose one of the options below." }}
            </p>
        </div>
    </div>

    <!-- Survey Options Section -->
    <div class="col s12 m8 offset-m2">
        <div class="card">
            <div class="card-content">
                <h5 style="margin-bottom: 20px; text-align: center;">Make Your Choice</h5>
                <div id="choices-container">
                    {% for option in survey.options %}
                    <button class="choice-button" data-option-id="{{ option.id }}">
                        <span>{{ option.visible_text }}</span>
                        <span class="choice-count" id="count-{{ option.id }}">{{ option.response_count }}</span>
                    </button>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
</div>

<script>
    document.addEventListener('DOMContentLoaded', () => {
        const choiceButtons = document.querySelectorAll('.choice-button');

        choiceButtons.forEach(button => {
            button.addEventListener('click', () => {
                const optionId = button.getAttribute('data-option-id');

                fetch(`/respond/{{ survey.id }}/${optionId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                })
                .then(response => {
                    if (response.ok) {
                        return response.json();
                    } else {
                        return response.json().then(err => { throw err });
                    }
                })
                .then(data => {
                    // Update the vote count in real-time
                    document.querySelectorAll('.choice-button').forEach(btn => {
                        const countElement = btn.querySelector('.choice-count');
                        countElement.textContent = btn.getAttribute('data-option-id') == optionId
                            ? data.new_count
                            : countElement.textContent;
                    });
                })
                .catch(error => {
                    if (error.error === 'already_voted') {
                        alert("You have already voted.");
                    } else {
                        console.error('Error:', error);
                        alert("An error occurred while submitting your vote.");
                    }
                });
            });
        });
    });
</script>

<style>
    body {
        background-color: #f4f4f9;
        font-family: 'Roboto', sans-serif;
        color: #333;
    }
    .card {
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
        border: 1px solid #ddd;
    }
    .card-title {
        font-size: 24px;
        font-weight: 600;
        margin-bottom: 20px;
        text-align: center;
        color: #00796b;
    }
    .choice-button {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #26a69a;
        color: white;
        border: none;
        padding: 12px 20px;
        margin-bottom: 10px;
        border-radius: 25px;
        font-size: 16px;
        font-weight: bold;
        cursor: pointer;
        transition: background-color 0.3s ease;
        width: 100%;
    }
    .choice-button:hover {
        background-color: #1e8e84;
    }
    .choice-count {
        background-color: #00796b;
        padding: 5px 10px;
        border-radius: 12px;
        font-size: 14px;
    }
</style>
{% endblock %}
