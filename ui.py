import customtkinter as ctk
import tkinter as tk
from datetime import datetime
import threading

from edith import EdithBrain 

brain = EdithBrain()

#------------------------------
# Constant Values
#------------------------------


# -----------------------------
# APP CONFIG
# -----------------------------
ctk.set_default_color_theme("green")
ctk.set_appearance_mode("dark")

app = ctk.CTk()
app.title("EDITH — AI Assistant")
app.geometry("1100x720")
app.minsize(900, 600)

# -----------------------------
# GLOBAL UI STATE
# -----------------------------

ZOOM_MIN = 1.0
ZOOM_MAX = 5.0
ZOOM_STEP = 0.1
DEFAULT_UI_SIZE = 1.7

user_name = "You"

ui_scale = DEFAULT_UI_SIZE  
settings_visible = False
mic_active = False

BASE_FONTS = {
    "title": 26,
    "status": 14,
    "chat": 16,
    "input": 15,
    "settings_title": 18,
    "settings_label": 14,
    "icon": 20,
    "segmented": 14,
    "send_button": 20,
}

# -----------------------------
# MAIN GRID
# -----------------------------
app.grid_columnconfigure(0, weight=1)
app.grid_rowconfigure(1, weight=1)

# -----------------------------
# HEADER
# -----------------------------
header = ctk.CTkFrame(app, height=60, corner_radius=0)
header.grid(row=0, column=0, sticky="ew")
header.grid_columnconfigure(1, weight=1)

title_label = ctk.CTkLabel(
    header,
    text="EDITH",
    font=("Segoe UI", int(BASE_FONTS["title"] * ui_scale), "bold")
)
title_label.grid(row=0, column=0, padx=24, pady=10)

status_label = ctk.CTkLabel(
    header,
    text="● Ready",
    font=("Segoe UI", int(BASE_FONTS["status"] * ui_scale)),
    text_color="green"
)
status_label.grid(row=0, column=1, sticky="e", padx=12)

mic_status_label = ctk.CTkLabel(
    header,
    text="🎙 OFF",
    font=("Segoe UI", int(BASE_FONTS["status"] * ui_scale)),
    text_color="#ef4444"  # red
)
mic_status_label.grid(row=0, column=2, sticky="e", padx=8)

settings_btn = ctk.CTkButton(
    header,
    text="⚙",
    font=("Segoe UI Symbol", int(BASE_FONTS["icon"] * ui_scale)),
    width=50,
    height=50,
    corner_radius=20,
    command=lambda: toggle_settings()
)
settings_btn.grid(row=0, column=3, padx=18)

# -----------------------------
# CONTENT AREA
# -----------------------------
content = ctk.CTkFrame(app)
content.grid(row=1, column=0, sticky="nsew", padx=12, pady=12)
content.grid_columnconfigure(0, weight=1)
content.grid_rowconfigure(0, weight=1)

# -----------------------------
# CHAT AREA
# -----------------------------
chat_frame = ctk.CTkFrame(content, corner_radius=14)
chat_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
chat_frame.grid_rowconfigure(0, weight=1)
chat_frame.grid_columnconfigure(0, weight=1)

chat_box = ctk.CTkTextbox(
    chat_frame,
    wrap="word",
    font=("Consolas", int(BASE_FONTS["chat"] * ui_scale))
)

chat_box.tag_config("user_name", foreground="#3b82f6")    # blue
chat_box.tag_config("edith_name", foreground="#22c55e")   # green

chat_box.tag_config("user_msg", justify="right")
chat_box.tag_config("edith_msg", justify="left")

chat_box.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
chat_box.configure(state="disabled")

# -----------------------------
# SETTINGS PANEL (INLINE)
# -----------------------------
settings_panel = ctk.CTkFrame(content, width=300, corner_radius=14)
settings_panel.grid(row=0, column=1, sticky="ns")
settings_panel.grid_propagate(False)
settings_panel.grid_remove()

settings_title = ctk.CTkLabel(
    settings_panel,
    text="Settings",
    font=("Segoe UI", int(BASE_FONTS["settings_title"] * ui_scale), "bold")
)
settings_title.pack(pady=(18, 12))

# User name ------------------------

username_label = ctk.CTkLabel(
    settings_panel,
    text="Your Name",
    font=("Segoe UI", int(BASE_FONTS["settings_label"] * ui_scale))
)
username_label.pack(pady=(10, 8))

username_entry = ctk.CTkEntry(
    settings_panel,
    placeholder_text="Enter your name",
    font=("Segoe UI", int(BASE_FONTS["input"] * ui_scale)),
    height=int(30 * ui_scale)
)
username_entry.insert(0, user_name)
username_entry.pack(padx=18, pady=(0, 12), fill="x")

# Theme Mode ------------------------

appearance_label = ctk.CTkLabel(
    settings_panel,
    text="Theme",
    font=("Segoe UI", int(BASE_FONTS["settings_label"] * ui_scale))
)
appearance_label.pack(pady=(10, 6))

appearance_switch = ctk.CTkSegmentedButton(
    settings_panel,
    values=["Dark", "Light"],
    font=("Segoe UI", int(BASE_FONTS["segmented"] * ui_scale)),
    command=lambda v: ctk.set_appearance_mode(v.lower())
)
appearance_switch.set("Dark")
appearance_switch.pack(pady=6)

# Zoom Slider ---------------------

zoom_label = ctk.CTkLabel(
    settings_panel,
    text="UI Zoom",
    font=("Segoe UI", int(BASE_FONTS["settings_label"] * ui_scale))
)
zoom_label.pack(pady=(24, 6))

zoom_slider = ctk.CTkSlider(
    settings_panel,
    from_= ZOOM_MIN,
    to= ZOOM_MAX,
    number_of_steps = int((ZOOM_MAX - ZOOM_MIN) / ZOOM_STEP),
    command=lambda v: set_zoom(v)
)
zoom_slider.set(ui_scale)
zoom_slider.pack(padx=18, pady=10, fill="x")

zoom_value_label = ctk.CTkLabel(
    settings_panel,
    text=f"{int(ui_scale * 100)}%",
    font=("Segoe UI", int(BASE_FONTS["settings_label"] * ui_scale))
)
zoom_value_label.pack(pady=(0, 10))

# -----------------------------
# INPUT AREA
# -----------------------------
input_frame = ctk.CTkFrame(app, corner_radius=14)
input_frame.grid(row=2, column=0, sticky="ew", padx=18, pady=14)
input_frame.grid_columnconfigure(0, weight=1)

# Chat Intput Box ----------------------------

entry = ctk.CTkEntry(
    input_frame,
    placeholder_text="Type your message...",
    font=("Segoe UI", int(BASE_FONTS["input"] * ui_scale))
)
entry.grid(row=0, column=0, padx=14, pady=12, sticky="ew")

# Send Msg Button -------------------------------

send_btn = ctk.CTkButton(
    input_frame,
    text="Send",
    width=80,
    height=40,
    corner_radius=20,
    font=("Segoe UI", int(BASE_FONTS["send_button"] * ui_scale)),
    command=lambda: on_send()
)
send_btn.grid(row=0, column=1, padx=14)

# Mic Toggle Button ----------------------------

mic_btn = ctk.CTkButton(
    input_frame,
    text="🎙",
    width=40,
    height=40,
    corner_radius=20,
    font=("Segoe UI", int(BASE_FONTS["icon"] * ui_scale)),
    command=lambda: toggle_mic()
)
mic_btn.grid(row=0, column=2, padx=(6, 6))

# -----------------------------
# UI LOGIC
# -----------------------------
def toggle_settings():
    global settings_visible
    settings_visible = not settings_visible
    if settings_visible:
        settings_panel.grid()
    else:
        settings_panel.grid_remove()

# User Name Logic

def update_username(event=None):
    global user_name
    name = username_entry.get().strip()
    user_name = name if name else "You"

username_entry.bind("<KeyRelease>", update_username)

# Zoom Slider Logic

def set_zoom(value):
    global ui_scale
    ui_scale = float(value)
    apply_zoom()
    zoom_value_label.configure(text=f"{int(ui_scale * 100)}%")

def zoom_in(event=None):
    new_value = min(ui_scale + ZOOM_STEP, ZOOM_MAX)
    zoom_slider.set(new_value)
    set_zoom(new_value)

def zoom_out(event=None):
    new_value = max(ui_scale - ZOOM_STEP, ZOOM_MIN)
    zoom_slider.set(new_value)
    set_zoom(new_value)

def zoom_reset(event=None):
    zoom_slider.set(DEFAULT_UI_SIZE)
    set_zoom(DEFAULT_UI_SIZE)

# Mic Button Logic

def toggle_mic():
    global mic_active
    mic_active = not mic_active

    if mic_active:
        mic_status_label.configure(
            text="🎙 ON",
            text_color="#22c55e"   
        )
        mic_btn.configure(
            fg_color="#22c55e",
            hover_color="#16a34a"
        )
        add_message("Voice command enabled. EDITH is listening.", "assistant")

    else:
        mic_status_label.configure(
            text="🎙 OFF",  
            text_color="#ef4444" 
        )
        mic_btn.configure(
            fg_color="#ef4444",
            hover_color="#dc2626"
        )
        add_message("Voice command disabled.", "assistant")

# UI Zoom Logic -----------------------------

def apply_zoom():
    title_label.configure(font=("Segoe UI", int(BASE_FONTS["title"] * ui_scale), "bold"))
    status_label.configure(font=("Segoe UI", int(BASE_FONTS["status"] * ui_scale)))

    chat_box.configure(font=("Consolas", int(BASE_FONTS["chat"] * ui_scale)))
    entry.configure(font=("Segoe UI", int(BASE_FONTS["input"] * ui_scale)))

    settings_btn.configure(font=("Segoe UI Symbol", int(BASE_FONTS["icon"] * ui_scale)))
    settings_title.configure(font=("Segoe UI", int(BASE_FONTS["settings_title"] * ui_scale), "bold"))

    appearance_label.configure(font=("Segoe UI", int(BASE_FONTS["settings_label"] * ui_scale)))
    appearance_switch.configure(font=("Segoe UI", int(BASE_FONTS["segmented"] * ui_scale)))

    username_label.configure(font=("Segoe UI", int(BASE_FONTS["settings_label"] * ui_scale)))
    username_entry.configure(font=("Segoe UI", int(BASE_FONTS["input"] * ui_scale)))
    username_entry.configure(font=("Segoe UI", int(BASE_FONTS["settings_label"] * ui_scale)), height=int(32 * ui_scale))
    username_entry.pack_configure(padx=int(18 * ui_scale), pady=(0, int(12 * ui_scale)))

    zoom_label.configure(font=("Segoe UI", int(BASE_FONTS["settings_label"] * ui_scale)))
    zoom_value_label.configure(font=("Segoe UI", int(BASE_FONTS["settings_label"] * ui_scale)))

    mic_btn.configure(font=("Segoe UI", int(BASE_FONTS["icon"] * ui_scale)))
    mic_status_label.configure(font=("Segoe UI", int(BASE_FONTS["status"] * ui_scale)))

    send_btn.configure(font=("Segoe UI", int(BASE_FONTS["send_button"] * ui_scale)))

    mic_btn.configure(width=int(40 * ui_scale), height=int(40 * ui_scale))
    send_btn.configure(width=int(80 * ui_scale), height=int(40 * ui_scale))
    settings_btn.configure(width=int(40 * ui_scale), height=int(40 * ui_scale))


# -----------------------------
# CHAT HELPERS
# -----------------------------
def add_message(text, role="assistant"):
    chat_box.configure(state="normal")

    timestamp = datetime.now().strftime("%H:%M")

    if role == "user":
        # Username (blue)
        chat_box.insert(
            "end",
            f"{user_name} [{timestamp}]: ",
            ("user_name", "user_msg")
        )

        # Message text (normal)
        chat_box.insert(
            "end",
            f"{text}\n\n",
            "user_msg"
        )

    else:
        # EDITH name (green)
        chat_box.insert(
            "end",
            f"EDITH [{timestamp}]: ",
            ("edith_name", "edith_msg")
        )

        # Message text (normal)
        chat_box.insert(
            "end",
            f"{text}\n\n",
            "edith_msg"
        )

    chat_box.configure(state="disabled")
    chat_box.see("end")


def on_send():
    text = entry.get().strip()
    if not text:
        return

    entry.delete(0, tk.END)
    add_message(text, "user")

    def run_brain():
        try:
            response = brain.process(text)
        except Exception as e:
            response = f"⚠️ Error: {e}"

        # UI updates must be done on main thread
        app.after(0, lambda: add_message(response, "assistant"))

    # Run AI in background so UI never freezes
    threading.Thread(target=run_brain, daemon=True).start()


entry.bind("<Return>", lambda e: on_send())

#------------------------------
# Keyboard KeyBinds
#-----------------------------

app.bind("<Control-plus>", zoom_in)
app.bind("<Control-minus>", zoom_out)
app.bind("<Control-0>", zoom_reset)

# Linux sometimes uses these instead
app.bind("<Control-equal>", zoom_in)

# -----------------------------
# STARTUP
# -----------------------------
add_message("EDITH initialized. Ready.", "assistant")
app.mainloop()