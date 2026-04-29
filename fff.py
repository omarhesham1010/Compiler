import tkinter as tk
from tkinter import ttk

# =========================
# Data Definitions
# =========================
data_types = ["int", "char", "bool", "double", "float", "string"]
reserved_words = ["for", "while", "if", "do", "returns", "continue", "break", "end"]

symbols = ["+", "-", "*", "/", "=", "<", ">", "(", ")", "{", "}", ";", ",", "!", "%"]

# =========================
# Lexer Function
# =========================
def scan_code():
    text = input_text.get("1.0", tk.END)
    i = 0
    prev = ""

    # clear table
    for item in tree.get_children():
        tree.delete(item)

    while i < len(text):
        ch = text[i]

        # skip spaces
        if ch == " " or ch == "\n" or ch == "\t":
            i += 1
            continue

        # numbers
        if ch.isdigit():
            num = ""
            while i < len(text) and text[i].isdigit():
                num += text[i]
                i += 1
            tree.insert("", "end", values=(num, "Number"))
            continue

        # words (identifiers / reserved / datatype / variable)
        if ch.isalpha():
            word = ""
            while i < len(text) and (text[i].isalnum()):
                word += text[i]
                i += 1

            if word in data_types:
                tree.insert("", "end", values=(word, "Identifier"))
                prev = "datatype"

            elif word in reserved_words:
                tree.insert("", "end", values=(word, "Reserved"))
                prev = ""

            elif prev == "datatype":
                tree.insert("", "end", values=(word, "Variable"))
                prev = ""

            else:
                tree.insert("", "end", values=(word, "Identifier_Name"))
                prev = ""

            continue

        # double symbols
        if i+1 < len(text):
            two = text[i:i+2]
            if two == "&&" or two == "||" or two == "++" or two == "--":
                tree.insert("", "end", values=(two, "Symbol"))
                i += 2
                continue

        # single symbols
        if ch in symbols:
            tree.insert("", "end", values=(ch, "Symbol"))

        i += 1


# =========================
# Clear Function
# =========================
def clear_all():
    input_text.delete("1.0", tk.END)
    for item in tree.get_children():
        tree.delete(item)


# =========================
# GUI Setup (Dark Theme)
# =========================
root = tk.Tk()
root.title("Lexical Analyzer")
root.geometry("900x600")
root.configure(bg="#1e1e1e")

# Title
title = tk.Label(root, text="Lexical Analyzer", bg="#1e1e1e",
                 fg="white", font=("Arial", 18, "bold"))
title.pack(pady=10)

# Input Frame
frame_input = tk.Frame(root, bg="#1e1e1e")
frame_input.pack()

input_text = tk.Text(frame_input, height=10, width=90,
                      bg="#2b2b2b", fg="white",
                      insertbackground="white",
                      font=("Consolas", 12))
input_text.pack()

# Buttons Frame
frame_btn = tk.Frame(root, bg="#1e1e1e")
frame_btn.pack(pady=10)

scan_btn = tk.Button(frame_btn, text="Scan",
                     command=scan_code,
                     bg="#4CAF50", fg="white",
                     width=10, font=("Arial", 12, "bold"))

clear_btn = tk.Button(frame_btn, text="Clear",
                      command=clear_all,
                      bg="#f44336", fg="white",
                      width=10, font=("Arial", 12, "bold"))

scan_btn.grid(row=0, column=0, padx=10)
clear_btn.grid(row=0, column=1, padx=10)

# Output Table
style = ttk.Style()
style.theme_use("default")

style.configure("Treeview",
                background="#2b2b2b",
                foreground="white",
                rowheight=25,
                fieldbackground="#2b2b2b")

style.configure("Treeview.Heading",
                background="#1f1f1f",
                foreground="white")

tree = ttk.Treeview(root, columns=("Token", "Type"), show="headings")
tree.heading("Token", text="Token")
tree.heading("Type", text="Type")

tree.pack(fill="both", expand=True, pady=10)

root.mainloop()