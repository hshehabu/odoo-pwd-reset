import os
import sys
import psycopg2
from passlib.context import CryptContext
from dotenv import load_dotenv
import tkinter as tk
from tkinter import messagebox, ttk

load_dotenv()

# Load environment variables
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
USER_ID = os.getenv("USER_ID")
NEW_PASSWORD = os.getenv("NEW_PASSWORD")
LOGIN = os.getenv("LOGIN")

required_vars = {
    "DB_HOST": DB_HOST,
    "DB_PORT": DB_PORT,
    "DB_USER": DB_USER,
    "DB_PASSWORD": DB_PASSWORD,
    "USER_ID": USER_ID,
    "LOGIN": LOGIN,
    "NEW_PASSWORD": NEW_PASSWORD,
}

missing = [key for key, value in required_vars.items() if value is None]
if missing:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Configuration Error",
        f"Missing required environment variables:\n{', '.join(missing)}\n\nPlease check your .env file."
    )
    sys.exit(1)

USER_ID = int(USER_ID)

pwd_context = CryptContext(
    schemes=["pbkdf2_sha512"],
    default="pbkdf2_sha512",
    pbkdf2_sha512__default_rounds=60000,
)

hashed_password = pwd_context.hash(NEW_PASSWORD)


def reset_password():
    db_name = db_entry.get().strip()
    
    if not db_name:
        messagebox.showerror("Error", "Please enter a database name!")
        return
    
    # Disable button during operation
    reset_button.config(state="disabled")
    status_label.config(text="Resetting password...", fg="blue")
    root.update()
    
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        )
        cur = conn.cursor()
        cur.execute(
            "UPDATE res_users SET login = %s, password = %s WHERE id = %s",
            (LOGIN, hashed_password, USER_ID)
        )
        
        conn.commit()
        cur.close()
        conn.close()
        
        status_label.config(text="Password reset successful!", fg="green")
        messagebox.showinfo("Success", f"Password reset successful for database: {db_name}")
        db_entry.delete(0, tk.END)
        
    except Exception as e:
        status_label.config(text=f"Error: {str(e)}", fg="red")
        messagebox.showerror("Error", f"Failed to reset password:\n{str(e)}")
    
    finally:
        reset_button.config(state="normal")


# Create GUI
root = tk.Tk()
root.title("Odoo Password Reset")
root.geometry("400x200")
root.resizable(False, False)

# Center the window
root.update_idletasks()
x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
root.geometry(f"+{x}+{y}")

# Main frame
main_frame = ttk.Frame(root, padding="20")
main_frame.pack(fill=tk.BOTH, expand=True)

# Database name label and entry
ttk.Label(main_frame, text="Database Name:", font=("Arial", 10)).pack(anchor=tk.W, pady=(0, 5))
db_entry = ttk.Entry(main_frame, font=("Arial", 11), width=30)
db_entry.pack(pady=(0, 15))
db_entry.focus()

# Reset button
reset_button = ttk.Button(main_frame, text="Reset Password", command=reset_password)
reset_button.pack(pady=(0, 10))

# Status label
status_label = ttk.Label(main_frame, text="", font=("Arial", 9))
status_label.pack()

# Bind Enter key to reset button
root.bind('<Return>', lambda e: reset_password())

# Run GUI
root.mainloop()

