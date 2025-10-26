import random
import string
import tkinter as tk
from tkinter import messagebox

# Generate Password Function
def generate_password():
    length = int(length_entry.get())

    if length < 6:
        messagebox.showwarning("Weak Password", "Password length should be at least 6!")
        return

    characters = ""
    if var1.get(): characters += string.ascii_lowercase
    if var2.get(): characters += string.ascii_uppercase
    if var3.get(): characters += string.digits
    if var4.get(): characters += string.punctuation

    if characters == "":
        messagebox.showerror("Error", "Select at least one option!")
        return

    password = "".join(random.choice(characters) for _ in range(length))
    result_entry.delete(0, tk.END)
    result_entry.insert(0, password)

# Copy Password
def copy_to_clipboard():
    password = result_entry.get()
    window.clipboard_clear()
    window.clipboard_append(password)
    messagebox.showinfo("Copied", "Password copied to clipboard!")

# GUI Window Setup
window = tk.Tk()
window.title("Random Password Generator")
window.geometry("400x350")
window.config(bg="#e3f2fd")

label = tk.Label(window, text="Password Length:", bg="#e3f2fd")
label.pack()

length_entry = tk.Entry(window)
length_entry.pack()

var1 = tk.BooleanVar()
var2 = tk.BooleanVar()
var3 = tk.BooleanVar()
var4 = tk.BooleanVar()

tk.Checkbutton(window, text="Include Lowercase", variable=var1, bg="#e3f2fd").pack()
tk.Checkbutton(window, text="Include Uppercase", variable=var2, bg="#e3f2fd").pack()
tk.Checkbutton(window, text="Include Numbers", variable=var3, bg="#e3f2fd").pack()
tk.Checkbutton(window, text="Include Symbols", variable=var4, bg="#e3f2fd").pack()

generate_btn = tk.Button(window, text="Generate Password", command=generate_password)
generate_btn.pack(pady=10)

result_entry = tk.Entry(window, width=30)
result_entry.pack(pady=5)

copy_btn = tk.Button(window, text="Copy to Clipboard", command=copy_to_clipboard)
copy_btn.pack()

window.mainloop()