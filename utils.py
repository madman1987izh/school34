import json
from datetime import datetime, timedelta
import threading
import time
from datetime import datetime


def schedule_revert(class_name, day, lesson_number, revert_after_minutes):
    """Запланировать автоматическую отмену изменения"""

    def revert_task():
        time.sleep((revert_after_minutes + 10080) * 60)  # Конвертируем минуты в секунды

        try:
            changes = load_changes(class_name)
            schedule = load_schedule()

            # Находим изменение для отмены
            change_to_revert = None
            for change in changes:
                if (change['day'] == day and
                        change['lesson_number'] == lesson_number):
                    change_to_revert = change
                    break

            if change_to_revert:
                # Восстанавливаем оригинальный предмет
                for lesson in schedule[class_name]:
                    if (lesson['day'] == day and
                            lesson['lesson_number'] == lesson_number):
                        lesson['subject'] = change_to_revert['old_subject']
                        break

                # Удаляем изменение из истории
                changes.remove(change_to_revert)
                save_changes(class_name, changes)
                save_schedule(schedule)

                app.logger.info(f"Автоматически отменено изменение для {class_name}, {day}, урок {lesson_number}")
        except Exception as e:
            app.logger.error(f"Ошибка при автоматической отмене изменения: {str(e)}")

    # Запускаем в фоновом потоке
    thread = threading.Thread(target=revert_task)
    thread.daemon = True
    thread.start()

days_of_week = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']

def load_schedule():
    try:
        with open('schedule.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_schedule(schedule):
    try:
        with open('schedule.json', 'w', encoding='utf-8') as f:
            json.dump(schedule, f, ensure_ascii=False, indent=4)
    except IOError as e:
        print(f"Error saving schedule: {e}")

def save_changes(class_name, changes):
    try:
        filename = f'{class_name}_changes.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(changes, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        app.logger.error(f"Error saving changes for {class_name}: {str(e)}")
        return False

def load_changes(class_name):
    try:
        filename = f'{class_name}_changes.json'
        with open(filename, 'r', encoding='utf-8') as f:
            changes = json.load(f)
            # Проверяем структуру данных
            return [c for c in changes if all(k in c for k in ['day', 'lesson_number', 'old_subject', 'new_subject'])]
    except FileNotFoundError:
        return []
    except Exception as e:
        app.logger.error(f"Error loading changes for {class_name}: {str(e)}")
        return []

def parse_schedule_file(file_content):
    lines = file_content.split('\n')
    class_name = lines[0].strip()
    schedule = {day: [] for day in days_of_week}
    current_day = None

    for line in lines[1:]:
        line = line.strip()
        if line in days_of_week:
            current_day = line
        elif current_day and line:
            lesson_number = len(schedule[current_day]) + 1
            schedule[current_day].append({'day': current_day, 'subject': line, 'lesson_number': lesson_number})

    return class_name, schedule
def load_changes(class_name):
    filename = f'{class_name}_changes.json'
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)  # Возвращает список словарей с изменениями
    except (FileNotFoundError, json.JSONDecodeError):
        return []  # Если файла нет, возвращаем пустой список
def record_change(class_name, change_data):
    """Записывает изменение в историю"""
    changes = load_changes(class_name)
    changes.append(change_data)
    save_changes(class_name, changes)