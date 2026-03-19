import customtkinter as ctk
import os
import glob
import sys
import subprocess
import math
import webbrowser
from PIL import Image, ImageTk
import tkinter.messagebox as messagebox
import tkinter as tk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class RefsApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Mini Refs Viewer — референсы для покраса")
        self.geometry("1200x850")

        self.root_path = os.path.expanduser("~/reference_library")
        if not os.path.exists(self.root_path):
            os.makedirs(self.root_path, exist_ok=True)

        self.paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=6, sashrelief="raised")
        self.paned.pack(fill="both", expand=True)

        self.left_frame = ctk.CTkFrame(self.paned)
        self.paned.add(self.left_frame, minsize=320)
        self.paned.paneconfig(self.left_frame, width=380)

        header_frame = ctk.CTkFrame(self.left_frame)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        self.refresh_button = ctk.CTkButton(
            header_frame, text="🔄 Обновить", command=self.load_categories, width=140
        )
        self.refresh_button.pack(side="left", padx=(0, 8))

        self.open_folder_button = ctk.CTkButton(
            header_frame, text="📁 Открыть папку", command=self.open_folder_in_explorer, width=140
        )
        self.open_folder_button.pack(side="left")

        self.scrollable_left = ctk.CTkScrollableFrame(self.left_frame)
        self.scrollable_left.pack(fill="both", expand=True, padx=10, pady=10)

        self.right_frame = ctk.CTkFrame(self.paned)
        self.paned.add(self.right_frame, minsize=400)

        self.current_images = []
        self.selected_index = 0
        self.fullscreen_active = False

        self.load_categories()
        self.left_frame.bind("<Configure>", self.on_left_resize)

        # Привязка клавиатуры (работает глобально, когда окно в фокусе)
        self.bind("<Left>",  self.on_key_prev)
        self.bind("<Right>", self.on_key_next)
        self.bind("<a>",     self.on_key_prev)   # A / а
        self.bind("<A>",     self.on_key_prev)
        self.bind("<d>",     self.on_key_next)   # D / в
        self.bind("<D>",     self.on_key_next)
        self.bind("<Escape>", self.on_key_escape)

    def on_key_prev(self, event=None):
        if self.fullscreen_active and self.current_images:
            self.selected_index = (self.selected_index - 1) % len(self.current_images)
            self.show_full_image()

    def on_key_next(self, event=None):
        if self.fullscreen_active and self.current_images:
            self.selected_index = (self.selected_index + 1) % len(self.current_images)
            self.show_full_image()

    def on_key_escape(self, event=None):
        if self.fullscreen_active:
            self.clear_right()
            self.fullscreen_active = False

    def on_left_resize(self, event):
        if hasattr(self, '_last_left_width') and self._last_left_width == event.width:
            return
        self._last_left_width = event.width
        self.load_categories()

    def open_folder_in_explorer(self):
        path = os.path.abspath(self.root_path)
        if not os.path.exists(path):
            messagebox.showerror("Ошибка", f"Папка не найдена:\n{path}")
            return
        try:
            if sys.platform == 'win32':
                os.startfile(path)
            elif sys.platform == 'darwin':
                subprocess.call(['open', path])
            else:
                subprocess.call(['xdg-open', path])
        except Exception as e:
            messagebox.showerror("Ошибка открытия", f"Не удалось открыть:\n{str(e)}")

    def open_url(self, url):
        try:
            webbrowser.open(url, new=2)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть ссылку:\n{str(e)}")

    def load_categories(self):
        for widget in self.scrollable_left.winfo_children():
            widget.destroy()

        subdirs = [d for d in os.listdir(self.root_path) if os.path.isdir(os.path.join(self.root_path, d))]
        subdirs.sort()

        if not subdirs:
            ctk.CTkLabel(self.scrollable_left, text="Папка готова, но пустая.\nСоздай подпапки с темами").pack(pady=40)
            return

        left_width = self.left_frame.winfo_width() or 380
        thumb_size = 110
        padding = 8          # было 12 → стало меньше
        cols = max(1, math.floor((left_width - 30) / (thumb_size + padding)))

        for cat in subdirs:
            cat_path = os.path.join(self.root_path, cat)
            images = self.get_images(cat_path)
            links = self.get_links(cat_path)

            if not images and not links:
                continue

            expander = CollapsibleFrame(self.scrollable_left, text=f"{cat}  ({len(images)} фото)")
            expander.pack(fill="x", pady=5)

            link_frame = ctk.CTkFrame(expander.content_frame)
            link_frame.pack(fill="x", pady=(6, 3))

            if links:
                ctk.CTkLabel(link_frame, text="Ссылки:", font=("Arial", 13, "bold")).pack(anchor="w")
                for link in links[:12]:
                    if link.startswith(('http://', 'https://')):
                        lbl = ctk.CTkLabel(
                            link_frame,
                            text=link,
                            text_color="#1e90ff",
                            cursor="hand2",
                            justify="left",
                            wraplength=left_width-80
                        )
                        lbl.pack(anchor="w", pady=1)
                        lbl.bind("<Button-1>", lambda e, u=link: self.open_url(u))
                        lbl.bind("<Enter>", lambda e, l=lbl: l.configure(text_color="#00bfff"))
                        lbl.bind("<Leave>", lambda e, l=lbl: l.configure(text_color="#1e90ff"))
                    else:
                        ctk.CTkLabel(link_frame, text=link, justify="left", wraplength=left_width-80).pack(anchor="w", pady=1)
                if len(links) > 12:
                    ctk.CTkLabel(link_frame, text=f"... ещё {len(links)-12}").pack(anchor="w")
            else:
                hint = ctk.CTkLabel(
                    link_frame,
                    text="Здесь могут быть полезные ссылки (создай файл links.txt)",
                    text_color="gray",
                    justify="left",
                    wraplength=left_width-80
                )
                hint.pack(anchor="w", pady=3)

            if images:
                gallery_frame = ctk.CTkFrame(expander.content_frame)
                gallery_frame.pack(fill="x", pady=4)

                for i, img_path in enumerate(images):
                    try:
                        img = Image.open(img_path)
                        img.thumbnail((thumb_size, thumb_size * 1.4))
                        photo = ImageTk.PhotoImage(img)

                        btn = ctk.CTkButton(
                            gallery_frame, image=photo, text="",
                            fg_color="transparent", hover_color="#3a3a3a",
                            width=thumb_size+4, height=thumb_size+8*1.4,
                            command=lambda p=cat_path, idx=i: self.open_fullscreen(p, idx)
                        )
                        btn.image = photo
                        btn.grid(row=i//cols, column=i%cols, padx=3, pady=3, sticky="nsew")   # padx/pady уменьшены
                        gallery_frame.grid_columnconfigure(i % cols, weight=1)
                    except:
                        pass

    def get_images(self, path):
        exts = ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp", "*.bmp"]
        imgs = []
        for ext in exts:
            imgs.extend(glob.glob(os.path.join(path, ext)))
        return sorted(imgs)

    def get_links(self, path):
        links_file = os.path.join(path, "links.txt")
        if not os.path.exists(links_file):
            return []
        try:
            with open(links_file, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]
        except:
            return []

    def open_fullscreen(self, cat_path, index):
        self.current_images = self.get_images(cat_path)
        if not self.current_images:
            return
        self.selected_index = index % len(self.current_images)
        self.fullscreen_active = True
        self.show_full_image()

    def show_full_image(self):
        for widget in self.right_frame.winfo_children():
            widget.destroy()

        if not self.current_images:
            ctk.CTkLabel(self.right_frame, text="Нет изображений").pack(expand=True)
            return

        img_path = self.current_images[self.selected_index]
        try:
            img = Image.open(img_path)
            avail_w = self.right_frame.winfo_width() - 60
            avail_h = self.right_frame.winfo_height() - 140
            if avail_w < 100 or avail_h < 100:
                avail_w, avail_h = 800, 600

            ratio = min(avail_w / img.width, avail_h / img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            label = ctk.CTkLabel(self.right_frame, image=photo, text="")
            label.image = photo
            label.pack(expand=True, pady=10, fill="both")

            name = os.path.basename(img_path)
            ctk.CTkLabel(self.right_frame, text=f"{self.selected_index+1} / {len(self.current_images)} — {name}").pack(pady=4)
        except Exception as e:
            ctk.CTkLabel(self.right_frame, text=f"Ошибка загрузки\n{str(e)}").pack(expand=True)

        # Центрируем кнопки навигации
        nav_container = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        nav_container.pack(fill="x", pady=8)

        nav_frame = ctk.CTkFrame(nav_container, fg_color="transparent")
        nav_frame.pack(anchor="center")  # ← вот ключ: anchor="center" внутри контейнера

        ctk.CTkButton(nav_frame, text="⬅️ Предыдущая", command=self.prev_image).pack(side="left", padx=30)
        ctk.CTkButton(nav_frame, text="Открыть оригинал", command=lambda: self.open_original(self.current_images[self.selected_index])).pack(side="left", padx=30)
        ctk.CTkButton(nav_frame, text="Следующая ➡️", command=self.next_image).pack(side="left", padx=30)

    def open_original(self, img_path):
        if not os.path.exists(img_path):
            messagebox.showerror("Ошибка", "Файл не найден")
            return
        try:
            if sys.platform == 'win32':
                os.startfile(img_path)
            elif sys.platform == 'darwin':
                subprocess.call(['open', img_path])
            else:
                subprocess.call(['xdg-open', img_path])
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть:\n{str(e)}")

    def prev_image(self):
        if self.current_images:
            self.selected_index = (self.selected_index - 1) % len(self.current_images)
            self.show_full_image()

    def next_image(self):
        if self.current_images:
            self.selected_index = (self.selected_index + 1) % len(self.current_images)
            self.show_full_image()

    def clear_right(self):
        for widget in self.right_frame.winfo_children():
            widget.destroy()
        self.current_images = []
        self.selected_index = 0
        self.fullscreen_active = False


class CollapsibleFrame(ctk.CTkFrame):
    def __init__(self, parent, text="", **kwargs):
        super().__init__(parent, **kwargs)
        self.is_expanded = False

        self.header = ctk.CTkButton(
            self, text=f"▶ {text}", anchor="w", fg_color="transparent", hover_color="#2e2e2e",
            command=self.toggle, corner_radius=6, height=34
        )
        self.header.pack(fill="x")

        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")

    def toggle(self):
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            self.header.configure(text=f"▼ {self.header.cget('text')[2:]}")
            self.content_frame.pack(fill="x", expand=True)
        else:
            self.header.configure(text=f"▶ {self.header.cget('text')[2:]}")
            self.content_frame.pack_forget()


if __name__ == "__main__":
    app = RefsApp()
    app.mainloop()