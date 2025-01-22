import tkinter as tk
from dashboard import show_dashboard
from workouts import show_workout_page

# Main App Window
root = tk.Tk()
root.title("Workout App")
root.geometry("500x500")

# Navigation Function
def clear_window():
    for widget in root.winfo_children():
        widget.destroy()

# Start with the dashboard
show_dashboard(root, clear_window, show_workout_page)

root.mainloop()
