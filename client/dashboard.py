from tkinter import ttk
from data_manager import user_metrics, workout_history

def show_dashboard(root, clear_window, show_workout_page):
    clear_window()

    ttk.Label(root, text="Dashboard", font=("Helvetica", 18, "bold")).pack(pady=10)

    # Metrics Section
    metrics_frame = ttk.Frame(root, padding=10)
    metrics_frame.pack(pady=10, fill="x")
    for key, value in user_metrics.items():
        ttk.Label(metrics_frame, text=f"{key}: {value}", font=("Helvetica", 12)).pack(anchor="w")

    # Workout History Section
    ttk.Label(root, text="Workout History", font=("Helvetica", 16, "bold")).pack(pady=10)
    history_frame = ttk.Frame(root, padding=10)
    history_frame.pack(pady=10, fill="x")
    for entry in workout_history:
        ttk.Label(
            history_frame,
            text=f"{entry['date']} - {entry['exercise']} - Reps: {entry['reps'][0]}",
            font=("Helvetica", 12),
        ).pack(anchor="w")

    # Start New Workout Button
    ttk.Button(
        root,
        text="Start New Lat Pulldowns Exercise",
        command=lambda: show_workout_page(root, clear_window, "Lat Pulldowns")
    ).pack(pady=20)
    ttk.Button(
        root,
        text="Start New Triceps Extension Exercise",
        command=lambda: show_workout_page(root, clear_window, "Triceps Extension")
    ).pack(pady=20)
