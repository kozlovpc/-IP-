import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
import ctypes

class ProfileManager:
    """Управление профилями сетевых настроек."""
    def __init__(self, filename='profiles.json'):
        self.filename = filename
        self.profiles = []
        self.load_profiles()

    def load_profiles(self):
        try:
            with open(self.filename, 'r') as f:
                self.profiles = json.load(f)
        except:
            self.profiles = []

    def save_profiles(self):
        with open(self.filename, 'w') as f:
            json.dump(self.profiles, f, indent=4)

    def add_profile(self, profile):
        self.profiles.append(profile)
        self.save_profiles()

class ProfileSettingsWindow(tk.Toplevel):
    """Окно редактирования профиля."""
    def __init__(self, parent, profile=None):
        super().__init__(parent)
        self.parent = parent
        self.profile = profile or {
            "name": "Новый профиль",
            "interface": "Ethernet",
            "ip": "192.168.1.100",
            "mask": "255.255.255.0",
            "gateway": "192.168.1.1",
            "dns1": "8.8.8.8",
            "dns2": "8.8.4.4"
        }

        self.title("Параметры профиля")
        self.geometry("300x300")

        fields = [
            ("Имя профиля", "name"),
            ("Интерфейс", "interface"),
            ("IP-адрес", "ip"),
            ("Маска", "mask"),
            ("Шлюз", "gateway"),
            ("DNS1", "dns1"),
            ("DNS2", "dns2")
        ]

        self.entries = {}
        for row, (label, key) in enumerate(fields):
            tk.Label(self, text=label).grid(row=row, column=0, sticky="w")
            entry = tk.Entry(self)
            entry.insert(0, self.profile[key])
            entry.grid(row=row, column=1)
            self.entries[key] = entry

        tk.Button(self, text="Сохранить", command=self.save).grid(row=len(fields), columnspan=2)

    def save(self):
        for key, entry in self.entries.items():
            self.profile[key] = entry.get()
        self.parent.profile_manager.add_profile(self.profile)
        self.parent.update_list()
        self.destroy()

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.profile_manager = ProfileManager()
        
        self.title("IP Manager")
        self.geometry("600x500")

        # Список профилей
        self.listbox = tk.Listbox(self)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Кнопки
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Добавить", command=self.add_profile).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Удалить", command=self.delete_profile).pack(side=tk.LEFT)  # Новая кнопка
        tk.Button(btn_frame, text="Показать команды", command=self.show_commands).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Создать файл для запуска", command=self.create_bat).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Запуск(изменить IP)", command=self.run_bat).pack(side=tk.LEFT)

        self.update_list()

    def update_list(self):
        self.listbox.delete(0, tk.END)
        for profile in self.profile_manager.profiles:
            self.listbox.insert(tk.END, profile["name"])

    def add_profile(self):
        ProfileSettingsWindow(self)

    def get_selected_profile(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Ошибка", "Выберите профиль!")
            return None
        return self.profile_manager.profiles[selection[0]]

    def delete_profile(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Ошибка", "Выберите профиль для удаления!")
            return
        
        index = selection[0]
        del self.profile_manager.profiles[index]
        self.profile_manager.save_profiles()
        self.update_list()

    def show_commands(self):
        profile = self.get_selected_profile()
        if not profile: return

        commands = [
            f'netsh interface ip set address "{profile["interface"]}" static {profile["ip"]} {profile["mask"]} {profile["gateway"]}',
            f'netsh interface ip set dns "{profile["interface"]}" static {profile["dns1"]}',
            f'netsh interface ip add dns "{profile["interface"]}" {profile["dns2"]} index=2'
        ]

        messagebox.showinfo(
            "Команды для применения", 
            "Скопируйте эти команды и запустите от имени администратора:\n\n" + 
            "\n".join(commands)
        )

    def run_bat(self):
        """Запускает BAT-файл с правами администратора"""
        profile = self.get_selected_profile()
        if not profile: 
            return

        script_dir = os.path.dirname(os.path.abspath(__file__))
        bat_filename = f"{profile['name']}.bat"
        bat_path = os.path.join(script_dir, bat_filename)

        if not os.path.exists(bat_path):
            messagebox.showerror("Ошибка", "BAT-файл не найден! Создайте его сначала.")
            return

        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas", 
                "cmd.exe", 
                f"/C \"{bat_path}\"", 
                None, 
                1
            )
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось запустить файл: {str(e)}")

    def create_bat(self):
        profile = self.get_selected_profile()
        if not profile: 
            return

        script_dir = os.path.dirname(os.path.abspath(__file__))
        bat_filename = f"{profile['name']}.bat"
        bat_path = os.path.join(script_dir, bat_filename)

        bat_content = f"""@echo off
echo Запрос прав администратора...
netsh interface ip set address "{profile['interface']}" static {profile['ip']} {profile['mask']} {profile['gateway']}
netsh interface ip set dns "{profile['interface']}" static {profile['dns1']}
netsh interface ip add dns "{profile['interface']}" {profile['dns2']} index=2
echo Настройки применены успешно!
pause
"""

        try:
            with open(bat_path, "w") as f:
                f.write(bat_content)
            messagebox.showinfo("Готово", f"Файл сохранен в:\n{bat_path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать файл:\n{str(e)}")

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
