import os
import subprocess
import customtkinter as ctk
from tkinter import filedialog
import json

# --- AESTHETIC STYLING CONSTANTS ---
BG_ABYSS = "#09090b"          # Extremely dark background
CARD_BG = "#13131a"           # Slightly lighter for floating cards
BORDER_COLOR = "#272736"      # Subtle card borders
CYAN_NEON = "#00f0ff"         # Module 1 / Primary Accent
CRIMSON_NEON = "#ff0055"      # Module 2 / Secondary Accent
MUTED_TEXT = "#8a8a9d"        # Subtitles and muted info
WHITE_TEXT = "#ffffff"        # Main readable text
SUCCESS_GREEN = "#00ff66"     # Console success
FONT_MAIN = ("Segoe UI", 13)  # Standard clean sans-serif
FONT_TITLE = ("Segoe UI Black", 22, "bold")
FONT_MONO = ("Monospace", 11) # Terminal/Tech font

ctk.set_appearance_mode("dark")

CONFIG_FILE = "z0n_launcher_favorites.json"

class GPULauncher(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("z0n // OVERRIDE PROTOCOL")
        self.geometry("900x950")
        self.resizable(False, False)
        self.configure(fg_color=BG_ABYSS)

        self.favorites = self.load_favorites()
        self.selected_app = self.favorites[0] if self.favorites else None

        # --- HEADER ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(30, 15), fill="x", padx=40)
        
        self.title_label = ctk.CTkLabel(self.header_frame, text="z0n // GPU_OVERRIDE", font=FONT_TITLE, text_color=WHITE_TEXT)
        self.title_label.pack(side="left")
        
        self.status_label = ctk.CTkLabel(self.header_frame, text="[ SYSTEM ONLINE ]", font=("Monospace", 12, "bold"), text_color=SUCCESS_GREEN)
        self.status_label.pack(side="right", pady=5)

        # ==========================================
        # MODULE 1: GUI BINARY (CYAN CARD)
        # ==========================================
        self.gui_module = ctk.CTkFrame(self, fg_color=CARD_BG, border_width=1, border_color=BORDER_COLOR, corner_radius=12)
        self.gui_module.pack(pady=10, padx=40, fill="x")

        self.gui_title = ctk.CTkLabel(self.gui_module, text="[01] GUI BINARY EXECUTION", font=("Monospace", 13, "bold"), text_color=CYAN_NEON)
        self.gui_title.pack(pady=(15, 5), anchor="w", padx=20)

        self.app_row = ctk.CTkFrame(self.gui_module, fg_color="transparent")
        self.app_row.pack(fill="x", padx=15, pady=(5, 20))

        combo_values = self.favorites if self.favorites else ["None Selected"]
        self.app_combo = ctk.CTkComboBox(self.app_row, values=combo_values, width=420, height=35, command=self.on_combo_select,
                                         fg_color=BG_ABYSS, border_color=BORDER_COLOR, text_color=WHITE_TEXT, font=FONT_MAIN,
                                         button_color=BORDER_COLOR, button_hover_color="#3a3a4d")
        self.app_combo.pack(side="left", padx=5)
        if self.selected_app:
            self.app_combo.set(self.selected_app)

        self.browse_btn = ctk.CTkButton(self.app_row, text="BROWSE", width=100, height=35, command=self.browse_app, 
                                        fg_color=BG_ABYSS, border_width=1, border_color=BORDER_COLOR, hover_color="#222230", font=FONT_MAIN)
        self.browse_btn.pack(side="left", padx=5)

        self.launch_gui_btn = ctk.CTkButton(self.app_row, text="LAUNCH BINARY", height=35, font=("Segoe UI", 12, "bold"), 
                                            command=self.launch_gui, fg_color=CYAN_NEON, text_color="#000000", hover_color="#00c4d1")
        self.launch_gui_btn.pack(side="right", padx=5, fill="x", expand=True)

        # ==========================================
        # MODULE 2: RAW TERMINAL (CRIMSON CARD)
        # ==========================================
        self.cli_module = ctk.CTkFrame(self, fg_color=CARD_BG, border_width=1, border_color=BORDER_COLOR, corner_radius=12)
        self.cli_module.pack(pady=10, padx=40, fill="x")

        self.cli_title = ctk.CTkLabel(self.cli_module, text="[02] TERMINAL PAYLOAD", font=("Monospace", 13, "bold"), text_color=CRIMSON_NEON)
        self.cli_title.pack(pady=(15, 5), anchor="w", padx=20)

        self.cmd_row = ctk.CTkFrame(self.cli_module, fg_color="transparent")
        self.cmd_row.pack(fill="x", padx=15, pady=(5, 20))

        self.cmd_entry = ctk.CTkEntry(self.cmd_row, placeholder_text="Enter raw command (e.g., hashcat -I)", width=530, height=35,
                                      fg_color=BG_ABYSS, border_color=BORDER_COLOR, text_color=CRIMSON_NEON, font=FONT_MONO,
                                      placeholder_text_color=MUTED_TEXT)
        self.cmd_entry.pack(side="left", padx=5)

        self.launch_cmd_btn = ctk.CTkButton(self.cmd_row, text="OPEN TERMINAL", height=35, font=("Segoe UI", 12, "bold"), 
                                            command=self.launch_cmd, fg_color=CRIMSON_NEON, text_color="#ffffff", hover_color="#cc0044")
        self.launch_cmd_btn.pack(side="right", padx=5, fill="x", expand=True)

        # ==========================================
        # HARDWARE OPTIONS (SPLIT CARDS)
        # ==========================================
        self.options_container = ctk.CTkFrame(self, fg_color="transparent")
        self.options_container.pack(pady=10, padx=40, fill="x")

        self.gpu_var = ctk.StringVar(value="nvidia")
        
        # Engine Card
        self.gpu_frame = ctk.CTkFrame(self.options_container, fg_color=CARD_BG, border_width=1, border_color=BORDER_COLOR, corner_radius=12)
        self.gpu_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.gpu_label = ctk.CTkLabel(self.gpu_frame, text="// RENDERING ENGINE", font=("Monospace", 12, "bold"), text_color=MUTED_TEXT)
        self.gpu_label.pack(pady=(15, 10), anchor="w", padx=20)

        self.radio_nvidia = ctk.CTkRadioButton(self.gpu_frame, text="NVIDIA RTX 5060 (Dedicated)", variable=self.gpu_var, value="nvidia",
                                               font=FONT_MAIN, text_color=WHITE_TEXT, fg_color=CYAN_NEON, border_color=CYAN_NEON, hover_color="#00c4d1")
        self.radio_nvidia.pack(pady=(0, 10), padx=25, anchor="w")

        self.radio_igpu = ctk.CTkRadioButton(self.gpu_frame, text="AMD Radeon (Integrated)", variable=self.gpu_var, value="integrated",
                                             font=FONT_MAIN, text_color=MUTED_TEXT, fg_color=MUTED_TEXT, border_color=MUTED_TEXT, hover_color="#a0a0b5")
        self.radio_igpu.pack(pady=(0, 20), padx=25, anchor="w")

        # Flags Card
        self.exec_frame = ctk.CTkFrame(self.options_container, fg_color=CARD_BG, border_width=1, border_color=BORDER_COLOR, corner_radius=12)
        self.exec_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))

        self.exec_label = ctk.CTkLabel(self.exec_frame, text="// GLOBAL FLAGS", font=("Monospace", 12, "bold"), text_color=MUTED_TEXT)
        self.exec_label.pack(pady=(15, 10), anchor="w", padx=20)

        self.suppress_var = ctk.BooleanVar(value=True)
        self.suppress_check = ctk.CTkCheckBox(self.exec_frame, text="Suppress GTK Warnings", variable=self.suppress_var,
                                              font=FONT_MAIN, text_color=WHITE_TEXT, fg_color=CYAN_NEON, border_color=CYAN_NEON, hover_color="#00c4d1")
        self.suppress_check.pack(pady=(0, 20), padx=25, anchor="w")

        # ==========================================
        # TELEMETRY DASHBOARD (WIDE CARD)
        # ==========================================
        self.telemetry_frame = ctk.CTkFrame(self, fg_color=CARD_BG, border_width=1, border_color=BORDER_COLOR, corner_radius=12)
        self.telemetry_frame.pack(pady=10, padx=40, fill="x")

        self.telemetry_label = ctk.CTkLabel(self.telemetry_frame, text="[ TELEMETRY ] CORE_MONITOR", font=("Monospace", 12, "bold"), text_color=MUTED_TEXT)
        self.telemetry_label.pack(pady=(15, 10), anchor="w", padx=20)

        # AMD Row
        self.amd_row = ctk.CTkFrame(self.telemetry_frame, fg_color="transparent")
        self.amd_row.pack(fill="x", padx=20)
        self.amd_label = ctk.CTkLabel(self.amd_row, text="iGPU // AMD 780M", font=FONT_MONO, text_color=WHITE_TEXT)
        self.amd_label.pack(side="left")
        self.amd_pct = ctk.CTkLabel(self.amd_row, text="0%", font=FONT_MONO, text_color=CYAN_NEON)
        self.amd_pct.pack(side="right")
        self.amd_gauge = ctk.CTkProgressBar(self.telemetry_frame, progress_color=CYAN_NEON, fg_color=BG_ABYSS, height=12, corner_radius=6)
        self.amd_gauge.pack(fill="x", padx=20, pady=(2, 15))
        self.amd_gauge.set(0)

        # NVIDIA Row
        self.nv_row = ctk.CTkFrame(self.telemetry_frame, fg_color="transparent")
        self.nv_row.pack(fill="x", padx=20)
        self.nv_label = ctk.CTkLabel(self.nv_row, text="dGPU // RTX 5060", font=FONT_MONO, text_color=WHITE_TEXT)
        self.nv_label.pack(side="left")
        self.nv_pct = ctk.CTkLabel(self.nv_row, text="0%", font=FONT_MONO, text_color=CYAN_NEON)
        self.nv_pct.pack(side="right")
        self.nv_gauge = ctk.CTkProgressBar(self.telemetry_frame, progress_color=CYAN_NEON, fg_color=BG_ABYSS, height=12, corner_radius=6)
        self.nv_gauge.pack(fill="x", padx=20, pady=(2, 20))
        self.nv_gauge.set(0)

        # ==========================================
        # STATUS CONSOLE
        # ==========================================
        self.console = ctk.CTkTextbox(self, height=110, font=FONT_MONO, text_color=CYAN_NEON, fg_color="#050508", 
                                      border_width=1, border_color=BORDER_COLOR, corner_radius=12)
        self.console.pack(padx=40, pady=(10, 20), fill="both", expand=True)
        self.console.insert("0.0", "> SYS.CORE INITIATED\n> WAITING FOR USER PROTOCOL...\n")
        self.console.configure(state="disabled")

        self.update_telemetry()

    def log(self, message, is_error=False):
        self.console.configure(state="normal")
        color = CRIMSON_NEON if is_error else SUCCESS_GREEN
        # Insert text
        self.console.insert("end", f"> {message}\n")
        self.console.see("end")
        self.console.configure(state="disabled")

    def load_favorites(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_favorites(self, filepath):
        if filepath not in self.favorites:
            self.favorites.insert(0, filepath)
            if len(self.favorites) > 10:
                self.favorites.pop()
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.favorites, f)
            self.app_combo.configure(values=self.favorites)
            self.app_combo.set(filepath)

    def on_combo_select(self, choice):
        if choice != "None Selected":
            self.selected_app = choice

    def browse_app(self):
        # Trigger the system's native modern file manager
        try:
            # --file-selection: Opens the picker
            # --title: Custom header
            # --filename: Starting directory
            cmd = [
                "zenity", 
                "--file-selection", 
                "--title=z0n // SELECT TARGET BINARY", 
                "--filename=/usr/bin/",
                "--modal"
            ]
            
            # Execute and capture the path
            filepath = subprocess.check_output(cmd).decode("utf-8").strip()
            
            if filepath:
                self.selected_app = filepath
                self.save_favorites(filepath)
                self.log(f"TARGET LOCKED: {filepath}")
                
        except subprocess.CalledProcessError:
            # This triggers if the user clicks 'Cancel' or closes the window
            self.log("BROWSE OPERAION ABORTED", is_error=True)
        except FileNotFoundError:
            # Fallback if zenity isn't installed
            self.log("ERR: zenity not found. Run 'sudo apt install zenity'", is_error=True)

    def get_nvidia_usage(self):
        try:
            result = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"], 
                encoding="utf-8"
            )
            return int(result.strip())
        except:
            return 0

    def get_amd_usage(self):
        paths = ["/sys/class/drm/card0/device/gpu_busy_percent", 
                 "/sys/class/drm/card1/device/gpu_busy_percent"]
        for path in paths:
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        return int(f.read().strip())
                except:
                    continue
        return 0

    def update_telemetry(self):
        nv_usage = self.get_nvidia_usage()
        amd_usage = self.get_amd_usage()

        self.nv_pct.configure(text=f"{nv_usage}%")
        self.amd_pct.configure(text=f"{amd_usage}%")

        self.nv_gauge.set(nv_usage / 100.0)
        self.amd_gauge.set(amd_usage / 100.0)

        # Shift to warning colors under load
        nv_color = CRIMSON_NEON if nv_usage > 85 else CYAN_NEON
        amd_color = CRIMSON_NEON if amd_usage > 85 else CYAN_NEON
        
        self.nv_gauge.configure(progress_color=nv_color)
        self.nv_pct.configure(text_color=nv_color)
        
        self.amd_gauge.configure(progress_color=amd_color)
        self.amd_pct.configure(text_color=amd_color)

        self.after(1000, self.update_telemetry)

    def get_env_prefix(self):
        if self.gpu_var.get() == "nvidia":
            return "__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia __VK_LAYER_NV_optimus=NVIDIA_only"
        return ""

    def launch_gui(self):
        if not self.selected_app or self.selected_app == "None Selected":
            self.log("ERR: NO BINARY SELECTED IN [01]", is_error=True)
            return

        env_vars = self.get_env_prefix()
        target = f"'{self.selected_app}'"
        command = f"{env_vars} {target}" if env_vars else target
        
        gpu_status = "RTX 5060" if env_vars else "AMD 780M"
        stderr_target = subprocess.DEVNULL if self.suppress_var.get() else None

        self.log(f"LAUNCH [01] -> {os.path.basename(self.selected_app)} ON {gpu_status}")
        try:
            subprocess.Popen(command, shell=True, executable='/bin/bash', stderr=stderr_target)
            self.log(f"SUCCESS: THREAD SPAWNED SILENTLY.")
        except Exception as e:
            self.log(f"FATAL: {str(e)}", is_error=True)

    def launch_cmd(self):
        raw_cmd = self.cmd_entry.get().strip()
        if not raw_cmd:
            self.log("ERR: NO PAYLOAD PROVIDED IN [02]", is_error=True)
            return

        env_vars = self.get_env_prefix()
        inner_cmd = f"{env_vars} {raw_cmd}" if env_vars else raw_cmd
        gpu_status = "RTX 5060" if env_vars else "AMD 780M"

        terminal_cmd = f"x-terminal-emulator -e bash -c \"{inner_cmd}; echo; echo '>> SESSION TERMINATED'; exec bash\""

        self.log(f"LAUNCH [02] -> TERMINAL ON {gpu_status}")
        self.log(f"PAYLOAD -> {raw_cmd}")
        
        try:
            subprocess.Popen(terminal_cmd, shell=True, executable='/bin/bash')
            self.log(f"SUCCESS: TERMINAL HOOK ESTABLISHED.")
        except Exception as e:
            self.log(f"FATAL: {str(e)}", is_error=True)

if __name__ == "__main__":
    app = GPULauncher()
    app.mainloop()