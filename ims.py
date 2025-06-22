import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import json
import os
from datetime import datetime

# File paths
INVENTORY_FILE = "inventory.json"
SALES_FILE = "sales.json"
USERS_FILE = "users.json"

# Initialize files
def init_files():
    for file in [INVENTORY_FILE, SALES_FILE, USERS_FILE]:
        if not os.path.exists(file):
            with open(file, 'w') as f:
                if file == USERS_FILE:
                    json.dump({"admin": "password"}, f)
                else:
                    json.dump({} if file == INVENTORY_FILE else [], f)

# Load data from file
def load_data(file_name):
    try:
        with open(file_name, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {} if file_name == INVENTORY_FILE else []

# Save data to file
def save_data(data, file_name):
    with open(file_name, 'w') as file:
        json.dump(data, file, indent=4)

# Authentication functions
def authenticate(username, password):
    users = load_data(USERS_FILE)
    return username in users and users[username] == password

def register_user(username, password):
    users = load_data(USERS_FILE)
    if username in users:
        return False
    users[username] = password
    save_data(users, USERS_FILE)
    return True

# Inventory system
class InventorySystem:
    def __init__(self):
        self.inventory = self.load_inventory_with_migration()
        self.sales = load_data(SALES_FILE)

    def load_inventory_with_migration(self):
        raw_data = load_data(INVENTORY_FILE)
        migrated = False
        new_data = {}

        for pid, details in raw_data.items():
            pid = str(pid)
            if not isinstance(details, dict):
                continue
            if 'price' not in details:
                details['price'] = 0.0
                migrated = True
            if 'category' not in details:
                details['category'] = 'Uncategorized'
                migrated = True
            if 'name' not in details:
                details['name'] = 'Unknown'
                migrated = True
            if 'quantity' not in details:
                details['quantity'] = 0
                migrated = True
            new_data[pid] = details

        if migrated:
            save_data(new_data, INVENTORY_FILE)

        return new_data

    def add_product(self, product_id, name, price, quantity, category):
        product_id = str(product_id)
        if product_id in self.inventory:
            return False
        self.inventory[product_id] = {
            "name": name,
            "price": float(price),
            "quantity": int(quantity),
            "category": category
        }
        save_data(self.inventory, INVENTORY_FILE)
        return True

    def update_product(self, product_id, name, price, quantity, category):
        product_id = str(product_id)
        if product_id not in self.inventory:
            return False
        self.inventory[product_id] = {
            "name": name,
            "price": float(price),
            "quantity": int(quantity),
            "category": category
        }
        save_data(self.inventory, INVENTORY_FILE)
        return True

    def delete_product(self, product_id):
        product_id = str(product_id)
        if product_id not in self.inventory:
            return False
        del self.inventory[product_id]
        save_data(self.inventory, INVENTORY_FILE)
        return True

    def record_sale(self, product_id, quantity_sold):
        product_id = str(product_id)
        if product_id not in self.inventory:
            return False
        if self.inventory[product_id]["quantity"] < quantity_sold:
            return False

        self.inventory[product_id]["quantity"] -= quantity_sold
        sale_record = {
            "product_id": product_id,
            "name": self.inventory[product_id]["name"],
            "quantity": quantity_sold,
            "price": self.inventory[product_id]["price"],
            "total": self.inventory[product_id]["price"] * quantity_sold,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.sales.append(sale_record)
        save_data(self.inventory, INVENTORY_FILE)
        save_data(self.sales, SALES_FILE)
        return True

    def get_low_stock(self, threshold=5):
        return {pid: details for pid, details in self.inventory.items() if details["quantity"] < threshold}

    def get_sales_summary(self):
        total_sales = sum(sale["total"] for sale in self.sales)
        return {
            "total_transactions": len(self.sales),
            "total_revenue": total_sales,
            "top_selling": sorted(self.sales, key=lambda x: x["quantity"], reverse=True)[:5]
        }

# GUI
class InventoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Inventory Management System")
        self.root.geometry("800x600")
        self.inventory = InventorySystem()
        self.create_widgets()
        self.load_inventory()

    def create_widgets(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.inventory_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.inventory_frame, text="Inventory")

        self.tree = ttk.Treeview(self.inventory_frame, columns=("ID", "Name", "Price", "Quantity", "Category"), show="headings")
        for col in ["ID", "Name", "Price", "Quantity", "Category"]:
            self.tree.heading(col, text=col)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(self.inventory_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        btn_frame = ttk.Frame(self.inventory_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(btn_frame, text="Add Product", command=self.add_product_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Edit Product", command=self.edit_product_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Product", command=self.delete_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Record Sale", command=self.record_sale_dialog).pack(side=tk.LEFT, padx=5)

        self.reports_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.reports_frame, text="Reports")

        report_btn_frame = ttk.Frame(self.reports_frame)
        report_btn_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(report_btn_frame, text="Low Stock Alert", command=self.low_stock_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(report_btn_frame, text="Sales Summary", command=self.sales_summary).pack(side=tk.LEFT, padx=5)

        self.report_text = tk.Text(self.reports_frame, height=20, state=tk.DISABLED)
        self.report_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def load_inventory(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for pid, details in self.inventory.inventory.items():
            self.tree.insert("", "end", values=(
                pid,
                details.get("name", ""),
                f"${details.get('price', 0.0):.2f}",
                details.get("quantity", 0),
                details.get("category", "Uncategorized")
            ))

    def add_product_dialog(self):
        self._product_dialog("Add Product")

    def edit_product_dialog(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Select a product to edit")
            return
        pid = str(self.tree.item(selected[0])["values"][0])
        self._product_dialog("Edit Product", pid)

    def _product_dialog(self, title, pid=None):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x300")
        dialog.grab_set()

        if pid:
            details = self.inventory.inventory.get(pid, {})
        else:
            details = {}

        def get_entry(label, default, row):
            ttk.Label(dialog, text=label).grid(row=row, column=0, padx=10, pady=5, sticky="e")
            entry = ttk.Entry(dialog)
            entry.grid(row=row, column=1, padx=10, pady=5, sticky="we")
            entry.insert(0, default)
            return entry

        if pid:
            ttk.Label(dialog, text="Product ID:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
            ttk.Label(dialog, text=pid).grid(row=0, column=1, padx=10, pady=5, sticky="w")
        else:
            product_id_entry = get_entry("Product ID:", "", 0)

        name_entry = get_entry("Name:", details.get("name", ""), 1)
        price_entry = get_entry("Price:", str(details.get("price", 0.0)), 2)
        quantity_entry = get_entry("Quantity:", str(details.get("quantity", 0)), 3)
        category_entry = get_entry("Category:", details.get("category", "Uncategorized"), 4)

        def save():
            try:
                name = name_entry.get().strip()
                price = float(price_entry.get().strip())
                quantity = int(quantity_entry.get().strip())
                category = category_entry.get().strip()

                if not all([name, category]):
                    raise ValueError

                if pid:
                    success = self.inventory.update_product(pid, name, price, quantity, category)
                else:
                    product_id = product_id_entry.get().strip()
                    success = self.inventory.add_product(product_id, name, price, quantity, category)

                if success:
                    self.load_inventory()
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", "Operation failed")
            except:
                messagebox.showerror("Error", "Invalid input")

        ttk.Button(dialog, text="Save", command=save).grid(row=5, column=1, padx=10, pady=10, sticky="e")

    def delete_product(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Select a product to delete")
            return
        pid = str(self.tree.item(selected[0])["values"][0])
        if messagebox.askyesno("Confirm", f"Delete product {pid}?"):
            if self.inventory.delete_product(pid):
                self.load_inventory()

    def record_sale_dialog(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Select a product")
            return
        pid = str(self.tree.item(selected[0])["values"][0])
        max_qty = self.inventory.inventory[pid]["quantity"]
        qty = simpledialog.askinteger("Sale", f"Quantity (max {max_qty}):", parent=self.root, minvalue=1, maxvalue=max_qty)
        if qty:
            if self.inventory.record_sale(pid, qty):
                self.load_inventory()

    def low_stock_report(self):
        report = self.inventory.get_low_stock()
        self.report_text.config(state=tk.NORMAL)
        self.report_text.delete(1.0, tk.END)
        if not report:
            self.report_text.insert(tk.END, "No low stock items.")
        else:
            self.report_text.insert(tk.END, "LOW STOCK ALERT:\n\n")
            for pid, d in report.items():
                self.report_text.insert(tk.END, f"{pid}: {d['name']} - {d['quantity']} left\n")
        self.report_text.config(state=tk.DISABLED)

    def sales_summary(self):
        summary = self.inventory.get_sales_summary()
        self.report_text.config(state=tk.NORMAL)
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, f"Total Transactions: {summary['total_transactions']}\n")
        self.report_text.insert(tk.END, f"Total Revenue: ${summary['total_revenue']:.2f}\n\n")
        self.report_text.insert(tk.END, "Top Selling Products:\n")
        for i, p in enumerate(summary["top_selling"], 1):
            self.report_text.insert(tk.END, f"{i}. {p['name']} ({p['quantity']} sold, ${p['total']:.2f})\n")
        self.report_text.config(state=tk.DISABLED)

# Login
class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Login")
        self.root.geometry("300x200")
        self.create_widgets()

    def create_widgets(self):
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Username:").grid(row=0, column=0, sticky="e")
        self.username_entry = ttk.Entry(frame)
        self.username_entry.grid(row=0, column=1, pady=5)

        ttk.Label(frame, text="Password:").grid(row=1, column=0, sticky="e")
        self.password_entry = ttk.Entry(frame, show="*")
        self.password_entry.grid(row=1, column=1, pady=5)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)

        ttk.Button(btn_frame, text="Login", command=self.login).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Register", command=self.register).pack(side=tk.LEFT, padx=5)

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if authenticate(username, password):
            self.root.destroy()
            root = tk.Tk()
            InventoryApp(root)
            root.mainloop()
        else:
            messagebox.showerror("Login Failed", "Invalid credentials")

    def register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if register_user(username, password):
            messagebox.showinfo("Registered", "You can now log in")
        else:
            messagebox.showerror("Error", "Username already exists")

# Run the app
if __name__ == "__main__":
    init_files()
    root = tk.Tk()
    LoginWindow(root)
    root.mainloop()
