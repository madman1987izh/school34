import json
import tkinter as tk
from tkinter import messagebox, scrolledtext
from tkinter import ttk

def load_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}
    return data

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def add_data(file_path, class_name, new_data):
    data = load_json(file_path)
    if class_name not in data:
        data[class_name] = []
    data[class_name].append(new_data)
    save_json(file_path, data)

def remove_duplicates(data):
    seen = set()
    unique_data = []
    for entry in data:
        entry_tuple = tuple(entry.items())
        if entry_tuple not in seen:
            seen.add(entry_tuple)
            unique_data.append(entry)
    return unique_data

def validate_and_correct_data(data):
    for class_name in data:
        for entry in data[class_name]:
            if 'day' not in entry or not isinstance(entry['day'], str):
                entry['day'] = 'Unknown'
            if 'subject' not in entry or not isinstance(entry['subject'], str):
                entry['subject'] = 'Unknown'
            if 'lesson_number' not in entry or not isinstance(entry['lesson_number'], int):
                entry['lesson_number'] = 0
    return data

def check_conflicts(data):
    for class_name in data:
        schedule = data[class_name]
        lesson_map = {}
        for entry in schedule:
            key = (entry['day'], entry['lesson_number'])
            if key in lesson_map and lesson_map[key] != entry['subject']:
                messagebox.showerror("Ошибка", f"Конфликт в классе {class_name}: {entry['day']} урок {entry['lesson_number']} назначен на {lesson_map[key]} и {entry['subject']}")
                schedule.remove(entry)
            else:
                lesson_map[key] = entry['subject']
    return data

def check_lesson_limits(data):
    for class_name in data:
        day_count = {}
        for entry in data[class_name]:
            day = entry['day']
            if day not in day_count:
                day_count[day] = 0
            day_count[day] += 1
            if day_count[day] > 8:
                messagebox.showerror("Ошибка", f"В классе {class_name} на {day} назначено более 8 уроков")
                data[class_name].remove(entry)
    return data

def submit_data():
    class_name = class_entry.get()
    day = day_entry.get()
    subject = subject_entry.get()
    lesson_number = lesson_number_entry.get()

    if not lesson_number.isdigit():
        messagebox.showerror("Ошибка", "Номер урока должен быть числом")
        return

    new_data = {
        'day': day,
        'subject': subject,
        'lesson_number': int(lesson_number)
    }

    add_data('schedule.json', class_name, new_data)
    messagebox.showinfo("Успех", "Данные успешно добавлены")
    display_data()

def display_data(filter_class=None):
    data = load_json('schedule.json')
    
    for row in tree.get_children():
        tree.delete(row)
    
    for class_name, schedule in data.items():
        if filter_class and filter_class != class_name:
            continue
        for entry in schedule:
            tree.insert("", tk.END, values=(class_name, entry['day'], entry['subject'], entry['lesson_number']))

def apply_filter():
    filter_class = filter_entry.get()
    display_data(filter_class)

def check_and_correct_data():
    data = load_json('schedule.json')
    data = validate_and_correct_data(data)
    save_json('schedule.json', data)
    messagebox.showinfo("Успех", "Данные проверены и исправлены")
    display_data()

def remove_duplicates_button():
    data = load_json('schedule.json')
    for class_name in data:
        data[class_name] = remove_duplicates(data[class_name])
    save_json('schedule.json', data)
    messagebox.showinfo("Успех", "Дубликаты удалены")
    display_data()

def check_conflicts_button():
    data = load_json('schedule.json')
    data = check_conflicts(data)
    data = check_lesson_limits(data)
    save_json('schedule.json', data)
    messagebox.showinfo("Успех", "Конфликты и превышения количества уроков удалены")
    
app = tk.Tk()
app.title("Schedule Manager")

tk.Label(app, text="Класс").grid(row=0)
tk.Label(app, text="День").grid(row=1)
tk.Label(app, text="Предмет").grid(row=2)
tk.Label(app, text="Номер урока").grid(row=3)

class_entry = tk.Entry(app)
day_entry = tk.Entry(app)
subject_entry = tk.Entry(app)
lesson_number_entry = tk.Entry(app)

class_entry.grid(row=0, column=1)
day_entry.grid(row=1, column=1)
subject_entry.grid(row=2, column=1)
lesson_number_entry.grid(row=3, column=1)

tk.Button(app, text="Добавить данные", command=submit_data).grid(row=4, column=1)

tk.Label(app, text="Фильтр по классу").grid(row=5)
filter_entry = tk.Entry(app)
filter_entry.grid(row=5, column=1)

tk.Button(app, text="Применить фильтр", command=apply_filter).grid(row=6, column=1)

tk.Button(app, text="Проверить данные", command=check_and_correct_data).grid(row=7, column=1)
tk.Button(app, text="Удалить дубликаты", command=remove_duplicates_button).grid(row=8, column=1)
tk.Button(app, text="Проверить конфликты", command=check_conflicts_button).grid(row=9, column=1)

columns = ("Класс", "День", "Предмет", "Номер урока")
tree = ttk.Treeview(app, columns=columns, show="headings")
tree.heading("Класс", text="Класс")
tree.heading("День", text="День")
tree.heading("Предмет", text="Предмет")
tree.heading("Номер урока", text="Номер урока")

tree.grid(row=10, column=0, columnspan=2)

display_data()

app.mainloop()
