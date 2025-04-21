from flask import Flask, render_template, request, redirect, url_for
import json

app = Flask(__name__)

# Загружаем данные о расписании из JSON-файла
def load_schedule():
    with open('schedule.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_schedule(schedule):
    with open('schedule.json', 'w', encoding='utf-8') as f:
        json.dump(schedule, f, ensure_ascii=False, indent=4)

schedule_data = load_schedule()

# Пример расписания звонков
bell_schedule = [
    {'lesson_number': 1, 'start_time': '08:00', 'end_time': '08:45'},
    {'lesson_number': 2, 'start_time': '08:55', 'end_time': '09:40'},
    {'lesson_number': 3, 'start_time': '09:50', 'end_time': '10:35'},
    {'lesson_number': 4, 'start_time': '10:45', 'end_time': '11:30'},
    {'lesson_number': 5, 'start_time': '11:40', 'end_time': '12:25'},
    {'lesson_number': 6, 'start_time': '12:35', 'end_time': '13:20'},
    {'lesson_number': 7, 'start_time': '13:30', 'end_time': '14:15'},
    {'lesson_number': 8, 'start_time': '14:25', 'end_time': '15:10'}
]

days_of_week = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/schedule/<parallel>')
def get_schedule(parallel):
    days = days_of_week
    parallel_classes = {class_name: lessons for class_name, lessons in schedule_data.items() if class_name.startswith(parallel)}
    return render_template('schedule.html', schedule=parallel_classes, days=days, bell_schedule=bell_schedule, parallel=parallel)

@app.route('/manage')
def manage():
    return render_template('manage.html', schedule=schedule_data, bell_schedule=bell_schedule, days_of_week=days_of_week)

@app.route('/add_class', methods=['POST'])
def add_class():
    new_class = request.form['class_name']
    if new_class and new_class not in schedule_data:
        schedule_data[new_class] = []
        save_schedule(schedule_data)
    return redirect(url_for('manage'))

@app.route('/add_schedule', methods=['POST'])
def add_schedule():
    class_name = request.form['class_name']
    day = request.form['day']
    subjects = request.form['subjects'].split('\n')
    lessons = [{'day': day, 'subject': subject.strip(), 'lesson_number': i + 1} for i, subject in enumerate(subjects)]
    if class_name in schedule_data:
        schedule_data[class_name].extend(lessons)
        save_schedule(schedule_data)
    return redirect(url_for('manage'))

@app.route('/edit_schedule', methods=['POST'])
def edit_schedule():
    class_name = request.form['class_name']
    day = request.form['day']
    lesson_index = int(request.form['lesson_index'])
    subject = request.form['subject']
    lesson_number = int(request.form['lesson_number'])
    if class_name in schedule_data and lesson_index < len(schedule_data[class_name]):
        schedule_data[class_name][lesson_index] = {'day': day, 'subject': subject, 'lesson_number': lesson_number}
        save_schedule(schedule_data)
    return redirect(url_for('manage'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=777,debug=True)
