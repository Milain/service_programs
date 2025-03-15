import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
import pynput
from pynput import mouse, keyboard
import time
import threading


class MacroRecorderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Macro Recorder v1")
        self.root.geometry("430x200")

        # Список всех возможных клавиш
        self.all_key_options = ['F6', 'F7', 'F8', '~'] + [f'F{i}' for i in range(1, 13) if i not in [6, 7, 8]] + [
            'Ctrl', 'Alt', 'Shift']

        # Переменные
        self.recording = False
        self.playing = False
        self.actions = []
        self.last_time = None
        self.hotkey_listener = None
        self.stop_listener = None
        self.play_listener = None
        self.first_move = True
        self.last_position = None

        # Иконка справки
        self.help_button = tk.Button(root, text="?", command=self.show_help, width=2, height=1)
        self.help_button.place(x=5, y=5)

        # Главный фрейм для левой части (управление)
        left_frame = tk.Frame(root)
        left_frame.pack(side="left", padx=10, pady=10)

        # Старт записи
        start_frame = tk.Frame(left_frame)
        start_frame.pack(pady=2)
        tk.Label(start_frame, text="Старт записи:").pack(side="left")
        self.start_key = tk.StringVar(value='F6')
        self.start_menu = ttk.Combobox(start_frame, textvariable=self.start_key, values=self.all_key_options,
                                       state='readonly', width=10)
        self.start_menu.pack(side="left", padx=5)
        self.start_key.trace('w', self.update_menus_and_listeners)

        # Запуск скрипта (было "Стоп выполнения")
        play_frame = tk.Frame(left_frame)
        play_frame.pack(pady=2)
        tk.Label(play_frame, text="Запуск скрипта:").pack(side="left")
        self.play_key = tk.StringVar(value='F7')  # По умолчанию F7
        self.play_menu = ttk.Combobox(play_frame, textvariable=self.play_key, values=self.all_key_options,
                                      state='readonly', width=10)
        self.play_menu.pack(side="left", padx=5)
        self.play_key.trace('w', self.update_menus_and_listeners)

        # Стоп выполнения (было "Запуск скрипта")
        stop_frame = tk.Frame(left_frame)
        stop_frame.pack(pady=2)
        tk.Label(stop_frame, text="Стоп выполнения:").pack(side="left")
        self.stop_key = tk.StringVar(value='F8')  # По умолчанию F8
        self.stop_menu = ttk.Combobox(stop_frame, textvariable=self.stop_key, values=self.all_key_options,
                                      state='readonly', width=10)
        self.stop_menu.pack(side="left", padx=5)
        self.stop_key.trace('w', self.update_menus_and_listeners)

        # Задержка
        delay_frame = tk.Frame(left_frame)
        delay_frame.pack(pady=2)
        tk.Label(delay_frame, text="Задержка (сек):").pack(side="left")
        self.delay_spinbox = tk.Spinbox(delay_frame, from_=1, to=60, increment=1, width=5)
        self.delay_spinbox.delete(0, tk.END)
        self.delay_spinbox.insert(0, "5")  # По умолчанию 5 секунд
        self.delay_spinbox.pack(side="left", padx=5)

        self.status_label = tk.Label(left_frame, text=f"Нажмите {self.start_key.get()} для начала записи")
        self.status_label.pack(pady=5)

        # Правое окно для списка действий
        right_frame = tk.Frame(root)
        right_frame.pack(side="right", padx=10, pady=10, fill="y")
        tk.Label(right_frame, text="Записанные действия:").pack()
        self.action_listbox = tk.Listbox(right_frame, width=30, height=10)
        self.action_listbox.pack(fill="y", expand=True)

        # Слушатели
        self.mouse_listener = None
        self.keyboard_listener = None
        self.update_menus_and_listeners()

    def get_key_format(self, key):
        key = key.lower()
        if key.startswith('f'):
            return f'<{key}>'
        elif key == 'ctrl':
            return '<ctrl>'
        elif key == 'alt':
            return '<alt>'
        elif key == 'shift':
            return '<shift>'
        elif key == '~':
            return '`'
        return f'<{key}>'

    def update_menus_and_listeners(self, *args):
        # Получаем текущие выбранные клавиши
        used_keys = {self.start_key.get(), self.stop_key.get(), self.play_key.get()}

        # Обновляем доступные опции для каждого меню
        start_options = [key for key in self.all_key_options if key not in used_keys or key == self.start_key.get()]
        play_options = [key for key in self.all_key_options if key not in used_keys or key == self.play_key.get()]
        stop_options = [key for key in self.all_key_options if key not in used_keys or key == self.stop_key.get()]

        self.start_menu['values'] = start_options
        self.play_menu['values'] = play_options
        self.stop_menu['values'] = stop_options

        # Останавливаем старые слушатели
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        if self.stop_listener:
            self.stop_listener.stop()
        if self.play_listener:
            self.play_listener.stop()

        # Создаём новые слушатели
        self.hotkey_listener = keyboard.GlobalHotKeys(
            {self.get_key_format(self.start_key.get()): self.toggle_recording})
        self.stop_listener = keyboard.GlobalHotKeys({self.get_key_format(self.stop_key.get()): self.stop_execution})
        self.play_listener = keyboard.GlobalHotKeys({self.get_key_format(self.play_key.get()): self.start_playback})

        self.hotkey_listener.start()
        self.stop_listener.start()
        self.play_listener.start()

        if not self.recording and not self.playing:
            self.status_label.config(text=f"Нажмите {self.start_key.get()} для начала записи")

    def toggle_recording(self):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        self.recording = True
        self.actions = []
        self.action_listbox.delete(0, tk.END)
        self.last_time = time.time()
        self.first_move = True
        self.last_position = None
        self.status_label.config(text="Идёт запись...")

        self.mouse_listener = mouse.Listener(
            on_move=self.on_move,
            on_click=self.on_click,
            on_scroll=self.on_scroll)
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press)

        self.mouse_listener.start()
        self.keyboard_listener.start()

    def stop_recording(self):
        self.recording = False
        if self.last_position:  # Добавляем последнюю точку
            current_time = time.time()
            delay = current_time - self.last_time
            action = f"Last move to {self.last_position}, delay: {delay:.2f}s"
            self.actions.append(('move', self.last_position, delay))
            self.action_listbox.insert(tk.END, action)
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
        self.status_label.config(text="Запись остановлена")

    def on_move(self, x, y):
        if self.recording:
            current_time = time.time()
            delay = current_time - self.last_time
            self.last_position = (x, y)
            if self.first_move:
                action = f"First move to ({x}, {y}), delay: {delay:.2f}s"
                self.actions.append(('move', (x, y), delay))
                self.action_listbox.insert(tk.END, action)
                self.first_move = False
            self.actions.append(('move', (x, y), delay))  # Все движения для воспроизведения
            self.last_time = current_time

    def on_click(self, x, y, button, pressed):
        if self.recording:
            current_time = time.time()
            delay = current_time - self.last_time
            action = f"{'Press' if pressed else 'Release'} {button} at ({x}, {y}), delay: {delay:.2f}s"
            self.actions.append(('click', (x, y, button, pressed), delay))
            self.action_listbox.insert(tk.END, action)
            self.last_time = current_time

    def on_scroll(self, x, y, dx, dy):
        if self.recording:
            current_time = time.time()
            delay = current_time - self.last_time
            action = f"Scroll ({dx}, {dy}) at ({x}, {y}), delay: {delay:.2f}s"
            self.actions.append(('scroll', (x, y, dx, dy), delay))
            self.action_listbox.insert(tk.END, action)
            self.last_time = current_time

    def on_press(self, key):
        if self.recording:
            current_time = time.time()
            delay = current_time - self.last_time
            if self.last_position:
                action = f"Move to {self.last_position} before key, delay: {delay:.2f}s"
                self.actions.append(('move', self.last_position, delay))
                self.action_listbox.insert(tk.END, action)
            action = f"Press {key}, delay: {delay:.2f}s"
            self.actions.append(('key', (key, True), delay))
            self.action_listbox.insert(tk.END, action)
            self.last_time = current_time

    def start_playback(self):
        if not self.actions or self.playing:
            return

        self.playing = True
        self.status_label.config(text="Идёт воспроизведение...")

        delay = float(self.delay_spinbox.get() or 5)  # По умолчанию 5 секунд
        mouse_ctrl = mouse.Controller()
        keyboard_ctrl = keyboard.Controller()

        def playback_loop():
            while self.playing:
                for action_type, data, wait_time in self.actions:
                    if not self.playing:
                        break
                    time.sleep(wait_time)

                    if action_type == 'move':
                        mouse_ctrl.position = data
                    elif action_type == 'click':
                        x, y, button, pressed = data
                        mouse_ctrl.position = (x, y)
                        if pressed:
                            mouse_ctrl.press(button)
                        else:
                            mouse_ctrl.release(button)
                    elif action_type == 'scroll':
                        x, y, dx, dy = data
                        mouse_ctrl.position = (x, y)
                        mouse_ctrl.scroll(dx, dy)
                    elif action_type == 'key':
                        key, pressed = data
                        if pressed:
                            keyboard_ctrl.press(key)
                        else:
                            keyboard_ctrl.release(key)
                time.sleep(delay)

            self.playing = False
            self.status_label.config(text="Воспроизведение остановлено")

        threading.Thread(target=playback_loop, daemon=True).start()

    def stop_execution(self):
        if self.playing:
            self.playing = False
        self.recording = False
        self.actions = []
        self.action_listbox.delete(0, tk.END)
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
        self.status_label.config(text=f"Нажмите {self.start_key.get()} для начала записи")

    def show_help(self):
        help_window = Toplevel(self.root)
        help_window.title("Справка")
        help_window.geometry("400x360")
        help_window.resizable(False, False)

        help_text = (
            "Как пользоваться Macro Recorder:\n\n"
            f"1. Выберите клавишу для старта записи (по умолчанию {self.start_key.get()}):\n"
            "   - Нажмите эту клавишу, чтобы начать запись.\n"
            "   - Записываются движения мыши, клики, прокрутка и нажатия клавиш.\n"
            "   - Повторное нажатие останавливает запись.\n\n"
            "2. Укажите задержку между циклами в секундах:\n"
            "   - По умолчанию 5 секунд.\n"
            "   - Используйте стрелки для изменения (от 1 до 60).\n\n"
            f"3. Выберите клавишу для запуска скрипта (по умолчанию {self.play_key.get()}):\n"
            "   - Нажмите её для циклического воспроизведения.\n\n"
            f"4. Выберите клавишу для остановки (по умолчанию {self.stop_key.get()}):\n"
            "   - Останавливает воспроизведение и сбрасывает запись.\n\n"
            "5. Справа отображается список действий:\n"
            "   - Первая точка мыши, точки перед нажатием клавиш, последняя точка, клики, прокрутка и клавиши.\n"
            "6. Клавиши в полях не могут повторяться."
        )

        tk.Label(help_window, text=help_text, justify="left", wraplength=380).pack(pady=10)
        tk.Button(help_window, text="Закрыть", command=help_window.destroy).pack(pady=5)


if __name__ == "__main__":
    root = tk.Tk()
    app = MacroRecorderApp(root)
    root.mainloop()
