from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime
import threading
import time
from utils import load_schedule, save_schedule, load_changes, save_changes, schedule_revert
import logging
import qrcode
import os
app = Flask(__name__)
if not os.path.exists('static/qrcodes'):
    os.makedirs('static/qrcodes')
# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка данных расписания
schedule_data = load_schedule()

# Расписание звонков
bell_schedule = [
    {'lesson_number': 1, 'start_time': '08:00', 'end_time': '08:40'},
    {'lesson_number': 2, 'start_time': '08:50', 'end_time': '09:30'},
    {'lesson_number': 3, 'start_time': '09:40', 'end_time': '10:20'},
    {'lesson_number': 4, 'start_time': '10:35', 'end_time': '11:15'},
    {'lesson_number': 5, 'start_time': '11:30', 'end_time': '12:10'},
    {'lesson_number': 6, 'start_time': '12:25', 'end_time': '13:05'},
    {'lesson_number': 7, 'start_time': '13:20', 'end_time': '14:00'},
    {'lesson_number': 8, 'start_time': '14:15', 'end_time': '14:55'}
]
# Дни недели
days_of_week = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']


@app.route('/')
def home():
    return render_template('home.html')


from flask import send_from_directory
import qrcode
import os


@app.route('/class/<class_name>')
def class_schedule(class_name):
    try:
        schedule = load_schedule()
        if class_name not in schedule:
            return render_template('error.html', message="Класс не найден"), 404

        changes = load_changes(class_name)
        return render_template('class_schedule.html',
                               class_name=class_name,
                               schedule=schedule[class_name],
                               days=days_of_week,
                               bell_schedule=bell_schedule,
                               changes=changes)
    except Exception as e:
        logger.error(f"Error in class_schedule: {str(e)}")
        return render_template('error.html', message="Ошибка загрузки расписания"), 500


@app.route('/qr/<class_name>')
def generate_qr(class_name):
    try:
        # Проверяем существование класса
        schedule = load_schedule()
        if class_name not in schedule:
            return render_template('error.html', message="Класс не найден"), 404

        qr_path = f'static/qrcodes/{class_name}.png'
        if not os.path.exists(qr_path):
            url = f"{request.host_url}class/{class_name}"
            img = qrcode.make(url)
            img.save(qr_path)

        return send_from_directory('static/qrcodes', f'{class_name}.png')
    except Exception as e:
        logger.error(f"Error generating QR: {str(e)}")
        return render_template('error.html', message="Ошибка генерации QR-кода"), 500


@app.route('/generate_all_qr')
def generate_all_qr():
    try:
        schedule = load_schedule()
        for class_name in schedule.keys():
            qr_path = f'static/qrcodes/{class_name}.png'
            if not os.path.exists(qr_path):
                url = f"{request.host_url}class/{class_name}"
                img = qrcode.make(url)
                img.save(qr_path)

        return redirect(url_for('manage', message="Все QR-коды успешно сгенерированы", success=True))
    except Exception as e:
        logger.error(f"Error generating all QR codes: {str(e)}")
        return redirect(url_for('manage', message="Ошибка при генерации QR-кодов", error=True))


@app.route('/schedule/<parallel>')
def get_schedule(parallel):
    try:
        group = int(request.args.get('group', 1))

        # Получаем все классы параллели
        parallel_classes = {class_name: lessons for class_name, lessons in schedule_data.items()
                            if class_name.startswith(parallel)}

        # Разбиваем на группы по 4 класса
        all_classes = sorted(parallel_classes.keys())
        class_groups = [all_classes[i:i + 4] for i in range(0, len(all_classes), 4)]
        total_groups = len(class_groups)

        # Получаем текущую группу классов
        current_group = min(max(group, 1), total_groups)
        current_classes = class_groups[current_group - 1]

        # Фильтруем расписание только для текущей группы
        filtered_schedule = {class_name: parallel_classes[class_name] for class_name in current_classes}

        changes = {}
        for class_name in current_classes:
            class_changes = load_changes(class_name)
            changes[class_name] = [
                {"day": c["day"], "lesson_number": c["lesson_number"]}
                for c in class_changes
            ]

        return render_template('schedule.html',
                               schedule=filtered_schedule,
                               days=days_of_week,
                               bell_schedule=bell_schedule,
                               changes=changes,
                               parallel=parallel,
                               current_group=current_group,
                               total_groups=total_groups,
                               class_groups=class_groups,
                               current_classes=current_classes)
    except Exception as e:
        logger.error(f"Error in get_schedule: {str(e)}")
        return render_template('error.html', message="Ошибка загрузки расписания"), 500

@app.route('/manage')
def manage():
    try:
        message = request.args.get('message')
        error = request.args.get('error') == 'True'
        success = request.args.get('success') == 'True'
        warning = request.args.get('warning') == 'True'

        # Загружаем только актуальные изменения
        all_changes = {}
        for class_name in schedule_data.keys():
            changes = load_changes(class_name)
            actual_changes = []
            for change in changes:
                for lesson in schedule_data.get(class_name, []):
                    if (lesson['day'] == change['day'] and
                            lesson['lesson_number'] == change['lesson_number'] and
                            lesson['subject'] == change['new_subject']):
                        actual_changes.append(change)
                        break
            if actual_changes:
                all_changes[class_name] = actual_changes

        return render_template('manage.html',
                               schedule=schedule_data,
                               days_of_week=days_of_week,
                               bell_schedule=bell_schedule,
                               changes=all_changes,
                               message=message,
                               error=error,
                               success=success,
                               warning=warning)
    except Exception as e:
        logger.error(f"Error in manage: {str(e)}")
        return render_template('error.html', message="Ошибка загрузки страницы управления"), 500


@app.route('/add_class', methods=['POST'])
def add_class():
    try:
        new_class = request.form['class_name'].strip()
        if not new_class:
            return redirect(url_for('manage', message="Название класса не может быть пустым", error=True))

        if new_class in schedule_data:
            return redirect(url_for('manage', message="Класс уже существует", error=True))

        schedule_data[new_class] = []
        save_schedule(schedule_data)

        return redirect(url_for('manage', message=f"Класс {new_class} успешно добавлен", success=True))
    except Exception as e:
        logger.error(f"Error adding class: {str(e)}")
        return redirect(url_for('manage', message="Ошибка при добавлении класса", error=True))


@app.route('/edit_schedule', methods=['POST'])
def edit_schedule():
    try:
        class_name = request.form['class_name'].strip()
        day = request.form['day'].strip()
        lesson_number = int(request.form['lesson_number'])
        subject = request.form['subject'].strip()

        if not all([class_name, day, subject]):
            return redirect(url_for('manage', message="Все поля обязательны для заполнения", error=True))

        if class_name not in schedule_data:
            return redirect(url_for('manage', message=f"Класс {class_name} не найден", error=True))

        # Ищем урок для редактирования
        lesson_index = None
        original_lesson = None
        for i, lesson in enumerate(schedule_data[class_name]):
            if lesson['day'] == day and lesson['lesson_number'] == lesson_number:
                lesson_index = i
                original_lesson = lesson.copy()
                break

        if lesson_index is None:
            return redirect(url_for('manage', message=f"Урок {lesson_number} в {day} не найден", error=True))

        if original_lesson['subject'] == subject:
            return redirect(url_for('manage', message="Изменений не обнаружено", warning=True))

        # Сохраняем информацию об изменении
        change_data = {
            'old_subject': original_lesson['subject'],
            'new_subject': subject,
            'day': day,
            'lesson_number': lesson_number,
            'changed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'changed_by': 'admin'
        }

        # Обновляем расписание
        schedule_data[class_name][lesson_index]['subject'] = subject

        # Сохраняем изменения
        changes = load_changes(class_name)
        changes.append(change_data)
        save_changes(class_name, changes)
        save_schedule(schedule_data)

       # Запланировать автоматическую отмену через 60 минут
        revert_minutes = 60
        schedule_revert(class_name, day, lesson_number, revert_minutes)

        return redirect(url_for('manage',
                                message=f"Изменения сохранены. Будет автоматически отменено через 1 неделю.",
                                success=True))
    except ValueError:
        return redirect(url_for('manage', message="Некорректный номер урока", error=True))
    except Exception as e:
        logger.error(f"Error editing schedule: {str(e)}")
        return redirect(url_for('manage', message="Ошибка при сохранении изменений", error=True))


@app.route('/revert_change', methods=['POST'])
def revert_change():
    try:
        data = request.get_json()
        class_name = data['class_name']
        day = data['day']
        lesson_number = int(data['lesson_number'])

        # Загружаем текущие данные
        changes = load_changes(class_name)
        schedule = load_schedule()

        # Ищем изменение для отмены
        change_to_revert = None
        for change in changes:
            if (change['day'] == day and
                    change['lesson_number'] == lesson_number):
                change_to_revert = change
                break

        if not change_to_revert:
            return jsonify({
                'success': False,
                'message': 'Изменение не найдено'
            }), 404

        # Восстанавливаем оригинальный предмет в расписании
        for lesson in schedule[class_name]:
            if (lesson['day'] == day and
                    lesson['lesson_number'] == lesson_number):
                lesson['subject'] = change_to_revert['old_subject']
                break

        # Удаляем изменение из истории
        updated_changes = [c for c in changes if c != change_to_revert]
        save_changes(class_name, updated_changes)
        save_schedule(schedule)

        # Обновляем глобальную переменную
        global schedule_data
        schedule_data = load_schedule()

        return jsonify({
            'success': True,
            'message': f'Изменение для {class_name} отменено'
        })

    except Exception as e:
        logger.error(f"Error reverting change: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Внутренняя ошибка сервера'
        }), 500


@app.route('/upload')
def upload():
    return render_template('upload_schedule.html')


@app.route('/upload_schedule', methods=['POST'])
def upload_schedule():
    try:
        if 'schedule_file' not in request.files:
            return redirect(url_for('manage', message="Файл не выбран", error=True))

        file = request.files['schedule_file']
        if file.filename == '':
            return redirect(url_for('manage', message="Файл не выбран", error=True))

        if file and file.filename.endswith('.txt'):
            file_content = file.read().decode('utf-8')
            lines = file_content.split('\n')

            if len(lines) < 2:
                return redirect(
                    url_for('manage', message="Файл должен содержать название класса и расписание", error=True))

            class_name = lines[0].strip()
            if not class_name:
                return redirect(url_for('manage', message="Не указано название класса в файле", error=True))

            # Обработка расписания
            current_day = None
            lessons = []

            for line in lines[1:]:
                line = line.strip()
                if line in days_of_week:
                    current_day = line
                elif current_day and line:
                    lesson_number = len([l for l in lessons if l['day'] == current_day]) + 1
                    lessons.append({
                        'day': current_day,
                        'subject': line,
                        'lesson_number': lesson_number
                    })

            if not lessons:
                return redirect(url_for('manage', message="Не найдено расписание в файле", error=True))

            # Сохраняем расписание
            if class_name not in schedule_data:
                schedule_data[class_name] = []

            schedule_data[class_name].extend(lessons)
            save_schedule(schedule_data)

            return redirect(url_for('manage', message=f"Расписание для {class_name} успешно загружено", success=True))

        return redirect(url_for('manage', message="Неподдерживаемый формат файла", error=True))
    except Exception as e:
        logger.error(f"Error uploading schedule: {str(e)}")
        return redirect(url_for('manage', message="Ошибка при загрузке файла", error=True))


if __name__ == '__main__':
    app.run(host='192.168.1.2', port=777, debug=True)
