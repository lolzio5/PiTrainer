from tkinter import ttk
import tkinter as tk
from data_manager import update_dashboard_with_new_workout
from dashboard import show_dashboard

def show_workout_page(root, clear_window, exercise_name):
    clear_window()
    # These counters are locally rendered based on the server's 
    reps_completed = tk.IntVar(value=0)
    sets_completed = tk.IntVar(value=0)
    # Logic for the server
    rep_counter=[0]
    def complete_rep():
        current_reps = reps_completed.get()
        reps_completed.set(current_reps + 1)
        rep_counter[0] += 1

    # These buttons are local, to give user the opportunity to end the set and the workout
    def complete_set():
        current_sets = reps_completed.get()
        sets_completed.set(current_sets + 1)
        reps_completed.set(0)

    def end_workout():
        current_sets = reps_completed.get()
        sets_completed.set(current_sets + 1)
        # The dashboard should be updated server side with the new entry into the database
        update_dashboard_with_new_workout(exercise_name, rep_counter)
        # This runs locally, to return to the dashboard but with the new workout
        show_dashboard(root, clear_window, show_workout_page)

    ttk.Label(root, text=f"Workout: {exercise_name}", font=("Helvetica", 18, "bold")).pack(pady=10)
    ttk.Label(root, text="Reps Completed:", font=("Helvetica", 14)).pack(pady=10)
    ttk.Label(root, textvariable=reps_completed, font=("Helvetica", 36, "bold")).pack(pady=10)

    # Complete Rep Button
    ttk.Button(root, text="Complete Rep", command=complete_rep).pack(pady=10)

    ttk.Button(root, text="Complete Set", command=complete_set).pack(pady=10)

    # End Workout Button
    ttk.Button(root, text="End Workout", command=end_workout).pack(pady=20)
