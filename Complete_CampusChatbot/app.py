from flask import Flask, render_template, request, redirect, url_for
import firebase_admin
from firebase_admin import credentials, firestore
import requests
import os

app = Flask(__name__)

# Firebase setup
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

if not os.path.exists('certificates'):
    os.makedirs('certificates')

def send_telegram_message(chat_id, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    requests.post(url, data=payload)

@app.route('/')
def home():
    events = [doc.to_dict() for doc in db.collection('events').stream()]
    scholarships = [doc.to_dict() for doc in db.collection('scholarships').stream()]
    certificates = [doc.to_dict() for doc in db.collection('certificates').stream()]
    schedules = [doc.to_dict() for doc in db.collection('schedules').stream()]
    return render_template('index.html', events=events, scholarships=scholarships, certificates=certificates, schedules=schedules)

@app.route('/register_event', methods=['POST'])
def register_event_web():
    student_id = request.form['student_id']
    event_id = request.form['event_id']
    db.collection('registrations').add({
        'student_id': student_id,
        'event_id': event_id,
        'status': 'registered',
        'certificate_generated': False
    })
    student_doc = db.collection('students').document(student_id).get()
    if student_doc.exists:
        chat_id = student_doc.to_dict().get('chat_id')
        send_telegram_message(chat_id, f"You are registered for event {event_id}!")
    return redirect(url_for('home'))

@app.route('/update_event', methods=['POST'])
def update_event():
    event_id = request.form['event_id']
    update_data = {
        'name': request.form.get('name'),
        'date': request.form.get('date'),
        'venue': request.form.get('venue'),
        'registration_link': request.form.get('registration_link')
    }
    db.collection('events').document(event_id).set(update_data)
    students = db.collection('students').stream()
    for student in students:
        chat_id = student.to_dict().get('chat_id')
        send_telegram_message(chat_id, f"Event {update_data['name']} updated!")
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
