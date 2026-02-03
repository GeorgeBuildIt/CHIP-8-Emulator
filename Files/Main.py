import pygame
import tkinter as tk
from tkinter import messagebox, colorchooser
import os
import sys
from Chip8_Emulator import Chip8
import SettingsManager as sm # Merged DB logic into this

SCALE = 12
SCREEN_WIDTH = 64 * SCALE
SCREEN_HEIGHT = 32 * SCALE

#--------HELPERS-----------#
def hex_to_rgb(hex_col):
    hex_col = hex_col.lstrip('#')
    return tuple(int(hex_col[i:i+2], 16) for i in (0, 2, 4))

#-----------GAME LOOP----------#
def main(chip8_instance, config):
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(f"CHIP-8 | Profile: {config['name']}")

    # Apply Configuration
    BG_COLOR = hex_to_rgb(config['bg_color'])
    FG_COLOR = hex_to_rgb(config['fg_color'])
    IPS = config['ips']
    CRT = bool(config['crt_enabled'])
    chip8_instance.bg_colour = BG_COLOR

    pygame.mixer.init()
    beep = pygame.mixer.Sound(buffer=bytes([128] * 441))
    clock = pygame.time.Clock()
    accumulator = 0.0
    
    mapping = {
        pygame.K_1: 0x1, pygame.K_2: 0x2, pygame.K_3: 0x3, pygame.K_4: 0xC,
        pygame.K_q: 0x4, pygame.K_w: 0x5, pygame.K_e: 0x6, pygame.K_r: 0xD,
        pygame.K_a: 0x7, pygame.K_s: 0x8, pygame.K_d: 0x9, pygame.K_f: 0xE,
        pygame.K_z: 0xA, pygame.K_x: 0x0, pygame.K_c: 0xB, pygame.K_v: 0xF
    }

    hue = 0 # Track current color position
    RAINBOW = bool(config.get('rainbow_enabled', 0))

    running = True
    saved_state = None
    paused = False
    
    while running:
        dt = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                mods = pygame.key.get_mods()
                is_ctrl = (mods & pygame.KMOD_CTRL)
                
                # RESET HOTKEY (Ctrl + R)
                if event.key == pygame.K_r and is_ctrl:
                    if hasattr(chip8_instance, 'current_rom_path'):
                        path = chip8_instance.current_rom_path
                        chip8_instance.__init__() 
                        chip8_instance.load_rom(path)
                        print("Emulator Reset")
                    continue
                
                # QUICK SAVE (Ctrl + S)
                elif event.key == pygame.K_s and is_ctrl:
                    saved_state = chip8_instance.get_snapshot()
                    print("Quick Save Created!")
                
                # QUICK LOAD (Ctrl + L)
                elif event.key == pygame.K_l and is_ctrl:
                    if saved_state:
                        chip8_instance.load_snapshot(saved_state)
                        print("Quick Save Loaded!")
                    
                elif event.key == pygame.K_p and is_ctrl:
                    paused = not paused
                    caption = f"CHIP-8 | Profile: {config['name']}"
                    pygame.display.set_caption(caption + (" [PAUSED]" if paused else ""))
                    continue
                
                # Standard Keypad
                if event.key in mapping and not is_ctrl:
                    chip8_instance.keypad[mapping[event.key]] = 1
            
            if event.type == pygame.KEYUP:
                if event.key in mapping:
                    chip8_instance.keypad[mapping[event.key]] = 0

        # Time Step Accumulator
        if not paused:
            accumulator += dt
            while accumulator >= (1.0 / 60.0):
                for _ in range(IPS // 60):
                    chip8_instance.cycle()
                chip8_instance.update_timers()
                accumulator -= (1.0 / 60.0)
        
        current_fg = FG_COLOR
        if RAINBOW:
            hue = (hue + 2) % 360 # Speed of color change
            rainbow_color = pygame.Color(0)
            rainbow_color.hsla = (hue, 100, 50, 100)
            current_fg = (rainbow_color.r, rainbow_color.g, rainbow_color.b)

        # Rendering
        screen.fill(BG_COLOR)
        chip8_instance.draw(screen, SCALE, BG_COLOR, current_fg, CRT)
        pygame.display.flip()

        # Audio
        if config["audio"] == 1 and not paused:
            if chip8_instance.sound_timer > 0: beep.play()
            else: beep.stop()

    pygame.quit()

#------------LOAD ROM LOGIC-----------#
def load_rom_wrapper(chip8_instance, full_path, root):
    def wrap():
        try:
            chip8_instance.load_rom(full_path)
            root.selected_config = sm.get_rom_settings(full_path) #Load settings for this ROM
            root.game_selected = True
            root.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Could not load ROM: {e}")
    return wrap

def set_rom_profile(rom_path, profile_name):
    sm.save_rom_profile_link(rom_path, profile_name)
    messagebox.showinfo("Updated", f"Assigned '{profile_name}' to this ROM.")

#--------------SETTINGS EDITOR--------------#
def open_settings_editor(root, refresh_callback):
    editor = tk.Toplevel(root)
    editor.title("Profile Manager")
    editor.geometry("350x550")
    
    #-----CREATE/EDIT SECTION------
    tk.Label(editor, text="CREATE OR EDIT PROFILE", font=("Arial", 10, "bold")).pack(pady=10)
    
    tk.Label(editor, text="Profile Name:").pack()
    name_var = tk.StringVar(value="New Profile")
    tk.Entry(editor, textvariable=name_var).pack(pady=5)

    bg_var = tk.StringVar(value="#0a140a")
    fg_var = tk.StringVar(value="#00ff00")

    def pick_color(var, btn):
        from tkinter import colorchooser
        color = colorchooser.askcolor()[1]
        if color:
            var.set(color)
            btn.config(bg=color)

    btn_bg = tk.Button(editor, text="Pick Background", bg=bg_var.get(), command=lambda: pick_color(bg_var, btn_bg))
    btn_bg.pack(pady=2)
    btn_fg = tk.Button(editor, text="Pick Foreground", bg=fg_var.get(), command=lambda: pick_color(fg_var, btn_fg))
    btn_fg.pack(pady=2)

    crt_var = tk.BooleanVar(value=True)
    tk.Checkbutton(editor, text="Enable CRT Ghosting", variable=crt_var).pack(pady=5)

    tk.Label(editor, text="Speed (IPS):").pack()
    ips_var = tk.IntVar(value=700)
    tk.Scale(editor, from_=100, to=3000, orient="horizontal", variable=ips_var).pack(fill="x", padx=20)

    audio_var = tk.BooleanVar(value=True)
    tk.Checkbutton(editor, text="Enable Audio", variable=audio_var).pack(pady=5)

    # Inside open_settings_editor function
    rainbow_var = tk.BooleanVar(value=False)
    tk.Checkbutton(editor, text="Rainbow Mode", variable=rainbow_var).pack(pady=5)

    # Update the save button command to include rainbow_var.get()
    def save():
        sm.save_profile(name_var.get(), bg_var.get(), fg_var.get(), 
                        crt_var.get(), ips_var.get(), audio_var.get(), rainbow_var.get())
        messagebox.showinfo("Success", "Profile saved!")
        refresh_callback()
        editor.destroy()

    tk.Button(editor, text="SAVE PROFILE", command=save, bg="#ccffcc", font=("Arial", 9, "bold")).pack(pady=15)

    #----DELETE SECTION-------
    tk.Frame(editor, height=2, bd=1, relief="sunken").pack(fill="x", pady=10, padx=10)
    tk.Label(editor, text="DELETE PROFILE", font=("Arial", 10, "bold"), fg="red").pack()

    profiles = sm.get_profiles()
    profile_names = [p for p in profiles.keys() if p != "Default"]
    
    if profile_names:
        delete_var = tk.StringVar(value=profile_names[0])
        del_menu = tk.OptionMenu(editor, delete_var, *profile_names)
        del_menu.pack(pady=5)

        def confirm_delete():
            target = delete_var.get()
            if messagebox.askyesno("Confirm", f"Are you sure you want to delete '{target}'?\nROMs using this will revert to Default."):
                sm.delete_profile(target)
                refresh_callback()
                editor.destroy()

        tk.Button(editor, text="DELETE SELECTED", command=confirm_delete, bg="#ffcccc").pack(pady=5)
    else:
        tk.Label(editor, text="No custom profiles to delete", fg="grey").pack()

#-----------ROM SELECTION SCREEN----------#
def create_rom_row(parent, filename, path, chip8, root, favorites, profile_options):
    frame = tk.Frame(parent)
    frame.pack(fill="x", padx=10, pady=2)
    
    is_fav = path in favorites
    fav_text = "★" if is_fav else "☆"
    fav_color = "orange" if is_fav else "black"
    
    # Profile Dropdown
    current_setting = sm.get_rom_settings(path)["name"]
    var = tk.StringVar(value=current_setting)

    dropdown = tk.OptionMenu(frame, var, *profile_options, command=lambda val, p=path: set_rom_profile(p, val))
    dropdown.config(width=10)
    dropdown.pack(side="right")
    
    # Favorite Button
    # Note: We reload the screen by returning "RELOAD" so we don't nest mainloops
    fav_btn = tk.Button(frame, text=fav_text, fg=fav_color, width=3, 
                        command=lambda: [sm.toggle_favorite(path), root.event_generate("<<ReloadUI>>")])
    fav_btn.pack(side="left")
    
    #ROM Load Button
    btn = tk.Button(frame, text=filename, anchor="w", 
                    command=load_rom_wrapper(chip8, path, root))
    btn.pack(side="left", fill="x", expand=True)

def load_rom_screen(chip8_instance):
    sm.init_db()
    
    root = tk.Tk()
    root.title("CHIP-8 Library")
    root.geometry("450x600")
    
    root.game_selected = False
    root.selected_config = None

    #------REFRESH LOGIC------
    def build_ui():
        for widget in container.winfo_children():
            widget.destroy()

        # Canvas Setup
        canvas = tk.Canvas(container)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        #Mousewheel
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        #Data Loading
        favorites = sm.get_favorites()
        profile_options = list(sm.get_profiles().keys())

        #FAVORITES SECTION
        if favorites:
            tk.Label(scrollable_frame, text="FAVORITES", font=("Arial", 12, "bold"), fg="orange").pack(pady=(10, 2))
            for path in favorites:
                if os.path.exists(path):
                    filename = os.path.basename(path)
                    create_rom_row(scrollable_frame, filename, path, chip8_instance, root, favorites, profile_options)

        #FOLDER SCANNING
        rom_folder = "ROMS"
        if not os.path.exists(rom_folder): os.makedirs(rom_folder)
        
        found_any = False
        for item in sorted(os.listdir(rom_folder)):
            dir_path = os.path.join(rom_folder, item)
            
            if os.path.isdir(dir_path):
                files = [f for f in os.listdir(dir_path) if f.endswith(".ch8")]
                if files:
                    found_any = True
                    tk.Label(scrollable_frame, text=item.upper(), font=("Arial", 10, "bold"), fg="blue").pack(pady=(10, 2))
                    for file in sorted(files):
                        path = os.path.join(dir_path, file)
                        create_rom_row(scrollable_frame, file, path, chip8_instance, root, favorites, profile_options)
            
            elif item.endswith(".ch8"):
                found_any = True
                path = os.path.join(rom_folder, item)
                create_rom_row(scrollable_frame, item, path, chip8_instance, root, favorites, profile_options)
        
        if not found_any and not favorites:
             tk.Label(scrollable_frame, text="No ROMs found in /ROMS").pack(pady=20)

    #-----MENU BAR-------
    menubar = tk.Menu(root)
    root.config(menu=menubar)
    settings_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Settings", menu=settings_menu)
    
    #Passing build_ui as callback to refresh dropdowns after saving
    settings_menu.add_command(label="Profile Settings", command=lambda: open_settings_editor(root, build_ui))

    container = tk.Frame(root)
    container.pack(fill="both", expand=True)

    #Event listener to reload UI (when favorite is clicked)
    root.bind("<<ReloadUI>>", lambda e: build_ui())
    
    build_ui() #Initial build

    #Exit logic
    def on_close():
        root.destroy()
        sys.exit()
    root.protocol("WM_DELETE_WINDOW", on_close)
    
    root.mainloop()
    
    #Return the config found by the wrapper
    return root.selected_config

# --- MAIN ENTRY POINT ---
if __name__ == "__main__":
    while True:
        chip8 = Chip8() 
        config = load_rom_screen(chip8)
        
        if config:
            main(chip8, config)