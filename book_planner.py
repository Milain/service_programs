import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
import datetime
import calendar
from math import ceil
import pystray
from PIL import Image, ImageTk
import threading
import locale

locale.setlocale(locale.LC_TIME, "ru_RU")

# Путь к файлу для сохранения
DATA_FILE = "books.json"


# Функция для загрузки данных
def load_books():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


# Функция для сохранения данных
def save_books(books):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=4)


# Основной класс приложения
class BookPlannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("План чтения книг")
        self.books = load_books()  # Загружаем существующие книги

        # Полупрозрачность окна (0.0 - полностью прозрачно, 1.0 - непрозрачно)
        self.root.attributes('-alpha', 0.8)  # Например, 80% непрозрачности

        # Вкладки
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill="both")

        self.months = {
            "Январь": "01",
            "Февраль": "02",
            "Март": "03",
            "Апрель": "04",
            "Май": "05",
            "Июнь": "06",
            "Июль": "07",
            "Август": "08",
            "Сентябрь": "09",
            "Октябрь": "10",
            "Ноябрь": "11",
            "Декабрь": "12"
        }

        self.months_names = list(self.months.keys())  # ["Январь", "Февраль", ...]

        self.current_date = datetime.date.today()
        self.current_year = self.current_date.year
        self.current_month_num = f"{self.current_date.month:02d}"
        self.current_month_name = self.current_date.strftime("%B")

##########################
        # Вкладка "План чтения" (основная)
        self.plan_frame = tk.Frame(self.notebook)
        self.notebook.add(self.plan_frame, text="План чтения")

        # Окно с планом
        self.plan_tree = ttk.Treeview(self.plan_frame, columns=("day","book", "today","page","left"), show="headings")
        self.plan_tree.heading("day", text="День")
        self.plan_tree.heading("book", text="Книга")
        self.plan_tree.heading("today", text="Читать сегодня")
        self.plan_tree.heading("page", text="Будешь на странице")
        self.plan_tree.heading("left", text="Осталось")
        self.plan_tree.pack(expand=True, fill="both")

        # Фрейм для активных штук
        actions_frame = tk.Frame(self.plan_frame)
        actions_frame.pack(fill='x', pady=10, anchor='w', padx=5)

        # Выпадающее меню для выбора месяца
        self.month_var = tk.StringVar()
        self.month_combobox = ttk.Combobox(actions_frame, textvariable=self.months_names, state="readonly")
        self.month_combobox.pack(side=tk.LEFT, padx=5)
        self.month_combobox['values'] = self.months_names
        self.month_combobox.set(self.current_month_name)

        self.month_combobox.bind("<<ComboboxSelected>>", lambda e: self.refresh_plan())

        # Кнопка обновления плана
        refresh_plan_button = tk.Button(actions_frame, text="Обновить план", command=self.refresh_plan)
        refresh_plan_button.pack(side=tk.LEFT, padx=5, pady=0)

        # Кнопка для минимизации в трей
        minimize_button = tk.Button(actions_frame, text="Скрыть в трей", command=self.hide_window)
        minimize_button.pack(side=tk.RIGHT, padx=5, pady=0)

##########################
        # Вкладка "Список книг"
        self.list_frame = tk.Frame(self.notebook)
        self.notebook.add(self.list_frame, text="Список книг")

        self.list_tree = ttk.Treeview(self.list_frame, columns=("title", "author","pages_readed", "pages_cnt", "month", "read"),
                                      show="headings")
        self.list_tree.heading("title", text="Название")
        self.list_tree.heading("author", text="Автор")
        self.list_tree.heading("pages_readed", text="Страниц прочитано")
        self.list_tree.heading("pages_cnt", text="Страниц всего")
        self.list_tree.heading("month", text="Месяц")
        self.list_tree.heading("read", text="Статус")
        self.list_tree.pack(expand=True, fill="both")

        # self.list_tree.bind("<Double-1>", self.toggle_read)
        self.list_tree.bind("<Double-1>", self.on_double_click)

##########################
        # Вкладка "Добавить книгу"
        self.input_frame = tk.Frame(self.notebook)
        self.notebook.add(self.input_frame, text="Добавить книгу")

        tk.Label(self.input_frame, text="Название:").grid(row=0, column=0, padx=5, pady=5)
        self.title_entry = tk.Entry(self.input_frame)
        self.title_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self.input_frame, text="Автор:").grid(row=1, column=0, padx=5, pady=5)
        self.author_entry = tk.Entry(self.input_frame)
        self.author_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(self.input_frame, text="Страниц:").grid(row=2, column=0, padx=5, pady=5)
        self.pages_entry = tk.Entry(self.input_frame)
        self.pages_entry.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(self.input_frame, text="Месяц (YYYY-MM):").grid(row=3, column=0, padx=5, pady=5)
        self.month_entry = tk.Entry(self.input_frame)
        self.month_entry.grid(row=3, column=1, padx=5, pady=5)
        self.month_entry.insert(0, f"{self.current_year}-{self.current_month_num}")

        add_button = tk.Button(self.input_frame, text="Добавить книгу", command=self.add_book)
        add_button.grid(row=4, column=0, columnspan=2, pady=10)

        # Инициализация
        self.refresh_list()
        self.refresh_plan()

    def add_book(self):
        title = self.title_entry.get().strip()
        author = self.author_entry.get().strip()
        pages_str = self.pages_entry.get().strip()
        month = self.month_entry.get().strip()

        if not title or not author or not pages_str or not month:
            messagebox.showerror("Ошибка", "Заполните все поля!")
            return

        try:
            pages = int(pages_str)
            if pages <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Страницы должны быть положительным числом!")
            return

        # Добавляем книгу
        new_book = {"title": title, "author": author, "pages": pages, "month": month, "read": False, "readed": 0}
        self.books.append(new_book)
        save_books(self.books)
        self.refresh_list()
        self.refresh_plan()
        messagebox.showinfo("Успех", "Книга добавлена!")

        # Очищаем поля
        self.title_entry.delete(0, tk.END)
        self.author_entry.delete(0, tk.END)
        self.pages_entry.delete(0, tk.END)
        # self.month_entry.delete(0, tk.END)

    def refresh_list(self):
        # Очищаем дерево списка
        for item in self.list_tree.get_children():
            self.list_tree.delete(item)

        # Добавляем книги
        for book in self.books:
            read_status = "✔" if book["read"] else "❌"
            self.list_tree.insert("", "end",
                                  values=(book["title"], book["author"],book["readed"], book["pages"], book["month"], read_status))

    def toggle_read(self, event):
        selected = self.list_tree.selection()
        if not selected:
            return

        # Находим индекс выбранной книги
        item = selected[0]
        index = self.list_tree.index(item)

        # Переключаем статус
        self.books[index]["read"] = not self.books[index]["read"]
        save_books(self.books)
        self.refresh_list()
        self.refresh_plan()

    def refresh_plan(self):

        # Очищаем дерево плана
        for item in self.plan_tree.get_children():
            self.plan_tree.delete(item)

        # Получаем выбранный месяц
        # print('t1')
        selected_month_num = self.months.get(self.month_combobox.get())
        selected_month_full = f"{self.current_year}-{selected_month_num}"
        # print(selected_month_full)
        selected_month=selected_month_full

        # Если нет книг
        books_this_month = [b for b in self.books if b['month'] == selected_month_full and not b['read']]

        if not books_this_month:
            self.plan_tree.insert("", "end", values=("Нет книг", "Добавьте книги на этот месяц"))
            return

        # Определяем дни в месяце
        month_int = int(self.current_month_num)
        # print(month_int)
        _, last_day = calendar.monthrange(self.current_year, month_int)

        if month_int != self.current_date.month:
            start_day = 1
            # remaining_days = last_day
        else:
            start_day = self.current_date.day
            # remaining_days = last_day

        remaining_days=(last_day-start_day)+1

        #Считаем среднее количество страниц
        total_pages=0
        for book in books_this_month:
            total_pages=total_pages+(book['pages']-book['readed'])
        avg_pages=total_pages // remaining_days
        cnt_books=len(books_this_month)
        # print('yy')

        filled_days=0
        for book in books_this_month:
            total_pages = book['pages']-book['readed']
            filled_days=filled_days+total_pages//avg_pages
        empty_days=remaining_days-filled_days
        # print(remaining_days)
        # print(filled_days)
        # print(empty_days)
        #Заполняем таблицу
        j = start_day
        for book in books_this_month:
            # print(book['title'])
            flag_plus=0
            total_pages = book['pages']-book['readed']
            book_days=total_pages//avg_pages
            if book_days!=total_pages/avg_pages and empty_days>0:
                book_days=book_days+1
                empty_days=empty_days-1
                flag_plus=1
            cur_page = book['readed']
            rem_pages=total_pages
            for i in range(book_days):
                cur_page=cur_page+avg_pages
                rem_pages=rem_pages-avg_pages
                avg_for_book=avg_pages
                # print(rem_pages)
                # print(avg_pages)
                if rem_pages<avg_pages and flag_plus==0:
                    avg_for_book = avg_pages + rem_pages
                    cur_page=book['pages']
                    rem_pages=0
                elif flag_plus==1 and cur_page>book['pages']:
                    avg_for_book =rem_pages+avg_pages
                    cur_page = book['pages']
                    rem_pages = 0
                # print(cur_page.__str__()+ ' / ' + rem_pages.__str__())
                self.plan_tree.insert("", "end", values=(f"{self.current_year}-{selected_month_num}-{j}", book['title'],avg_for_book,cur_page,rem_pages))
                j=j+1

        # j = start_day
        # for book in books_this_month:
        #     print(book['title'])
        #     total_pages = book['pages'] - book['readed']
        #     book_days = total_pages // avg_pages
        #     cur_page = book['readed']
        #     rem_pages = total_pages
        #     for i in range(book_days):
        #         cur_page = cur_page + avg_pages
        #         rem_pages = rem_pages - avg_pages
        #         avg_for_book = avg_pages
        #         print(rem_pages)
        #         print(avg_pages)
        #         if rem_pages < avg_pages:
        #             avg_for_book = avg_pages + rem_pages
        #             cur_page = book['pages']
        #             rem_pages = 0
        #         print(cur_page.__str__() + ' / ' + rem_pages.__str__())
        #         self.plan_tree.insert("", "end", values=(
        #         f"{self.current_year}-{selected_month_num}-{j}", book['title'], avg_for_book, cur_page, rem_pages))
        #         j = j + 1

    def hide_window(self):
        self.root.withdraw()  # Скрываем окно

    def show_window(self):
        self.root.deiconify()  # Показываем окно

    def quit_app(self):
        self.root.quit()  # Выход из приложения

    def on_double_click(self, event):
        """При двойном клике — открываем редактирование ячейки"""
        # Определяем, на какую ячейку кликнули
        item = self.list_tree.identify_row(event.y)
        if not item:
            return

        column = self.list_tree.identify_column(event.x)
        if not column:
            return

        # column приходит как '#1', '#2' и т.д.
        col_index = int(column[1:]) - 1  # 0 = title, 1 = author, 2 = pages, 3 = month, 4 = read

        # Запрещаем редактировать столбец "Прочитано" (или разрешаем, если хочешь)
        # if col_index == 4:  # read
        #     return

        # Получаем текущие координаты ячейки
        bbox = self.list_tree.bbox(item, column)
        if not bbox:
            return

        # Текущее значение ячейки
        current_values = self.list_tree.item(item, "values")
        current_text = current_values[col_index]

        # Удаляем старое поле ввода, если было открыто
        self.destroy_edit_entry()

        # Создаём временное поле Entry поверх ячейки
        self.edit_entry = tk.Entry(self.list_frame)
        self.edit_entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])

        self.edit_entry.insert(0, current_text)
        self.edit_entry.focus_set()
        self.edit_entry.select_range(0, tk.END)

        # Запоминаем, какую строку и столбец редактируем
        self.edit_item = item
        self.edit_col_index = col_index

        # Сохраняем при нажатии Enter или потере фокуса
        self.edit_entry.bind("<Return>", self.save_edit)
        self.edit_entry.bind("<FocusOut>", self.save_edit)

    def save_edit(self, event=None):
        """Сохраняем значение из поля ввода"""
        if not hasattr(self, 'edit_entry') or not self.edit_entry:
            return

        new_value = self.edit_entry.get().strip()

        # Получаем индекс книги в списке self.books
        # (iid в Treeview совпадает с индексом, если мы вставляли так)
        iid = self.edit_item
        index = int(iid) if iid.isdigit() else self.list_tree.index(iid)

        # Обновляем модель данных
        key = ["title", "author", "readed", "pages", "month", "read"][self.edit_col_index]

        if key == "pages":
            try:
                new_value = int(new_value)
            except ValueError:
                messagebox.showwarning("Ошибка", "Страницы должны быть числом")
                self.destroy_edit_entry()
                return

        if key == "readed":
            try:
                new_value = int(new_value)
            except ValueError:
                messagebox.showwarning("Ошибка", "Страницы должны быть числом")
                self.destroy_edit_entry()
                return

        self.books[index][key] = new_value

        # Сохраняем на диск
        save_books(self.books)

        # Обновляем отображение
        self.refresh_list()

        # Удаляем поле ввода
        self.destroy_edit_entry()

    def destroy_edit_entry(self):
        """Удаляем временное поле ввода, если оно существует"""
        if hasattr(self, 'edit_entry') and self.edit_entry:
            self.edit_entry.destroy()
            self.edit_entry = None
        if hasattr(self, 'edit_item'):
            del self.edit_item
        if hasattr(self, 'edit_col_index'):
            del self.edit_col_index

# Функция для запуска tray в отдельном потоке
def run_tray(app):
    # Создаём простую иконку (замени на свою PNG/ICO)
    image = Image.new('RGB', (64, 64), color=(0, 0, 0))  # Чёрный квадрат для примера

    # Меню для tray
    menu = (
        pystray.MenuItem('Показать', app.show_window),
        pystray.MenuItem('Скрыть', app.hide_window),
        pystray.MenuItem('Выход', app.quit_app)
    )

    # Создаём иконку
    icon = pystray.Icon("book_planner", image, "План чтения", menu)
    icon.run()


# Запуск приложения
if __name__ == "__main__":
    root = tk.Tk()
    app = BookPlannerApp(root)

    # Запускаем tray в отдельном потоке
    tray_thread = threading.Thread(target=run_tray, args=(app,), daemon=True)
    tray_thread.start()

    root.mainloop()