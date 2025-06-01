import tkinter as tk
from tkinter import simpledialog
import random
import time
import pymongo
from PIL import Image, ImageTk, ImageDraw

# MongoDB setup
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["atm_system"]
accounts_collection = db["accounts"]

# --- Custom Toggle Switch Widget ---
class ToggleSwitch(tk.Canvas):
    def __init__(self, master, on_toggle_callback, initial_state=False, **kwargs):
        super().__init__(master, **kwargs)
        self.on_toggle_callback = on_toggle_callback
        self.state = initial_state
        # Set highlightthickness and bd to 0 to remove any borders
        self.config(highlightthickness=0, bd=0)

        self.width = 60
        self.height = 30
        self.slider_radius = (self.height - 4) // 2 # 2px padding on each side
        self.slider_x_on = self.width - self.slider_radius - 2
        self.slider_x_off = self.slider_radius + 2

        self.config(width=self.width, height=self.height)
        
        # Make the canvas itself transparent by setting its background to a color
        # that will blend with the main canvas's actual drawn image background
        # or, more robustly, match the dark/light mode background of the main frame
        # We'll handle this from the ATMInterface side for better integration.
        
        self.bind("<Button-1>", self._toggle)
        self.draw_switch()

    def draw_switch(self):
        self.delete("all")
        
        # Draw the background of the switch (the track)
        # This is where the background color logic should be
        track_color = "#00e676" if self.state else "#cccccc"
        
        # Rounded rectangle for the track
        # Draw two circles at the ends and a rectangle in the middle
        self.create_oval(2, 2, self.height-2, self.height-2, fill=track_color, outline="") # Left half circle
        self.create_oval(self.width-(self.height-2), 2, self.width-2, self.height-2, fill=track_color, outline="") # Right half circle
        self.create_rectangle(self.height/2, 2, self.width-self.height/2, self.height-2, fill=track_color, outline="") # Middle rectangle
        
        # Slider (white circle)
        slider_x = self.slider_x_on if self.state else self.slider_x_off
        self.create_oval(slider_x - self.slider_radius, self.height/2 - self.slider_radius,
                         slider_x + self.slider_radius, self.height/2 + self.slider_radius,
                         fill="white", outline="#cccccc", width=1)

    def _toggle(self, event=None):
        self.state = not self.state
        self.draw_switch()
        if self.on_toggle_callback:
            self.on_toggle_callback()

# --- ATM Interface Class ---
class ATMInterface:
    def __init__(self, master):
        self.master = master
        self.master.title("ATM Interface")
        
        self.master.minsize(600, 600)

        self.dark_mode = False
        self.set_colors()

        self.current_user = None

        self.original_bg_image = None
        try:
            self.original_bg_image = Image.open("currency.jpg")
        except FileNotFoundError:
            print("Error: currency.jpg not found. Please ensure the image file is in the correct directory.")

        self.canvas = tk.Canvas(master, bg="lightgray") # Default canvas background
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Configure>", self.on_canvas_resize)

        self.main_frame = tk.Frame(self.canvas, bg=self.bg_color, highlightbackground="#cfcfcf", highlightthickness=2)
        self.main_window_id = None

        # Create the ToggleSwitch widget as a child of the canvas
        self.dark_mode_toggle_switch = ToggleSwitch(self.canvas, on_toggle_callback=self.toggle_dark_mode,
                                                    initial_state=self.dark_mode,
                                                    bg=self.bg_color) # Pass the initial background color here
        # Use create_window to place the toggle switch on the canvas
        self.toggle_switch_window_id = self.canvas.create_window(0, 0, window=self.dark_mode_toggle_switch, anchor="nw") # Initial position, will be updated


        self.show_welcome()

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.set_colors()
        # Update the ToggleSwitch's internal state so it redraws with the correct colors
        self.dark_mode_toggle_switch.state = self.dark_mode
        self.dark_mode_toggle_switch.draw_switch()
        
        # Also update the background of the toggle switch canvas itself
        self.dark_mode_toggle_switch.config(bg=self.bg_color)


        if hasattr(self, '_current_screen_func') and self._current_screen_func:
            self._current_screen_func()
        else:
            self.show_welcome()

    def on_canvas_resize(self, event):
        if self.original_bg_image:
            resized_image = self.original_bg_image.resize((event.width, event.height), Image.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(resized_image)
            
            if hasattr(self, 'canvas_bg') and self.canvas_bg:
                self.canvas.itemconfig(self.canvas_bg, image=self.bg_photo)
            else:
                self.canvas_bg = self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")
            self.canvas.tag_lower(self.canvas_bg) # Ensure image is at the bottom
        else:
            self.canvas.config(bg="lightgray")

        min_frame_width = 300
        min_frame_height = 450
        
        max_frame_width = 500
        max_frame_height = 600

        desired_frame_width = event.width * 0.5
        desired_frame_height = event.height * 0.7

        frame_width = max(min_frame_width, min(max_frame_width, desired_frame_width))
        frame_height = max(min_frame_height, min(max_frame_height, desired_frame_height))

        x_center = event.width / 2
        y_center = event.height / 2

        if self.main_window_id:
            self.canvas.coords(self.main_window_id, x_center, y_center)
            self.canvas.itemconfig(self.main_window_id, width=frame_width, height=frame_height)
        else:
            self.main_window_id = self.canvas.create_window(x_center, y_center,
                                                            window=self.main_frame,
                                                            anchor="center",
                                                            width=frame_width,
                                                            height=frame_height)
        self.main_frame.config(bg=self.bg_color)
        
        # Position the toggle switch in the top-right corner of the canvas
        toggle_x = event.width - self.dark_mode_toggle_switch.width - 20 # 20px padding from right
        toggle_y = 20 # 20px padding from top
        self.canvas.coords(self.toggle_switch_window_id, toggle_x, toggle_y)


    def set_colors(self):
        if self.dark_mode:
            self.bg_color = "#2b2b2b"
            self.fg_color = "white"
            self.button_bg = "#555555"
            self.button_fg = "white"
            self.active_button_bg = "#777777"
        else:
            self.bg_color = "#e0e0e0" # Light grey
            self.fg_color = "#0d47a1"
            self.button_bg = "#1976d2"
            self.button_fg = "white"
            self.active_button_bg = "#1565c0"
        
        if hasattr(self, 'main_frame') and self.main_frame:
            self.main_frame.config(bg=self.bg_color)
            for widget in self.main_frame.winfo_children():
                if 'bg' in widget.config():
                    widget.config(bg=self.bg_color)
                if 'fg' in widget.config() and not isinstance(widget, tk.Entry):
                    widget.config(fg=self.fg_color)
                if isinstance(widget, tk.Button):
                    widget.config(bg=self.button_bg, fg=self.button_fg, activebackground=self.active_button_bg)
        
        # Update the background of the toggle switch canvas directly
        if hasattr(self, 'dark_mode_toggle_switch') and self.dark_mode_toggle_switch:
            self.dark_mode_toggle_switch.config(bg=self.bg_color)


    def create_button(self, text, command):
        btn = tk.Button(self.main_frame, text=text, font=("Arial", 14),
                         bg=self.button_bg, fg=self.button_fg, relief="flat",
                         padx=10, pady=5,
                         activebackground=self.active_button_bg,
                         activeforeground="white", cursor="hand2",
                         command=command)
        btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.active_button_bg))
        btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.button_bg))
        return btn

    def show_welcome(self):
        self.clear_frame()
        self._current_screen_func = self.show_welcome
        tk.Label(self.main_frame, text="Mongo ATM", font=("Arial", 20),
                 bg=self.bg_color, fg=self.fg_color).pack(pady=30)

        self.create_button("Insert Card", command=self.login_screen).pack(pady=10)
        self.create_button("Create Account", command=self.create_account_screen).pack(pady=10)

    def create_account_screen(self):
        self.clear_frame()
        self._current_screen_func = self.create_account_screen
        tk.Label(self.main_frame, text="Create New Account", font=("Arial", 18),
                 bg=self.bg_color, fg=self.fg_color).pack(pady=20)

        tk.Label(self.main_frame, text="Card Number:", font=("Arial", 14),
                 bg=self.bg_color, fg=self.fg_color).pack()
        self.new_card_entry = tk.Entry(self.main_frame, font=("Arial", 14))
        self.new_card_entry.pack(pady=5)

        tk.Label(self.main_frame, text="4-digit PIN:", font=("Arial", 14),
                 bg=self.bg_color, fg=self.fg_color).pack()
        self.new_pin_entry = tk.Entry(self.main_frame, show="*", font=("Arial", 14))
        self.new_pin_entry.pack(pady=5)

        self.create_button("Create", command=self.create_account).pack(pady=10)
        self.create_button("Back", command=self.show_welcome).pack(pady=10)

    def create_account(self):
        card = self.new_card_entry.get()
        pin = self.new_pin_entry.get()
        if not card:
            self.show_message("Card number cannot be empty.")
            return
        if accounts_collection.find_one({"card": card}):
            self.show_message("Card number already exists. Please choose another.")
            return
        if not pin or len(pin) != 4 or not pin.isdigit():
            self.show_message("PIN must be 4 digits.")
            return

        new_account = {"card": card, "pin": pin, "balance": 0.0, "transactions": []}
        accounts_collection.insert_one(new_account)
        self.show_message("Account created successfully!", go_back=self.show_welcome)

    def login_screen(self):
        self.clear_frame()
        self._current_screen_func = self.login_screen
        tk.Label(self.main_frame, text="Login", font=("Arial", 18),
                 bg=self.bg_color, fg=self.fg_color).pack(pady=20)

        tk.Label(self.main_frame, text="Card Number:", font=("Arial", 14),
                 bg=self.bg_color, fg=self.fg_color).pack()
        self.card_entry = tk.Entry(self.main_frame, font=("Arial", 14))
        self.card_entry.pack(pady=5)

        tk.Label(self.main_frame, text="PIN:", font=("Arial", 14),
                 bg=self.bg_color, fg=self.fg_color).pack()
        self.pin_entry = tk.Entry(self.main_frame, show="*", font=("Arial", 14))
        self.pin_entry.pack(pady=5)

        self.create_button("Login", command=self.authenticate).pack(pady=20)
        self.create_button("Back", command=self.show_welcome).pack(pady=10)

    def authenticate(self):
        card = self.card_entry.get()
        pin = self.pin_entry.get()
        user = accounts_collection.find_one({"card": card, "pin": pin})
        if user:
            self.current_user = card
            self.main_menu()
        else:
            self.show_message("Invalid Card Number or PIN")

    def main_menu(self):
        self.clear_frame()
        self._current_screen_func = self.main_menu
        tk.Label(self.main_frame, text="Main Menu", font=("Arial", 20),
                 bg=self.bg_color, fg=self.fg_color).pack(pady=10)

        menu_buttons_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        menu_buttons_frame.pack(pady=20, fill="both", expand=True)

        options = [
            ("Withdraw Cash", self.withdraw_screen),
            ("Deposit Cash", self.deposit_screen),
            ("Balance Inquiry", self.show_balance_screen),
            ("Mini Statement", self.show_mini_statement_screen),
            ("Change PIN", self.change_pin_screen),
            ("Money Transfer", self.transfer_money_screen),
            ("Logout", self.logout)
        ]

        for i, (text, func) in enumerate(options):
            btn = tk.Button(menu_buttons_frame, text=text, font=("Arial", 14),
                             bg=self.button_bg, fg=self.button_fg, relief="flat",
                             padx=10, pady=5,
                             activebackground=self.active_button_bg,
                             activeforeground="white", cursor="hand2",
                             command=func)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.active_button_bg))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.button_bg))
            btn.grid(row=i, column=0, padx=10, pady=5, sticky="ew")

        menu_buttons_frame.grid_columnconfigure(0, weight=1)
        for i in range(len(options)):
            menu_buttons_frame.grid_rowconfigure(i, weight=1)

    def transaction_screen(self, title, action_func):
        self.clear_frame()
        self._current_screen_func = lambda: self.transaction_screen(title, action_func)
        
        tk.Label(self.main_frame, text=title, font=("Arial", 20),
                 bg=self.bg_color, fg=self.fg_color).pack(pady=20)

        tk.Label(self.main_frame, text="Enter amount:", font=("Arial", 14),
                 bg=self.bg_color, fg=self.fg_color).pack()
        self.amount_entry = tk.Entry(self.main_frame, font=("Arial", 14))
        self.amount_entry.pack(pady=10)

        self.create_button(title, action_func).pack(pady=5)
        self.create_button("Back", command=self.main_menu).pack(pady=5)

    def withdraw(self):
        try:
            amount = float(self.amount_entry.get())
            if amount <= 0:
                self.show_message("Amount must be positive.")
                return

            user = accounts_collection.find_one({"card": self.current_user})
            if user['balance'] >= amount:
                accounts_collection.update_one(
                    {"card": self.current_user},
                    {"$inc": {"balance": -amount},
                     "$push": {"transactions": self.get_transaction(f"Withdrawn: ${amount:.2f}")}}
                )
                self.show_message(f"Withdrawn ${amount:.2f}", go_back=self.main_menu)
            else:
                self.show_message("Not enough balance")
        except ValueError:
            self.show_message("Invalid amount")

    def deposit_screen(self):
        self.transaction_screen("Deposit Cash", self.deposit)

    def withdraw_screen(self):
        self.transaction_screen("Withdraw Cash", self.withdraw)

    def deposit(self):
        try:
            amount = float(self.amount_entry.get())
            if amount <= 0:
                self.show_message("Amount must be positive.")
                return

            accounts_collection.update_one(
                {"card": self.current_user},
                {"$inc": {"balance": amount},
                 "$push": {"transactions": self.get_transaction(f"Deposited: ${amount:.2f}")}}
            )
            self.show_message(f"Deposited ${amount:.2f}", go_back=self.main_menu)
        except ValueError:
            self.show_message("Invalid amount")

    def show_balance_screen(self):
        self.clear_frame()
        self._current_screen_func = self.show_balance_screen
        user = accounts_collection.find_one({"card": self.current_user})
        tk.Label(self.main_frame, text="Balance Inquiry", font=("Arial", 20),
                 bg=self.bg_color, fg=self.fg_color).pack(pady=20)
        tk.Label(self.main_frame, text=f"Current Balance: ${user['balance']:.2f}", font=("Arial", 16),
                 bg=self.bg_color, fg=self.fg_color).pack(pady=10)
        self.create_button("Back", command=self.main_menu).pack(pady=10)

    def show_mini_statement_screen(self):
        self.clear_frame()
        self._current_screen_func = self.show_mini_statement_screen
        user = accounts_collection.find_one({"card": self.current_user})
        transactions = user.get('transactions', [])[-5:]
        tk.Label(self.main_frame, text="Mini Statement", font=("Arial", 20),
                 bg=self.bg_color, fg=self.fg_color).pack(pady=20)
        if not transactions:
            tk.Label(self.main_frame, text="No recent transactions", font=("Arial", 14),
                     bg=self.bg_color, fg=self.fg_color).pack()
        else:
            for txn in transactions:
                tk.Label(self.main_frame, text=txn, font=("Arial", 12),
                         bg=self.bg_color, fg=self.fg_color).pack()
        self.create_button("Back", command=self.main_menu).pack(pady=10)

    def change_pin_screen(self):
        self.clear_frame()
        self._current_screen_func = self.change_pin_screen
        tk.Label(self.main_frame, text="Change PIN", font=("Arial", 20),
                 bg=self.bg_color, fg=self.fg_color).pack(pady=20)

        tk.Label(self.main_frame, text="Old PIN:", font=("Arial", 14), bg=self.bg_color, fg=self.fg_color).pack()
        self.old_pin_entry = tk.Entry(self.main_frame, show='*', font=("Arial", 14))
        self.old_pin_entry.pack(pady=5)

        tk.Label(self.main_frame, text="New PIN (4 digits):", font=("Arial", 14), bg=self.bg_color, fg=self.fg_color).pack()
        self.new_pin_entry = tk.Entry(self.main_frame, show='*', font=("Arial", 14))
        self.new_pin_entry.pack(pady=5)

        tk.Label(self.main_frame, text="Confirm New PIN:", font=("Arial", 14), bg=self.bg_color, fg=self.fg_color).pack()
        self.confirm_pin_entry = tk.Entry(self.main_frame, show='*', font=("Arial", 14))
        self.confirm_pin_entry.pack(pady=5)

        self.create_button("Change", command=self.change_pin).pack(pady=10)
        self.create_button("Back", command=self.main_menu).pack(pady=5)

    def change_pin(self):
        user = accounts_collection.find_one({"card": self.current_user})
        old_pin = self.old_pin_entry.get()
        new_pin = self.new_pin_entry.get()
        confirm_pin = self.confirm_pin_entry.get()

        if old_pin != user['pin']:
            self.show_message("Incorrect old PIN")
            return

        if not new_pin or len(new_pin) != 4 or not new_pin.isdigit():
            self.show_message("New PIN must be 4 digits.")
            return

        if new_pin != confirm_pin:
            self.show_message("New PINs do not match")
            return

        accounts_collection.update_one({"card": self.current_user}, {"$set": {"pin": new_pin}})
        self.show_message("PIN changed successfully", go_back=self.main_menu)

    def transfer_money_screen(self):
        self.clear_frame()
        self._current_screen_func = self.transfer_money_screen
        tk.Label(self.main_frame, text="Transfer Money", font=("Arial", 20),
                 bg=self.bg_color, fg=self.fg_color).pack(pady=20)

        tk.Label(self.main_frame, text="Receiver Card Number:", font=("Arial", 14), bg=self.bg_color, fg=self.fg_color).pack()
        self.receiver_entry = tk.Entry(self.main_frame, font=("Arial", 14))
        self.receiver_entry.pack(pady=5)

        tk.Label(self.main_frame, text="Amount:", font=("Arial", 14), bg=self.bg_color, fg=self.fg_color).pack()
        self.transfer_amount_entry = tk.Entry(self.main_frame, font=("Arial", 14))
        self.transfer_amount_entry.pack(pady=5)

        self.create_button("Transfer", command=self.transfer_money).pack(pady=10)
        self.create_button("Back", command=self.main_menu).pack(pady=5)

    def transfer_money(self):
        receiver = self.receiver_entry.get()
        try:
            amount = float(self.transfer_amount_entry.get())
            if amount <= 0:
                self.show_message("Transfer amount must be positive.")
                return

            sender_data = accounts_collection.find_one({"card": self.current_user})
            receiver_data = accounts_collection.find_one({"card": receiver})

            if receiver == self.current_user:
                self.show_message("Cannot transfer to the same account.")
                return

            if not receiver_data:
                self.show_message("Receiver card number does not exist.")
                return

            if sender_data['balance'] < amount:
                self.show_message("Insufficient funds for transfer.")
                return

            accounts_collection.update_one(
                {"card": self.current_user},
                {"$inc": {"balance": -amount},
                 "$push": {"transactions": self.get_transaction(f"Transferred ${amount:.2f} to {receiver}")}}
            )
            accounts_collection.update_one(
                {"card": receiver},
                {"$inc": {"balance": amount},
                 "$push": {"transactions": self.get_transaction(f"Received ${amount:.2f} from {self.current_user}")}}
            )
            self.show_message(f"Transferred ${amount:.2f} to {receiver}", go_back=self.main_menu)

        except ValueError:
            self.show_message("Invalid amount. Please enter a number.")
        except Exception as e:
            self.show_message(f"An error occurred: {e}")

    def logout(self):
        self.current_user = None
        self.show_message("Logged out successfully", go_back=self.show_welcome)

    def show_message(self, text, go_back=None):
        self.clear_frame()
        message_color = "green" if "success" in text.lower() or "withdrawn" in text.lower() or "deposited" in text.lower() or "transferred" in text.lower() else "red"
        tk.Label(self.main_frame, text=text, font=("Arial", 16), bg=self.bg_color, fg=message_color).pack(pady=30)
        if go_back:
            self.master.after(2000, go_back)

    def get_transaction(self, description):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        return f"{timestamp} - {description}"

    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.main_frame.config(bg=self.bg_color)


if __name__ == '__main__':
    root = tk.Tk()
    atm = ATMInterface(root)
    root.mainloop()