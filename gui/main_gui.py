import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import os
import sys
import random
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from bestiary_utils import load_zone_data, get_enemy_loot_from_zone_file, get_loot_rarity, format_text_color, ZONE_NAME_COLORS
from enemy import EnemyDatabase
from gui.game_controller import GameController, GamePhase
from player import Player  # Import Player for character creation

# Path to your images (change as needed)
ENEMY_IMAGE_DIR = os.path.join(os.path.dirname(__file__), '../data/assets/Images/enemys')
PLACEHOLDER_IMAGE = os.path.join(ENEMY_IMAGE_DIR, 'placeholder.png')
ZONE_BESTIARY_PATH = os.path.join(os.path.dirname(__file__), '../data/bestiary')

class GameGUI(tk.Tk):
    def __init__(self):
        print("[DEBUG] GameGUI __init__ start")
        super().__init__()
        print("[DEBUG] GameGUI super().__init__ done")
        self.title("Python RPG Main Menu (GUI)")
        self.geometry("800x600")
        self.minsize(640, 480)
        self.configure(bg="#222")
        self.image_label = None
        self.bg_canvas = None
        self.bg_layers = []
        self.bg_layer_imgs = []
        self.bg_anim_index = 0
        self.bg_anim_running = False
        self.controller = GameController()
        self.enemy_db = self.controller.enemy_db
        print("[DEBUG] GameController and enemy_db initialized")
        self.zones_data = load_zone_data(ZONE_BESTIARY_PATH, self.enemy_db)
        print("[DEBUG] zones_data loaded")
        # self.load_menu_bg_layers()  # TEMP: Commented out for debug
        # print("[DEBUG] load_menu_bg_layers done")
        self.create_main_menu()
        print("[DEBUG] create_main_menu done")
        self.bind('<F11>', self.toggle_fullscreen)
        self.bind('<Configure>', self._on_resize)
        self._is_fullscreen = False
        self._current_screen = None  # Track current active screen
        print("[DEBUG] GameGUI __init__ end")

    def load_menu_bg_layers(self):
        print("[DEBUG] load_menu_bg_layers start")
        menu_img_dir = os.path.join(os.path.dirname(__file__), '../data/assets/Images/menu')
        files = [f for f in os.listdir(menu_img_dir) if f.lower().startswith('moddedlayer') and f.lower().endswith('.png')]
        print(f"[DEBUG] Found menu bg files: {files}")
        def sort_key(f):
            parts = f.replace('moddedlayer', '').replace('.png', '').split('_')
            return tuple(int(p) for p in parts if p.isdigit())
        files.sort(key=sort_key)
        self.bg_layers = []
        for f in files:
            try:
                print(f"[DEBUG] Loading image: {f}")
                img = Image.open(os.path.join(menu_img_dir, f)).resize((800, 600))
                self.bg_layers.append(img)
                print(f"[DEBUG] Loaded image: {f}")
            except Exception as e:
                print(f"[ERROR] Failed to load image {f}: {e}")
        self.bg_layer_imgs = [None] * len(self.bg_layers)
        print("[DEBUG] load_menu_bg_layers end")

    def start_bg_animation(self):
        if not self.bg_layers:
            return
        if not self.bg_canvas:
            self.bg_canvas = tk.Canvas(self, highlightthickness=0, bd=0)
            self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.bg_anim_running = True
        self.animate_bg_layer()

    def stop_bg_animation(self):
        self.bg_anim_running = False
        if self.bg_canvas:
            self.bg_canvas.destroy()
            self.bg_canvas = None

    def animate_bg_layer(self):
        if not self.bg_anim_running or not self.bg_layers:
            return
        win_w, win_h = self.winfo_width(), self.winfo_height()
        # Compose all layers up to current index, resize to window size
        base = Image.new('RGBA', (win_w, win_h), (0, 0, 0, 255))
        for i in range(self.bg_anim_index + 1):
            layer = self.bg_layers[i].resize((win_w, win_h))
            base = Image.alpha_composite(base, layer.convert('RGBA'))
        self.bg_layer_imgs[self.bg_anim_index] = ImageTk.PhotoImage(base)
        if hasattr(self, 'bg_canvas') and self.bg_canvas and self.bg_canvas.winfo_exists():
            self.bg_canvas.delete('all')
            self.bg_canvas.create_image(0, 0, anchor='nw', image=self.bg_layer_imgs[self.bg_anim_index])
        self.bg_anim_index = (self.bg_anim_index + 1) % len(self.bg_layers)
        self.after(120, self.animate_bg_layer)

    def _resize_static_background(self):
        """Dedicated method to resize the static background image"""
        if hasattr(self, '_static_bg_img_orig') and hasattr(self, '_static_bg_label') and self._static_bg_label:
            try:
                win_w, win_h = self.winfo_width(), self.winfo_height()
                # Make sure we have valid dimensions
                if win_w > 1 and win_h > 1:
                    img = self._static_bg_img_orig.resize((win_w, win_h))
                    self._static_bg_img = ImageTk.PhotoImage(img)
                    self._static_bg_label.config(image=self._static_bg_img)
                    # Ensure the background covers the entire window
                    self._static_bg_label.place(x=0, y=0, width=win_w, height=win_h)
            except Exception as e:
                print(f"[ERROR] Failed to resize background: {e}")

    def set_static_bg(self, image_name):
        print(f"[DEBUG] set_static_bg called with {image_name}")
        # Remove any existing static bg
        if hasattr(self, '_static_bg_label') and self._static_bg_label:
            self._static_bg_label.destroy()
            self._static_bg_label = None
        # Use the correct folder for CharecterPrep.png and Cavehome.png
        if image_name.lower() == 'cavehome.png':
            img_dir = os.path.join(os.path.dirname(__file__), '../data/assets/Images/Zones')
        elif image_name.lower() == 'charecterprep.png':
            img_dir = os.path.join(os.path.dirname(__file__), '../data/assets/Images/menu')
        else:
            img_dir = os.path.join(os.path.dirname(__file__), '../data/assets/Images/menu')
        img_path = os.path.join(img_dir, image_name)
        if os.path.exists(img_path):
            try:
                print(f"[DEBUG] Loading static bg image: {img_path}")
                img = Image.open(img_path)
                self._static_bg_img_orig = img.copy()
                # Get window dimensions - make sure we have a valid size
                win_w, win_h = max(self.winfo_width(), 800), max(self.winfo_height(), 600)
                img = img.resize((win_w, win_h))
                self._static_bg_img = ImageTk.PhotoImage(img)
                if hasattr(self, '_static_bg_label') and self._static_bg_label:
                    self._static_bg_label.destroy()
                self._static_bg_label = tk.Label(self, image=self._static_bg_img, borderwidth=0)
                self._static_bg_label.place(x=0, y=0, width=win_w, height=win_h)
                self._static_bg_label.lower()
                print(f"[DEBUG] Static bg image loaded: {img_path}")
            except Exception as e:
                print(f"[ERROR] Failed to load static bg image {img_path}: {e}")
                self._static_bg_label = None
        else:
            print(f"[ERROR] Static bg image not found: {img_path}")
            self._static_bg_label = None

    def _on_resize(self, event=None):
        """Master resize handler that calls appropriate screen-specific handlers"""
        # Always resize the background image/canvas first
        # Use a more robust check that always works regardless of screen or fullscreen state
        self._resize_static_background()
        
        # Call the appropriate screen-specific resize handler based on current screen
        if self._current_screen == "main_menu":
            self._resize_main_menu()
        elif self._current_screen == "character_creation":
            self._resize_character_creation()
        elif self._current_screen == "stat_allocation":
            self._resize_stat_allocation()
        elif self._current_screen == "cavehome":
            self._resize_cavehome()
            
        # Resize any open modals
        self._resize_active_modals()
    
    def _resize_main_menu(self):
        """Resize handler for main menu screen"""
        if hasattr(self, '_main_menu_img_orig') and hasattr(self, '_main_menu_img_label') and self._main_menu_img_label:
            win_w, win_h = self.winfo_width(), self.winfo_height()
            img_w = int(win_w * 0.45)
            img_h = int(win_h * 0.85)
            img = self._main_menu_img_orig.resize((img_w, img_h))
            self._main_menu_img = ImageTk.PhotoImage(img)
            self._main_menu_img_label.config(image=self._main_menu_img)
            self._main_menu_img_label.place(x=0, y=0, width=img_w, height=img_h)
        
        # Update title and menu buttons positions (they use relx/rely so they should adapt automatically)
        # However, we can force a refresh if needed by updating their placement
        if hasattr(self, '_main_menu_widgets'):
            for widget in self._main_menu_widgets:
                if hasattr(widget, 'place_info'):
                    place_info = widget.place_info()
                    if 'relx' in place_info and 'rely' in place_info:
                        widget.place(relx=float(place_info['relx']),
                                     rely=float(place_info['rely']),
                                     anchor="center",
                                     relwidth=float(place_info.get('relwidth', 0.18)),
                                     relheight=float(place_info.get('relheight', 0.055)))
    
    def _resize_character_creation(self):
        """Resize handler for character creation screen"""
        # Mostly uses relx/rely, but we can update the gender selection frames
        if hasattr(self, 'male_box') and hasattr(self, 'female_box') and hasattr(self, 'gender_frame'):
            self.gender_frame.place(relx=0.5, rely=0.38, anchor="center")
            # Update the images if needed
            if hasattr(self, 'male_photo') and hasattr(self, 'female_photo'):
                # No need to recreate images unless they need to scale with window size
                pass
    
    def _resize_stat_allocation(self):
        """Resize handler for stat allocation screen"""
        # The stat allocation screen already uses pack geometry manager which is responsive
        # We might just need to ensure the confirm label is properly centered
        if hasattr(self, 'confirm_label') and hasattr(self, 'free_points_var'):
            if self.free_points_var.get() == 0:
                self.confirm_label.place(relx=0.5, rely=0.5, anchor="center")
    
    def _resize_cavehome(self):
        """Resize handler for cavehome screen"""
        if hasattr(self, '_menu_buttons') and self._menu_buttons:
            btn_width = 120
            btn_height = 32
            btn_spacing = 18
            win_w, win_h = self.winfo_width(), self.winfo_height()
            base_x = 24
            base_y = int(win_h * 0.18)
            for i, btn in enumerate(self._menu_buttons):
                btn.place(x=base_x, y=base_y + i * (btn_height + btn_spacing), width=btn_width, height=btn_height)
    
    def _resize_active_modals(self):
        """Resize any active modal windows"""
        # Resize crafting modal if open
        if hasattr(self, '_crafting_modal') and self._crafting_modal and self._crafting_modal.winfo_exists():
            modal = self._crafting_modal
            w, h = int(self.winfo_width()*0.7), int(self.winfo_height()*0.7)
            x, y = self.winfo_rootx()+int(self.winfo_width()*0.15), self.winfo_rooty()+int(self.winfo_height()*0.15)
            modal.geometry(f"{w}x{h}+{x}+{y}")
            # Resize modal children (border, frames)
            for child in modal.winfo_children():
                if hasattr(child, 'place_info'):
                    place_info = child.place_info()
                    if 'relwidth' in place_info and 'relheight' in place_info:
                        child.place_configure(relwidth=float(place_info['relwidth']),
                                             relheight=float(place_info['relheight']))
        
        # Resize storage modal if open
        if hasattr(self, '_storage_modal') and self._storage_modal and self._storage_modal.winfo_exists():
            modal = self._storage_modal
            w, h = int(self.winfo_width()*0.7), int(self.winfo_height()*0.7)
            x, y = self.winfo_rootx()+int(self.winfo_width()*0.15), self.winfo_rooty()+int(self.winfo_height()*0.15)
            modal.geometry(f"{w}x{h}+{x}+{y}")
            
        # Resize zones modal if open
        if hasattr(self, '_zones_modal') and self._zones_modal and self._zones_modal.winfo_exists():
            modal = self._zones_modal
            w, h = int(self.winfo_width()*0.85), int(self.winfo_height()*0.85)
            x, y = self.winfo_rootx()+int(self.winfo_width()*0.075), self.winfo_rooty()+int(self.winfo_height()*0.075)
            modal.geometry(f"{w}x{h}+{x}+{y}")

    def create_main_menu(self):
        print("[DEBUG] create_main_menu start")
        self.set_static_bg('CharecterPrep.png')  # Show static background on main menu
        # self.stop_bg_animation()  # TEMP: Commented out for debug
        # self.start_bg_animation()  # TEMP: Commented out for debug
        for widget in self.winfo_children():
            if widget != getattr(self, '_static_bg_label', None) and widget != getattr(self, 'bg_canvas', None):
                widget.destroy()
        
        # Set current screen for resize handling
        self._current_screen = "main_menu"
        self._main_menu_widgets = []
        # Responsive placement using relx/rely
        title_label = tk.Label(self, text="Main Menu", font=("Arial", 18, "bold"), fg="#fff", bg="#222", bd=0)
        title_label.place(relx=0.62, rely=0.18, anchor="center", relwidth=0.18)
        self._main_menu_widgets.append(title_label)
        menu_items = [
            ("New Game", self.stub_new_game),
            ("Load Game", self.stub_load_game),
            ("About", self.show_about),
            ("Exit", self.quit)
        ]
        menu_item_widgets = []
        for i, (text, cmd) in enumerate(menu_items):
            btn = tk.Button(self, text=text, font=("Arial", 13, "bold"), fg="#fff", bg="#222", activebackground="#ffe066", activeforeground="#222", bd=2, relief="ridge", cursor="hand2", command=cmd)
            btn.place(relx=0.62, rely=0.25 + i*0.07, anchor="center", relwidth=0.18, relheight=0.055)
            menu_item_widgets.append(btn)
            self._main_menu_widgets.append(btn)
        # Responsive background image (left side)
        if hasattr(self, '_main_menu_img_label') and self._main_menu_img_label:
            self._main_menu_img_label.destroy()
        menu_img_path = os.path.join(os.path.dirname(__file__), '../data/assets/Images/menu/main_menu_bg.png')
        if os.path.exists(menu_img_path):
            self._main_menu_img_orig = Image.open(menu_img_path)
            win_w, win_h = self.winfo_width(), self.winfo_height()
            img_w = int(win_w * 0.45)
            img_h = int(win_h * 0.85)
            img = self._main_menu_img_orig.resize((img_w, img_h))
            self._main_menu_img = ImageTk.PhotoImage(img)
            self._main_menu_img_label = tk.Label(self, image=self._main_menu_img, borderwidth=0, highlightthickness=0, bg='')
            self._main_menu_img_label.place(x=0, y=0, width=img_w, height=img_h)
            self._main_menu_img_label.lower()
        else:
            self._main_menu_img_label = None
        def on_resize(event=None):
            win_w, win_h = self.winfo_width(), self.winfo_height()
            # Resize and place background image
            if hasattr(self, '_main_menu_img_orig') and self._main_menu_img_label:
                img_w = int(win_w * 0.45)
                img_h = int(win_h * 0.85)
                img = self._main_menu_img_orig.resize((img_w, img_h))
                self._main_menu_img = ImageTk.PhotoImage(img)
                self._main_menu_img_label.config(image=self._main_menu_img)
                self._main_menu_img_label.place(x=0, y=0, width=img_w, height=img_h)
            # Reposition title and buttons (relx/rely already used, so no manual adjustment needed)
        if hasattr(self, '_main_menu_resize_binding') and self._main_menu_resize_binding:
            self.unbind('<Configure>', self._main_menu_resize_binding)
        self._main_menu_resize_binding = self.bind('<Configure>', on_resize)
        self.after(100, lambda: on_resize(None))
        print("[DEBUG] create_main_menu end")

    def stub_new_game(self):
        # Start character creation flow (GUI stub for now)
        self.stop_bg_animation()  # Stop animation before static bg
        self.controller.start_new_game()
        self.show_character_creation()

    def stub_load_game(self):
        # Load Game: skip character creation/stat allocation, go straight to cavehome
        self.stop_bg_animation()  # Stop animation before static bg
        try:
            self.controller.load_game()  # This should load the player and state
            self.show_cavehome_menu()
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Load Game Failed", f"No save data found or failed to load.\n\n{e}")
            self.create_main_menu()

    def toggle_fullscreen(self, event=None):
        self._is_fullscreen = not getattr(self, '_is_fullscreen', False)
        self.attributes('-fullscreen', self._is_fullscreen)
        
        # Force a resize event to update all elements after toggling fullscreen
        self.update_idletasks()  # Make sure window dimensions are updated
        
        # Force resizing background first - this is crucial when toggling fullscreen
        self._resize_static_background()
        
        # Then call the master resize handler for other elements
        self._on_resize()

    # Removing _bind_bg_resize method as it's no longer needed with the improved approach

    def show_cavehome_menu(self):
        # Remove previous widgets and unbind resize handler if present
        if hasattr(self, '_menu_resize_binding') and self._menu_resize_binding:
            self.unbind('<Configure>', self._menu_resize_binding)
            self._menu_resize_binding = None
        
        # Set current screen for resize handling
        self._current_screen = "cavehome"
        if hasattr(self, '_menu_img_label') and self._menu_img_label:
            self._menu_img_label.destroy()
            self._menu_img_label = None
        if hasattr(self, '_menu_buttons'):
            for btn in self._menu_buttons:
                btn.destroy()
        self._menu_buttons = []
        if hasattr(self, '_menu_btn_frame') and self._menu_btn_frame:
            self._menu_btn_frame.destroy()
            self._menu_btn_frame = None
        for widget in self.winfo_children():
            if widget != self.bg_canvas and widget != getattr(self, '_static_bg_label', None):
                widget.destroy()
        self.set_static_bg('Cavehome.png')
        # We no longer need to call _bind_bg_resize as our master handler takes care of this
        # Remove parchment image and use only transparent clickable buttons
        btn_labels = ["Crafting", "Storage", "Zones", "Sleep"]
        self._menu_buttons = []
        btn_font = ("Segoe UI", 14, "bold")
        btn_fg = "#ffe066"
        btn_bg = "#222"
        btn_active_bg = "#444"
        btn_active_fg = "#fff"
        btn_width = 120
        btn_height = 32
        btn_spacing = 18
        win_w, win_h = self.winfo_width(), self.winfo_height()
        base_x = 24
        base_y = int(win_h * 0.18)
        for i, label in enumerate(btn_labels):
            if label == "Crafting":
                btn = tk.Button(self, text=label, font=btn_font, fg=btn_fg, bg=btn_bg,
                                activebackground=btn_active_bg, activeforeground=btn_active_fg,
                                bd=0, relief="flat", highlightthickness=0, cursor="hand2", command=self.show_crafting_ui)
            elif label == "Storage":
                btn = tk.Button(self, text=label, font=btn_font, fg=btn_fg, bg=btn_bg,
                                activebackground=btn_active_bg, activeforeground=btn_active_fg,
                                bd=0, relief="flat", highlightthickness=0, cursor="hand2", command=self.show_storage_ui)
            elif label == "Zones":
                btn = tk.Button(self, text=label, font=btn_font, fg=btn_fg, bg=btn_bg,
                                activebackground=btn_active_bg, activeforeground=btn_active_fg,
                                bd=0, relief="flat", highlightthickness=0, cursor="hand2", command=self.show_zones_ui)
            else:
                btn = tk.Button(self, text=label, font=btn_font, fg=btn_fg, bg=btn_bg,
                                activebackground=btn_active_bg, activeforeground=btn_active_fg,
                                bd=0, relief="flat", highlightthickness=0, cursor="hand2")
            btn.place(x=base_x, y=base_y + i * (btn_height + btn_spacing), width=btn_width, height=btn_height)
            self._menu_buttons.append(btn)
        # Responsive resize handler for buttons
        def on_resize(event=None):
            win_w, win_h = self.winfo_width(), self.winfo_height()
            base_x = 24
            base_y = int(win_h * 0.18)
            for i, btn in enumerate(self._menu_buttons):
                btn.place(x=base_x, y=base_y + i * (btn_height + btn_spacing), width=btn_width, height=btn_height)
        if hasattr(self, '_menu_resize_binding') and self._menu_resize_binding:
            self.unbind('<Configure>', self._menu_resize_binding)
        self._menu_resize_binding = self.bind('<Configure>', on_resize)
        self.after(100, lambda: on_resize(None))
        # Add a simple animated particle effect for the fireplace (ensure canvas exists and is on top of bg)
        def start_fireplace_particles():
            if not hasattr(self, 'bg_canvas') or not self.bg_canvas:
                return
            self.bg_canvas.lift()  # Ensure canvas is above the background label
            if hasattr(self, '_fire_particles'):
                for p in self._fire_particles:
                    self.bg_canvas.delete(p['id'])
            self._fire_particles = []
            # Fireplace coordinates (tuned for your screenshot)
            def get_fireplace_coords():
                win_w, win_h = self.winfo_width(), self.winfo_height()
                base_x = int(win_w * 0.74)
                base_y = int(win_h * 0.72)
                return base_x, base_y
            def spawn_particle():
                base_x, base_y = get_fireplace_coords()
                x = base_x + random.randint(-18, 18)  # wider spread
                y = base_y + random.randint(0, 16)    # taller spawn
                size = random.randint(8, 16)          # larger size
                color = random.choice(['#ffb347', '#ffd580', '#ff9933', '#ffcc80', '#fff2cc', '#fffbe6', '#ffe066', '#ffae42'])
                pid = self.bg_canvas.create_oval(x, y, x+size, y+size, fill=color, outline='')
                particle = {'id': pid, 'x': x, 'y': y, 'size': size, 'color': color, 'life': 0}
                self._fire_particles.append(particle)
            def animate_particles():
                if not hasattr(self, 'bg_canvas') or not self.bg_canvas:
                    return
                to_remove = []
                for p in self._fire_particles:
                    # Move up and fade out
                    self.bg_canvas.move(p['id'], random.uniform(-0.7, 0.7), -2.2)  # faster, more drift
                    p['life'] += 1
                    # Fade out by reducing alpha (simulate by changing color to lighter)
                    if p['life'] > 12:
                        self.bg_canvas.itemconfig(p['id'], fill='#fffbe6')
                    if p['life'] > 20:
                        self.bg_canvas.itemconfig(p['id'], fill='white')
                    if p['life'] > 28:
                        self.bg_canvas.delete(p['id'])
                        to_remove.append(p)
                for p in to_remove:
                    self._fire_particles.remove(p)
                # Spawn new particles if not too many
                if random.random() < 0.55 and len(self._fire_particles) < 18:  # more particles
                    spawn_particle()
                self.after(28, animate_particles)  # faster update
            animate_particles()
            # Debug: draw a red rectangle at the spawn area
            if hasattr(self, 'debug_particles') and self.debug_particles:
                base_x, base_y = get_fireplace_coords()
                self.bg_canvas.create_rectangle(base_x-20, base_y, base_x+20, base_y+20, outline='red', width=2)
        self.debug_particles = True  # Set to True to show debug rectangle
        if hasattr(self, 'bg_canvas') and self.bg_canvas:
            start_fireplace_particles()

    def show_about(self):
        from tkinter import messagebox
        messagebox.showinfo("About", "Python RPG Game\nVersion 1.0\nDeveloped by Your Name")

    def show_character_creation(self):
        # Unbind previous resize handler if present
        if hasattr(self, '_char_resize_binding') and self._char_resize_binding:
            self.unbind('<Configure>', self._char_resize_binding)
            self._char_resize_binding = None
        for widget in self.winfo_children():
            if widget != self.bg_canvas:
                widget.destroy()
        
        # Set current screen for resize handling
        self._current_screen = "character_creation"
        self.stop_bg_animation()  # Ensure animated bg is stopped/removed
        self.set_static_bg('CharecterPrep.png')
        # We no longer need to call _bind_bg_resize as our master handler takes care of this
        # Place widgets directly on root for transparent look
        label_style = dict(fg="#fff", bg="#222")
        entry_style = dict(font=("Arial", 14), bg="#181818", fg="#fff", insertbackground="#fff", relief="flat", highlightthickness=1, highlightbackground="#ffe066")
        title_label = tk.Label(self, text="Character Creation", font=("Arial", 18, "bold"), **label_style)
        title_label.place(relx=0.5, rely=0.13, anchor="center")
        name_label = tk.Label(self, text="Enter your character's name:", **label_style)
        name_label.place(relx=0.5, rely=0.20, anchor="center")
        name_entry = tk.Entry(self, **entry_style)
        name_entry.place(relx=0.5, rely=0.25, anchor="center", relwidth=0.28)
        gender_label = tk.Label(self, text="Select Gender:", **label_style)
        gender_label.place(relx=0.5, rely=0.31, anchor="center")
        gender_var = tk.StringVar(value="Male")
        img_dir = os.path.join(os.path.dirname(__file__), '../data/assets/Images/misc')
        male_img_path = os.path.join(img_dir, 'male.png')
        female_img_path = os.path.join(img_dir, 'female.png')
        male_img = Image.open(male_img_path).resize((100, 100))
        female_img = Image.open(female_img_path).resize((100, 100))
        self.male_photo = ImageTk.PhotoImage(male_img)
        self.female_photo = ImageTk.PhotoImage(female_img)
        # Gender selection boxes
        gender_frame = tk.Frame(self, bg="#222")
        gender_frame.place(relx=0.5, rely=0.38, anchor="center")
        self.male_box = tk.Frame(gender_frame, width=110, height=130, bd=4, relief="solid", bg="#ffe066")
        self.female_box = tk.Frame(gender_frame, width=110, height=130, bd=4, relief="solid", bg="#222")
        self.male_box.grid(row=0, column=0, padx=32)
        self.female_box.grid(row=0, column=1, padx=32)
        male_canvas = tk.Canvas(self.male_box, width=100, height=100, highlightthickness=0, bd=0, bg="#ffe066")
        male_canvas.create_image(0, 0, anchor="nw", image=self.male_photo)
        male_canvas.place(x=0, y=0)
        female_canvas = tk.Canvas(self.female_box, width=100, height=100, highlightthickness=0, bd=0, bg="#222")
        female_canvas.create_image(0, 0, anchor="nw", image=self.female_photo)
        female_canvas.place(x=0, y=0)
        male_label = tk.Label(self.male_box, text="Male", font=("Arial", 12, "bold"), bg="#ffe066", fg="#222")
        male_label.place(relx=0.5, y=110, anchor="center")
        female_label = tk.Label(self.female_box, text="Female", font=("Arial", 12, "bold"), bg="#222", fg="#ffe066")
        female_label.place(relx=0.5, y=110, anchor="center")
        def select_gender(gender):
            gender_var.set(gender)
            if gender == "Male":
                self.male_box.config(bg="#ffe066")
                self.female_box.config(bg="#222")
                male_label.config(bg="#ffe066", fg="#222")
                female_label.config(bg="#222", fg="#ffe066")
                male_canvas.config(bg="#ffe066")
                female_canvas.config(bg="#222")
            else:
                self.male_box.config(bg="#222")
                self.female_box.config(bg="#ffe066")
                male_label.config(bg="#222", fg="#ffe066")
                female_label.config(bg="#ffe066", fg="#222")
                male_canvas.config(bg="#222")
                female_canvas.config(bg="#ffe066")
        self.male_box.bind("<Button-1>", lambda e: select_gender("Male"))
        self.female_box.bind("<Button-1>", lambda e: select_gender("Female"))
        male_canvas.bind("<Button-1>", lambda e: select_gender("Male"))
        female_canvas.bind("<Button-1>", lambda e: select_gender("Female"))
        male_label.bind("<Button-1>", lambda e: select_gender("Male"))
        female_label.bind("<Button-1>", lambda e: select_gender("Female"))
        select_gender("Male")
        btn_style = dict(bg="#222", fg="#ffe066", activebackground="#ffe066", activeforeground="#222", font=("Arial", 12, "bold"), bd=2, relief="ridge")
        def confirm():
            name = name_entry.get().strip()
            gender = gender_var.get()
            if not name:
                messagebox.showerror("Error", "Name cannot be empty!")
                return
            self.controller.player = Player(name, gender)
            self.show_stat_allocation()
        confirm_btn = tk.Button(self, text="Confirm", command=confirm, **btn_style)
        confirm_btn.place(relx=0.5, rely=0.60, anchor="center")
        back_btn = tk.Button(self, text="Back to Main Menu", command=self.create_main_menu, **btn_style)
        back_btn.place(relx=0.5, rely=0.66, anchor="center")
        # Responsive resize handler (optional, for future use)
        def on_resize(event=None):
            pass  # All widgets use relx/rely, so no action needed
        if hasattr(self, '_char_resize_binding') and self._char_resize_binding:
            self.unbind('<Configure>', self._char_resize_binding)
        self._char_resize_binding = self.bind('<Configure>', on_resize)
        self.after(100, lambda: on_resize(None))

    def _allocate_stat(self, stat, stat_vars, free_points_var, labels, base_stats, update_secondary):
        # Increase stat if free points are available
        if free_points_var.get() > 0:
            stat_vars[stat].set(stat_vars[stat].get() + 1)
            free_points_var.set(free_points_var.get() - 1)
            labels[stat].config(bg="#ffe066", fg="#222")
            self.after(120, lambda: labels[stat].config(bg="#222", fg="#fff"))
            update_secondary()

    def _deallocate_stat(self, stat, stat_vars, free_points_var, labels, base_stats, update_secondary):
        # Decrease stat if above base value
        if stat_vars[stat].get() > base_stats[stat]:
            stat_vars[stat].set(stat_vars[stat].get() - 1)
            free_points_var.set(free_points_var.get() + 1)
            labels[stat].config(bg="#ffe066", fg="#222")
            self.after(120, lambda: labels[stat].config(bg="#222", fg="#fff"))
            update_secondary()

    def show_stat_allocation(self):
        self.stop_bg_animation()
        for widget in self.winfo_children():
            if widget != getattr(self, '_static_bg_label', None):
                widget.destroy()
        
        # Set current screen for resize handling
        self._current_screen = "stat_allocation"
        self.set_static_bg('CharecterPrep.png')
        # We no longer need to call _bind_bg_resize as our master handler takes care of this
        if hasattr(self, '_static_bg_label') and self._static_bg_label:
            self._static_bg_label.lower()
        player = self.controller.player
        main_frame = tk.Frame(self, bg="#222")
        main_frame.pack(fill="both", expand=True)
        main_frame.columnconfigure(0, weight=1)
        header_label = tk.Label(main_frame, text=f"Stat Allocation for {player.name}", font=("Arial", 20, "bold"), fg="#fff", bg="#222", anchor="center")
        header_label.pack(fill="x", pady=(0, 10))
        free_points_var = tk.IntVar(value=player.free_points)
        free_points_frame = tk.Frame(main_frame, bg="#222")
        free_points_frame.pack(fill="x", padx=10, pady=(0, 10))
        tk.Label(free_points_frame, text="Free Points:", font=("Arial", 14, "bold"), fg="#fff", bg="#222").pack(side="left")
        free_points_label = tk.Label(free_points_frame, textvariable=free_points_var, font=("Consolas", 14, "bold"), fg="#fff", bg="#222")
        free_points_label.pack(side="left", padx=(8, 0))
        stats = ["strength", "dexterity", "agility", "intelligence", "vitality", "luck"]
        base_stats = {stat: 2 for stat in stats}
        base_stats["vitality"] = 1
        stat_vars = {stat: tk.IntVar(value=getattr(player.main_stats, stat)) for stat in stats}
        stat_vars["vitality"].set(1)
        self.stat_frame = tk.Frame(main_frame, bg="#222", bd=3, relief="ridge")
        self.stat_frame.pack(pady=12, fill="x", padx=20)
        labels = {}
        value_labels = {}
        def update_secondary():
            from player import MainStats, SecondaryStats
            temp_main = MainStats(**{s: stat_vars[s].get() for s in stats})
            temp_sec = SecondaryStats()
            temp_sec.max_hp = 31 + (temp_main.vitality * 9)
            temp_sec.max_mp = 21 + (temp_main.intelligence * 4)
            temp_sec.attack = 5 + (temp_main.strength * 1.3)
            temp_sec.defense = 2 + (temp_main.vitality * 1.2)
            temp_sec.m_attack = 5 + (temp_main.intelligence * 1)
            temp_sec.m_defense = 2 + (temp_main.intelligence * 1)
            temp_sec.crit_rate = temp_main.dexterity * 0.5
            temp_sec.dodge = temp_main.agility * 0.5
            temp_sec.luck = temp_main.luck
            temp_sec.discovery = temp_main.luck * 0.5
            for i, stat in enumerate(sec_stats):
                label, key = stat[0], stat[1]
                val = getattr(temp_sec, key)
                sec_labels[i].config(text=f"{label}: {val:.2f}", fg="#fff")
            for stat in stats:
                value_labels[stat].config(text=f"{stat_vars[stat].get():.2f}")
            # Show confirm label if no free points
            if free_points_var.get() == 0:
                confirm_label.pack(pady=10)
            else:
                confirm_label.pack_forget()
        for i, stat in enumerate(stats):
            row = tk.Frame(self.stat_frame, bg="#222")
            row.grid(row=i, column=0, pady=6, padx=12, sticky="ew")
            row.columnconfigure(0, weight=1)
            icon = tk.Label(row, text="★", font=("Arial", 14), bg="#222", fg="#ffe066")
            icon.pack(side="left", padx=(0, 6))
            tk.Label(row, text=stat.title()+":", width=10, anchor="e", font=("Arial", 13, "bold"), bg="#222", fg="#fff"). pack(side="left")
            value_labels[stat] = tk.Label(row, text=f"{stat_vars[stat].get():.2f}", width=6, font=("Consolas", 14, "bold"), bg="#222", fg="#fff", bd=2, relief="groove")
            value_labels[stat].pack(side="left", padx=4)
            labels[stat] = value_labels[stat]
            minus_btn = tk.Button(row, text="-", command=lambda s=stat: self._deallocate_stat(s, stat_vars, free_points_var, value_labels, base_stats, update_secondary), width=2, font=("Arial", 13, "bold"), bg="#222", fg="#ffe066", bd=1, relief="raised", activebackground="#333", activeforeground="#ffe066")
            minus_btn.pack(side="left", padx=2)
            plus_btn = tk.Button(row, text="+", command=lambda s=stat: self._allocate_stat(s, stat_vars, free_points_var, value_labels, base_stats, update_secondary), width=2, font=("Arial", 13, "bold"), bg="#ffe066", fg="#222", bd=1, relief="raised", activebackground="#fffbe6", activeforeground="#222")
            plus_btn.pack(side="left", padx=2)
        sec_stats = [
            ("Max HP", 'max_hp'), ("Max MP", 'max_mp'), ("Attack", 'attack'), ("Defense", 'defense'),
            ("Magic Atk", 'm_attack'), ("Magic Def", 'm_defense'),
            ("Dodge", 'dodge'), ("Crit Rate", 'crit_rate'), ("Discovery", 'discovery')
        ]
        sec_frame = tk.Frame(main_frame, bg="#222", bd=2, relief="groove")
        sec_frame.pack(pady=14, fill="both", expand=True, padx=20)
        sec_labels = []
        from player import SecondaryStats
        temp_main = type(player.main_stats)(**{s: stat_vars[s].get() for s in stats})
        temp_sec = SecondaryStats()
        temp_sec.max_hp = 31 + (temp_main.vitality * 9)
        temp_sec.max_mp = 21 + (temp_main.intelligence * 4)
        temp_sec.attack = 5 + (temp_main.strength * 1.3)
        temp_sec.defense = 2 + (temp_main.vitality * 1.2)
        temp_sec.m_attack = 5 + (temp_main.intelligence * 1)
        temp_sec.m_defense = 2 + (temp_main.intelligence * 1)
        temp_sec.crit_rate = temp_main.dexterity * 0.5
        temp_sec.dodge = temp_main.agility * 0.5
        temp_sec.luck = temp_main.luck
        temp_sec.discovery = temp_main.luck * 0.5
        for i, stat in enumerate(sec_stats):
            label, key = stat[0], stat[1]
            val = getattr(temp_sec, key)
            sec_labels.append(tk.Label(sec_frame, text=f"{label}: {val:.2f}", font=("Consolas", 12), bg="#222", fg="#fff"))
            sec_labels[-1].grid(row=i, column=0, sticky="w", padx=12, pady=1)
        # Confirm label and Enter binding
        confirm_label = tk.Label(main_frame, text="Press Enter to confirm", font=("Segoe UI", 15, "bold"), bg="#222", fg="#ffe066")
        confirm_label.pack_forget()
        def on_enter_confirm(event=None):
            if free_points_var.get() == 0:
                self.fade_to_cavehome_menu()
        self.bind('<Return>', on_enter_confirm)
        # --- End of stat allocation setup ---
        self.update_idletasks()
        self.minsize(800, 600)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        main_frame.pack_propagate(False)
        # Update secondary stats and confirm label on start
        update_secondary()
        # Move confirm label to center of window if visible
        def update_confirm_label():
            if free_points_var.get() == 0:
                confirm_label.place(relx=0.5, rely=0.5, anchor="center")
            else:
                confirm_label.place_forget()
        # Patch update_secondary to also update confirm label position
        old_update_secondary = update_secondary
        def new_update_secondary():
            old_update_secondary()
            update_confirm_label()
        update_secondary = new_update_secondary
        # Call once to set position
        update_confirm_label()

    def fade_to_cavehome_menu(self):
        # Fade out, switch bg, fade in, then show cavehome menu
        self.update_idletasks()
        win_w = self.winfo_width()
        win_h = self.winfo_height()
        win_x = self.winfo_rootx()
        win_y = self.winfo_rooty()
        fade = tk.Toplevel(self)
        fade.overrideredirect(True)
        fade.geometry(f"{win_w}x{win_h}+{win_x}+{win_y}")
        fade.lift()
        fade.attributes('-topmost', True)
        fade.config(bg='#000')
        fade.attributes('-alpha', 0.0)
        for i in range(0, 21):
            fade.attributes('-alpha', i/20)
            fade.update()
            fade.after(15)
        self.set_static_bg('Cavehome.png')
        for i in range(20, -1, -1):
            fade.attributes('-alpha', i/20)
            fade.update()
            fade.after(15)
        fade.destroy()
        self.show_cavehome_menu()

    def show_crafting_ui(self):
        # Remove any previous crafting UI
        if hasattr(self, '_crafting_modal') and self._crafting_modal:
            self._crafting_modal.destroy()
        modal = tk.Toplevel(self)
        modal.transient(self)
        modal.grab_set()
        modal.geometry(f"{int(self.winfo_width()*0.7)}x{int(self.winfo_height()*0.7)}+{self.winfo_rootx()+int(self.winfo_width()*0.15)}+{self.winfo_rooty()+int(self.winfo_height()*0.15)}")
        modal.configure(bg="#111")
        modal.title("Crafting")
        modal.resizable(True, True)  # Make resizable for better UI experience
        self._crafting_modal = modal
        def close_modal(event=None):
            modal.grab_release()
            modal.destroy()
        modal.bind('<Escape>', close_modal)
        # Red border for modal
        border = tk.Frame(modal, bg="#c00", bd=2)
        border.place(relx=0, rely=0, relwidth=1, relheight=1)
        # Tabs at the top
        categories = ["Alchemy", "Carpentry", "Cooking", "Goldsmithing", "Leatherworking", "Smithing"]
        selected_cat = tk.StringVar(value=categories[0])
        tab_frame = tk.Frame(border, bg="#111")
        tab_frame.place(relx=0.01, rely=0.01, relwidth=0.95, relheight=0.08)
        tab_btns = []
        def select_cat(cat):
            selected_cat.set(cat)
            for btn in tab_btns:
                if btn['text'] == cat:
                    btn.config(bg="#3cf", fg="#fff", relief="sunken")
                else:
                    btn.config(bg="#222", fg="#3cf", relief="raised")
            update_level_panel()
        for i, cat in enumerate(categories):
            btn = tk.Button(tab_frame, text=cat, font=("Segoe UI", 12, "bold"), bg="#3cf" if i==0 else "#222", fg="#fff" if i==0 else "#3cf", bd=1, relief="sunken" if i==0 else "raised", activebackground="#3cf", activeforeground="#fff", cursor="hand2", command=lambda c=cat: select_cat(c))
            btn.pack(side="left", padx=4, pady=2, ipadx=6, ipady=2)
            tab_btns.append(btn)
        # X close button (styled)
        x_btn = tk.Button(tab_frame, text="✕", command=close_modal, font=("Arial", 14, "bold"), bg="#222", fg="#f44", bd=1, relief="flat", activebackground="#f44", activeforeground="#fff", cursor="hand2")
        x_btn.pack(side="right", padx=6, pady=2)
        # Blue border for left column
        left_col = tk.Frame(border, bg="#09f", bd=2)
        left_col.place(relx=0.01, rely=0.10, relwidth=0.22, relheight=0.87)
        # Recipes label
        recipes_lbl = tk.Label(left_col, text="Recipes", font=("Segoe UI", 12, "bold"), bg="#111", fg="#3cf")
        recipes_lbl.pack(fill="x", pady=(4,2))
        # Level range buttons
        level_ranges = [f"Lvl {i}-{i+9}" for i in range(1, 100, 10)]
        selected_lvl = tk.StringVar(value=level_ranges[0])
        lvl_btns = []
        # Placeholder: get actual player crafting level for selected category
        player_crafting_level = 23  # TODO: Replace with real value from player data
        def get_range_minmax(lvl_str):
            parts = lvl_str.replace('Lvl ','').split('-')
            return int(parts[0]), int(parts[1])
        def select_lvl(lvl):
            selected_lvl.set(lvl)
            for btn in lvl_btns:
                if btn['text'] == lvl:
                    btn.config(bg="#3cf", fg="#fff", relief="sunken")
                else:
                    btn.config(bg="#111", fg="#3cf", relief="raised")
            update_recipe_panel()
        for i, lvl in enumerate(level_ranges):
            min_lvl, max_lvl = get_range_minmax(lvl)
            enabled = player_crafting_level >= min_lvl
            btn = tk.Button(left_col, text=lvl, font=("Segoe UI", 11, "bold"),
                bg="#3cf" if i==0 and enabled else ("#111" if enabled else "#222"),
                fg="#fff" if i==0 and enabled else ("#3cf" if enabled else "#888"),
                bd=1, relief="sunken" if i==0 and enabled else ("raised" if enabled else "flat"),
                activebackground="#3cf", activeforeground="#fff", cursor="hand2" if enabled else "arrow",
                command=(lambda l=lvl: select_lvl(l)) if enabled else None,
                state="normal" if enabled else "disabled"
            )
            btn.pack(fill="x", pady=1, padx=2)
            lvl_btns.append(btn)
        # Main area for recipe details (right side)
        main_area = tk.Frame(border, bg="#111")
        main_area.place(relx=0.24, rely=0.10, relwidth=0.75, relheight=0.87)
        # Placeholder for recipe details
        details_lbl = tk.Label(main_area, text="", font=("Segoe UI", 13), bg="#111", fg="#fff", anchor="nw", justify="left")
        details_lbl.pack(fill="both", expand=True, padx=8, pady=8)
        # Update panels on selection
        def update_level_panel():
            for i, btn in enumerate(tab_btns):
                if btn['text'] == selected_cat.get():
                    btn.config(bg="#3cf", fg="#fff", relief="sunken")
                else:
                    btn.config(bg="#222", fg="#3cf", relief="raised")
            # Optionally update recipes for new category
            update_recipe_panel()
        def update_recipe_panel():
            for i, btn in enumerate(lvl_btns):
                min_lvl, max_lvl = get_range_minmax(btn['text'])
                enabled = player_crafting_level >= min_lvl
                if btn['text'] == selected_lvl.get() and enabled:
                    btn.config(bg="#3cf", fg="#fff", relief="sunken", state="normal", cursor="hand2")
                elif enabled:
                    btn.config(bg="#111", fg="#3cf", relief="raised", state="normal", cursor="hand2")
                else:
                    btn.config(bg="#222", fg="#888", relief="flat", state="disabled", cursor="arrow")
            # For now, just show selected tab and level
            details_lbl.config(text=f"Category: {selected_cat.get()}\nLevel Range: {selected_lvl.get()}\n\n(Recipe details will appear here)")
        update_level_panel()
        update_recipe_panel()
        modal.focus_set()
        # --- Crafting UI Improvements ---
        # Show player crafting level and XP at the top
        player_crafting_level = 23  # TODO: Replace with real value from player data
        player_crafting_xp = 1200   # TODO: Replace with real value from player data
        level_xp_frame = tk.Frame(border, bg="#111")
        level_xp_frame.place(relx=0.01, rely=0.09, relwidth=0.97, relheight=0.05)
        tk.Label(level_xp_frame, text=f"Level: {player_crafting_level}", font=("Segoe UI", 11, "bold"), bg="#111", fg="#3cf").pack(side="left", padx=8)
        tk.Label(level_xp_frame, text=f"XP: {player_crafting_xp}", font=("Segoe UI", 11), bg="#111", fg="#fff").pack(side="left", padx=8)
        # Recipe list for selected category and level range
        recipe_list_frame = tk.Frame(left_col, bg="#111")
        recipe_list_frame.pack(fill="both", expand=True, padx=2, pady=(8,2))
        # Sample recipes (replace with real data)
        sample_recipes = [
            {"name": "Healing Potion", "rarity": "Common", "icon": None, "ingredients": [("Herb", 2), ("Water", 1)], "can_craft": True},
            {"name": "Mana Elixir", "rarity": "Uncommon", "icon": None, "ingredients": [("Mana Herb", 2), ("Water", 2)], "can_craft": False},
            {"name": "Stamina Soup", "rarity": "Rare", "icon": None, "ingredients": [("Meat", 1), ("Herb", 1), ("Water", 1)], "can_craft": True},
        ]
        rarity_colors = {"Common": "#bbb", "Uncommon": "#3c3", "Rare": "#3cf", "Epic": "#a3f", "Legendary": "#fc0"}
        recipe_scroll = tk.Scrollbar(recipe_list_frame)
        recipe_scroll.pack(side="right", fill="y")
        recipe_listbox = tk.Listbox(recipe_list_frame, font=("Segoe UI", 11), bg="#222", fg="#fff", selectbackground="#3cf", selectforeground="#fff", activestyle="none", yscrollcommand=recipe_scroll.set, height=8)
        for recipe in sample_recipes:
            recipe_listbox.insert("end", recipe["name"])
        recipe_scroll.config(command=recipe_listbox.yview)
        recipe_listbox.pack(fill="both", expand=True)
        # Details panel for selected recipe
        details_panel = tk.Frame(main_area, bg="#111")
        details_panel.pack(fill="both", expand=True, padx=8, pady=8)
        details_lbl = tk.Label(details_panel, text="Select a recipe to see details.", font=("Segoe UI", 13), bg="#111", fg="#fff", anchor="nw", justify="left")
        details_lbl.pack(fill="both", expand=True)
        craft_btn = tk.Button(details_panel, text="Craft", font=("Segoe UI", 12, "bold"), bg="#3cf", fg="#fff", state="disabled")
        craft_btn.pack(pady=8)
        def show_recipe_details(event=None):
            sel = recipe_listbox.curselection()
            if not sel:
                details_lbl.config(text="Select a recipe to see details.")
                craft_btn.config(state="disabled")
                return
            idx = sel[0]
            recipe = sample_recipes[idx]
            ing_lines = "\n".join([f"- {name} x{qty}" for name, qty in recipe["ingredients"]])
            details_lbl.config(text=f"{recipe['name']}\nRarity: {recipe['rarity']}\n\nIngredients:\n{ing_lines}")
            craft_btn.config(state="normal" if recipe["can_craft"] else "disabled")
        recipe_listbox.bind("<<ListboxSelect>>", show_recipe_details)
        # Responsive resizing for modal
        def on_modal_resize(event=None):
            modal.update_idletasks()
        modal.bind('<Configure>', on_modal_resize)

    def show_storage_ui(self):
        # Remove any previous storage UI
        if hasattr(self, '_storage_modal') and self._storage_modal:
            self._storage_modal.destroy()
        modal = tk.Toplevel(self)
        modal.transient(self)
        modal.grab_set()
        modal.geometry(f"{int(self.winfo_width()*0.7)}x{int(self.winfo_height()*0.7)}+{self.winfo_rootx()+int(self.winfo_width()*0.15)}+{self.winfo_rooty()+int(self.winfo_height()*0.15)}")
        modal.configure(bg="#111")
        modal.title("Storage")
        modal.resizable(True, True)  # Make resizable for better UI experience
        self._storage_modal = modal
        def close_modal(event=None):
            modal.grab_release()
            modal.destroy()
        modal.bind('<Escape>', close_modal)
        # Red border for modal
        border = tk.Frame(modal, bg="#c00", bd=2)
        border.place(relx=0, rely=0, relwidth=1, relheight=1)
        # Tabs for categories
        categories = ["Items", "Weapons", "Armor", "Materials", "Consumables", "Other"]
        selected_cat = tk.StringVar(value=categories[0])
        tab_frame = tk.Frame(border, bg="#111")
        tab_frame.place(relx=0.01, rely=0.01, relwidth=0.95, relheight=0.08)
        tab_btns = []
        def select_cat(cat):
            selected_cat.set(cat)
            for btn in tab_btns:
                if btn['text'] == cat:
                    btn.config(bg="#3cf", fg="#fff", relief="sunken")
                else:
                    btn.config(bg="#222", fg="#3cf", relief="raised")
            update_item_panel()
        for i, cat in enumerate(categories):
            btn = tk.Button(tab_frame, text=cat, font=("Segoe UI", 12, "bold"), bg="#3cf" if i==0 else "#222", fg="#fff" if i==0 else "#3cf", bd=1, relief="sunken" if i==0 else "raised", activebackground="#3cf", activeforeground="#fff", cursor="hand2", command=lambda c=cat: select_cat(c))
            btn.pack(side="left", padx=4, pady=2, ipadx=6, ipady=2)
            tab_btns.append(btn)
        # X close button (styled)
        x_btn = tk.Button(tab_frame, text="✕", command=close_modal, font=("Arial", 14, "bold"), bg="#222", fg="#f44", bd=1, relief="flat", activebackground="#f44", activeforeground="#fff", cursor="hand2")
        x_btn.pack(side="right", padx=6, pady=2)
        # Sorting options
        sort_frame = tk.Frame(border, bg="#111")
        sort_frame.place(relx=0.01, rely=0.10, relwidth=0.22, relheight=0.08)
        sort_by = tk.StringVar(value="Name")
        sort_options = ["Name", "Rarity", "Quantity"]
        tk.Label(sort_frame, text="Sort by:", font=("Segoe UI", 11, "bold"), bg="#111", fg="#3cf").pack(side="left", padx=2)
        for opt in sort_options:
            btn = tk.Radiobutton(sort_frame, text=opt, variable=sort_by, value=opt, font=("Segoe UI", 10), bg="#111", fg="#fff", selectcolor="#3cf", activebackground="#222", activeforeground="#fff", command=lambda: update_item_panel())
            btn.pack(side="left", padx=2)
        # Organize button
        organize_btn = tk.Button(sort_frame, text="Organize", font=("Segoe UI", 10, "bold"), bg="#3cf", fg="#fff", activebackground="#222", activeforeground="#3cf", bd=1, relief="ridge", command=lambda: organize_items())
        organize_btn.pack(side="right", padx=2)
        # Main area for items
        main_area = tk.Frame(border, bg="#111")
        main_area.place(relx=0.24, rely=0.10, relwidth=0.75, relheight=0.87)
        # Placeholder: sample items (replace with real inventory)
        sample_items = [
            {"name": "Potion", "type": "Consumable", "rarity": "Common", "qty": 5},
            {"name": "Elixir", "type": "Consumable", "rarity": "Rare", "qty": 2},
            {"name": "Iron Sword", "type": "Weapon", "rarity": "Uncommon", "qty": 1},
            {"name": "Steel Armor", "type": "Armor", "rarity": "Rare", "qty": 1},
            {"name": "Gold Nugget", "type": "Material", "rarity": "Epic", "qty": 3},
            {"name": "Mystery Box", "type": "Other", "rarity": "Legendary", "qty": 1},
        ]
        rarity_colors = {"Common": "#bbb", "Uncommon": "#3c3", "Rare": "#3cf", "Epic": "#a3f", "Legendary": "#fc0"}
        item_list_frame = tk.Frame(main_area, bg="#111")
        item_list_frame.pack(fill="both", expand=True)
        def organize_items():
            # Placeholder: just re-sort by current sort
            update_item_panel()
        def update_item_panel():
            for w in item_list_frame.winfo_children():
                w.destroy()
            # Filter by category and search
            cat = selected_cat.get()
            search = search_var.get().lower()
            items = [item for item in sample_items if ((cat == "Items" and item["type"] not in ["Weapon", "Armor", "Material", "Consumable", "Other"]) or item["type"] == cat or (cat == "Other" and item["type"] not in categories)) and (search in item["name"].lower())]
            # Sort
            if sort_by.get() == "Name":
                items.sort(key=lambda x: x["name"])
            elif sort_by.get() == "Rarity":
                rarity_order = ["Common", "Uncommon", "Rare", "Epic", "Legendary"]
                items.sort(key=lambda x: rarity_order.index(x["rarity"]))
            elif sort_by.get() == "Quantity":
                items.sort(key=lambda x: -x["qty"])
            # Display
            for item in items:
                frame = tk.Frame(item_list_frame, bg="#222", bd=1, relief="groove")
                frame.pack(fill="x", padx=4, pady=2)
                # Icon placeholder
                icon_lbl = tk.Label(frame, text="🗃️", font=("Segoe UI", 13), bg="#222", fg="#fff")
                icon_lbl.pack(side="left", padx=4)
                name_lbl = tk.Label(frame, text=item["name"], font=("Segoe UI", 12, "bold"), bg="#222", fg=rarity_colors.get(item["rarity"], "#fff"))
                name_lbl.pack(side="left", padx=8)
                qty_lbl = tk.Label(frame, text=f"x{item['qty']}", font=("Consolas", 11), bg="#222", fg="#fff")
                qty_lbl.pack(side="right", padx=8)
                rarity_lbl = tk.Label(frame, text=item["rarity"], font=("Segoe UI", 10), bg="#222", fg=rarity_colors.get(item["rarity"], "#fff"))
                rarity_lbl.pack(side="right", padx=8)
                # Tooltip for item details
                def show_tooltip(event, text=item["name"]+"\nRarity: "+item["rarity"]+f"\nQty: {item['qty']}"):
                    tip = tk.Toplevel(frame)
                    tip.wm_overrideredirect(True)
                    tip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
                    tk.Label(tip, text=text, bg="#222", fg="#fff", font=("Segoe UI", 10), bd=1, relief="solid").pack()
                    frame._tooltip = tip
                def hide_tooltip(event):
                    if hasattr(frame, '_tooltip'):
                        frame._tooltip.destroy()
                        del frame._tooltip
                frame.bind("<Enter>", show_tooltip)
                frame.bind("<Leave>", hide_tooltip)
                # Double-click to use/equip (placeholder)
                def on_double_click(event, item=item):
                    messagebox.showinfo("Item Action", f"Used or equipped: {item['name']}")
                frame.bind("<Double-Button-1>", on_double_click)
        search_var = tk.StringVar()
        search_var.trace_add('write', lambda *args: update_item_panel())
        # Responsive resizing for modal
        def on_modal_resize(event=None):
            modal.update_idletasks()
        modal.bind('<Configure>', on_modal_resize)

    def show_zones_ui(self):
        # Modern, split UI for unlocked zones based on user's mockup
        modal = tk.Toplevel(self)
        modal.transient(self)
        modal.grab_set()
        modal.geometry(f"{int(self.winfo_width()*0.85)}x{int(self.winfo_height()*0.85)}+{self.winfo_rootx()+int(self.winfo_width()*0.075)}+{self.winfo_rooty()+int(self.winfo_height()*0.075)}")
        modal.configure(bg="#000000")  # Black background
        modal.title("Unlocked Zones")
        modal.resizable(True, True)
        self._zones_modal = modal  # Store reference for resize handling
        
        # Red border for modal
        border = tk.Frame(modal, bg="#FF0000", bd=2)
        border.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Layout based on the second image:
        # Left panel (zones list)
        left_panel = tk.Frame(border, bg="#000000", bd=1, relief="solid")
        left_panel.place(relx=0.01, rely=0.01, relwidth=0.28, relheight=0.98)
        
        # Top right panel (zone image)
        top_right_panel = tk.Frame(border, bg="#000000", bd=1, relief="solid")
        top_right_panel.place(relx=0.30, rely=0.01, relwidth=0.69, relheight=0.59)
        
        # Bottom left panel (enemies list)
        bottom_left_panel = tk.Frame(border, bg="#000000", bd=1, relief="solid")
        bottom_left_panel.place(relx=0.30, rely=0.61, relwidth=0.34, relheight=0.38)
        
        # Bottom right panel (gatherables list)
        bottom_right_panel = tk.Frame(border, bg="#000000", bd=1, relief="solid")
        bottom_right_panel.place(relx=0.65, rely=0.61, relwidth=0.34, relheight=0.38)
        
        # --- Left panel: zone list ---
        zones_title = tk.Label(
            left_panel,
            text="List of zones from\nHighest level to\nlowest",
            font=("Segoe UI", 12, "bold"),
            bg="#000000",
            fg="#CD853F",  # SandyBrown
            justify="left"
        )
        zones_title.pack(pady=(8,2), anchor="w", padx=10)
        
        zone_list_frame = tk.Frame(left_panel, bg="#000000")
        zone_list_frame.pack(fill="both", expand=True, padx=4, pady=4)
        
        zone_scroll = tk.Scrollbar(zone_list_frame)
        zone_scroll.pack(side="right", fill="y")
        
        zone_listbox = tk.Listbox(
            zone_list_frame,
            font=("Segoe UI", 12),
            bg="#000000",
            fg="#FFFFFF",
            selectbackground="#333333",
            selectforeground="#FFFFFF",
            activestyle="none",
            yscrollcommand=zone_scroll.set,
            height=12,
            bd=0,
            highlightthickness=0
        )
        zone_scroll.config(command=zone_listbox.yview)
        zone_listbox.pack(fill="both", expand=True)
        
        # List of zones with colors matching the example image
        zones = [
            {"name": "Arch Devil Citadel", "color": "#00FFFF", "level": "80-99", "bestiary": "arch_devil_citadel.txt"},            # Cyan
            {"name": "Grand Palace of Sheol", "color": "#9932CC", "level": "70-79", "bestiary": "grand_palace_of_sheol.txt"},      # Purple
            {"name": "Sheol", "color": "#0000FF", "level": "60-69", "bestiary": "sheol.txt"},                                      # Blue
            {"name": "Fang of the Fallen God", "color": "#00BFFF", "level": "55-59", "bestiary": "fang_of_the_fallen_god.txt"},    # Light Blue
            {"name": "Edge of Eternity", "color": "#00BFFF", "level": "50-54", "bestiary": "edge_of_eternity.txt"},                # Light Blue
            {"name": "Outside Eternity", "color": "#00BFFF", "level": "45-49", "bestiary": "outside_eternity.txt"},                # Light Blue
            {"name": "Ice Continent", "color": "#00BFFF", "level": "40-44", "bestiary": "ice_continent.txt"},                      # Light Blue
            {"name": "Chaotic Zone", "color": "#FFFFFF", "level": "39-44", "bestiary": "chaotic_zone.txt"},                        # White
            {"name": "Volcanic Zone", "color": "#00FF00", "level": "35-39", "bestiary": "volcanic_zone.txt"},                      # Green
            {"name": "Desert Zone", "color": "#00FF00", "level": "30-34", "bestiary": "desert_zone.txt"},                          # Green
            {"name": "Dungeon Fallen Dynasty Ruins", "color": "#FFFF00", "level": "28-32", "bestiary": "dungeon_fallen_dyansty_ruins.txt"}, # Yellow
            {"name": "West Shapira Mountains", "color": "#00FF00", "level": "25-29", "bestiary": "west_shapira_mountains.txt"},    # Green
            {"name": "Dungeon Goblin Fortress", "color": "#FFFF00", "level": "22-26", "bestiary": "dungeon_goblin_fortress.txt"},  # Yellow
            {"name": "Central Shapira Forest", "color": "#CCCCCC", "level": "20-24", "bestiary": "central_shapira_forest.txt"},    # Light Gray
            {"name": "Dungeon Wahsh Den", "color": "#FFFF00", "level": "15-20", "bestiary": "dungeon_wahsh_den.txt"},              # Yellow
            {"name": "Shapira Plains", "color": "#CCCCCC", "level": "10-19", "bestiary": "shapira_plains.txt"},                    # Light Gray
            {"name": "Goblin Camp", "color": "#CCCCCC", "level": "5-9", "bestiary": "goblin_camp.txt"},                            # Light Gray
        ]
        
        for idx, z in enumerate(zones):
            zone_listbox.insert("end", f"{z['name']} (Lv.{z['level']})")
            zone_listbox.itemconfig(idx, fg=z["color"])
        
        # --- Top right panel: zone image ---
        image_title = tk.Label(
            top_right_panel,
            text="Zones .PNG\nimage when its\nselected",
            font=("Segoe UI", 12, "bold"),
            bg="#000000",
            fg="#CD853F"  # SandyBrown
        )
        image_title.pack(pady=(8,2))
        
        img_label = tk.Label(top_right_panel, bg="#000000")
        img_label.pack(fill="both", expand=True, padx=8, pady=8)
        
        def update_zone_image(zone_name):
            # Try .png and .PNG
            img_dir = os.path.join(os.path.dirname(__file__), '../data/assets/Images/Zones')
            for ext in [".png", ".PNG"]:
                img_path = os.path.join(img_dir, f"{zone_name}{ext}")
                if os.path.exists(img_path):
                    try:
                        img = Image.open(img_path)
                        # Resize to fit panel
                        panel_w = top_right_panel.winfo_width() or 320
                        panel_h = top_right_panel.winfo_height() or 240
                        img = img.resize((panel_w-32, panel_h-80))
                        img_label.img = ImageTk.PhotoImage(img)
                        img_label.config(image=img_label.img, text="")
                        return
                    except Exception as e:
                        continue
            img_label.config(image="", text="[No Image]", fg="#888", font=("Segoe UI", 16, "bold"))
        
        # --- Bottom left panel: enemies list ---
        enemies_title = tk.Label(
            bottom_left_panel,
            text="List of enemys\nthat randomizes\nwhen an enemy\nis defeated.",
            font=("Segoe UI", 12, "bold"),
            bg="#000000",
            fg="#CD853F"  # SandyBrown
        )
        enemies_title.pack(pady=(8,2))
        
        enemy_list_frame = tk.Frame(bottom_left_panel, bg="#000000")
        enemy_list_frame.pack(fill="both", expand=True, padx=4, pady=4)
        
        enemy_scroll = tk.Scrollbar(enemy_list_frame)
        enemy_scroll.pack(side="right", fill="y")
        
        enemy_listbox = tk.Listbox(
            enemy_list_frame,
            font=("Segoe UI", 11),
            bg="#000000",
            fg="#FFFFFF",
            selectbackground="#333333",
            selectforeground="#FFFFFF",
            activestyle="none",
            yscrollcommand=enemy_scroll.set,
            height=8,
            bd=0,
            highlightthickness=0
        )
        enemy_scroll.config(command=enemy_listbox.yview)
        enemy_listbox.pack(fill="both", expand=True)
        
        # --- Bottom right panel: gatherables list ---
        gather_title = tk.Label(
            bottom_right_panel,
            text="List of gatherable\nthat randomizes\nwhen a\ngatherable node\nis gathered",
            font=("Segoe UI", 12, "bold"),
            bg="#000000",
            fg="#CD853F"  # SandyBrown
        )
        gather_title.pack(pady=(8,2))
        
        gather_list_frame = tk.Frame(bottom_right_panel, bg="#000000")
        gather_list_frame.pack(fill="both", expand=True, padx=4, pady=4)
        
        gather_scroll = tk.Scrollbar(gather_list_frame)
        gather_scroll.pack(side="right", fill="y")
        
        gather_listbox = tk.Listbox(
            gather_list_frame,
            font=("Segoe UI", 11),
            bg="#000000",
            fg="#FFFFFF",
            selectbackground="#333333",
            selectforeground="#FFFFFF",
            activestyle="none",
            yscrollcommand=gather_scroll.set,
            height=8,
            bd=0,
            highlightthickness=0
        )
        gather_scroll.config(command=gather_listbox.yview)
        gather_listbox.pack(fill="both", expand=True)
        
        # --- Populate lists on zone select ---
        def on_zone_select(event=None):
            sel = zone_listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            zone = zones[idx]
            # Update image
            update_zone_image(zone["name"].replace(" ", "_").lower())
            # Load bestiary data for this zone
            bestiary_path = os.path.join(os.path.dirname(__file__), f"../data/bestiary/{zone['bestiary']}")
            all_enemies = []  # All enemies in the zone
            gatherables = []
            
            if os.path.exists(bestiary_path):
                with open(bestiary_path, encoding="utf-8") as f:
                    lines = f.readlines()
                for line in lines:
                    if line.startswith("ENEMY:"):
                        enemy = line.split(":",1)[1].strip()
                        all_enemies.append(enemy)
                    elif line.startswith("GATHER:"):
                        gather = line.split(":",1)[1].strip()
                        gatherables.append(gather)
            
            # Update enemy list - show all enemies but mark undiscovered ones as "???"
            enemy_listbox.delete(0, "end")
            if all_enemies:
                # Randomize order as per request
                random.shuffle(all_enemies)
                for enemy in all_enemies:
                    # Check if this enemy has been discovered
                    is_discovered = False
                    if hasattr(self.controller, 'bestiary') and self.controller.bestiary:
                        # Normalize the enemy name for comparison
                        enemy_id = enemy.lower().replace(" ", "_")
                        # Check if this enemy is in the discovered set
                        for discovered in self.controller.bestiary.discovered_enemies:
                            if enemy_id in discovered.lower():
                                is_discovered = True
                                break
                    
                    # Display actual name if discovered, otherwise "???"
                    if is_discovered:
                        enemy_listbox.insert("end", enemy)
                    else:
                        enemy_listbox.insert("end", "??? (Undiscovered)")
            
            # Update gatherable list - randomize order as per request
            gather_listbox.delete(0, "end")
            if gatherables:
                random.shuffle(gatherables)
                for g in gatherables:
                    gather_listbox.insert("end", g)
        
        zone_listbox.bind("<<ListboxSelect>>", on_zone_select)
        
        # Select first zone by default
        if zone_listbox.size() > 0:
            zone_listbox.selection_set(0)
            on_zone_select()
        
        # X close button
        x_btn = tk.Button(
            border,
            text="✕",
            command=lambda: (modal.grab_release(), modal.destroy()),
            font=("Arial", 16, "bold"),
            bg="#222",
            fg="#FF0000",
            bd=1,
            relief="flat",
            activebackground="#FF0000",
            activeforeground="#FFFFFF",
            cursor="hand2"
        )
        x_btn.place(relx=0.96, rely=0.01, width=36, height=36)
        
        modal.focus_set()

    def debug_print(self, *args, **kwargs):
        if hasattr(self, 'debug_output') and self.debug_output:
            print(*args, **kwargs)

    def debug_toggle(self):
        self.debug_output = not getattr(self, '_is_fullscreen', False)
        if self.debug_output:
            self.debug_print("Debugging enabled")
        else:
            self.debug_print("Debugging disabled")

    def debug_clear(self):
        if hasattr(self, 'debug_output') and self.debug_output:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("Debug log cleared")

# --- Debugging commands ---
def debug_commands(gui):
    import keyboard
    def on_f12():
        gui.debug_toggle()
    keyboard.add_hotkey('f12', on_f12)
    def on_f11():
        gui.debug_clear()
    keyboard.add_hotkey('f11', on_f11)
    print("[DEBUG] Debug commands registered")

# --- Main application ---
if __name__ == "__main__":
    app = GameGUI()
    # debug_commands(app)  # Uncomment to enable debug commands
    app.mainloop()
