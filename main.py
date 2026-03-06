import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk

# Vecindarios posibles (orden de mayor a menor valor binario)
neighborhoods = ["111", "110", "101", "100", "011", "010", "001", "000"]

def rule_to_binary(rule):
    return f"{rule:08b}"

def explain_rule(rule):
    binary = rule_to_binary(rule)
    explanation = ""
    for i, n in enumerate(neighborhoods):
        explanation += f"  {n} → {binary[i]}\n"
    return binary, explanation

def simulate(rule, width=101, steps=80):
    rule_bin = np.array([int(x) for x in rule_to_binary(rule)])
    grid = np.zeros((steps, width), dtype=int)
    grid[0, width // 2] = 1
    for t in range(1, steps):
        for i in range(1, width - 1):
            left   = int(grid[t-1, i-1])
            center = int(grid[t-1, i])
            right  = int(grid[t-1, i+1])
            pattern = (left << 2) | (center << 1) | right
            grid[t, i] = rule_bin[7 - pattern]
    return grid

class AutomataApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Explorador de Autómatas Celulares")
        self.root.configure(bg="#1a1a2e")
        self.anim = None          # referencia a la animación activa
        self.anim_running = False

        self._build_ui()

    # INTERFAZ
    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame",       background="#1a1a2e")
        style.configure("TLabel",       background="#1a1a2e", foreground="#e0e0ff",
                        font=("Courier New", 11))
        style.configure("TButton",      background="#16213e", foreground="#a0c4ff",
                        font=("Courier New", 11, "bold"), padding=6)
        style.map("TButton",            background=[("active", "#0f3460")])
        style.configure("TCombobox",    fieldbackground="#16213e", background="#16213e",
                        foreground="#e0e0ff", font=("Courier New", 11))

        # Panel izquierdo
        left = ttk.Frame(self.root, padding=14)
        left.grid(row=0, column=0, sticky="ns")

        ttk.Label(left, text="AUTÓMATA CELULAR",
                  font=("Courier New", 15, "bold"),
                  foreground="#a0c4ff").grid(row=0, column=0, columnspan=3, pady=(0,12))

        ttk.Label(left, text="Regla (0–255):").grid(row=1, column=0, sticky="w")
        self.rule_var = tk.StringVar(value="30")
        cb = ttk.Combobox(left, textvariable=self.rule_var,
                          values=[str(i) for i in range(256)], width=8)
        cb.grid(row=1, column=1, padx=6)
        cb.bind("<<ComboboxSelected>>", lambda e: self._update_rule_info())
        cb.bind("<Return>",             lambda e: self._update_rule_info())

        ttk.Label(left, text="Pasos:").grid(row=2, column=0, sticky="w", pady=(8,0))
        self.steps_var = tk.IntVar(value=80)
        ttk.Spinbox(left, from_=10, to=200, textvariable=self.steps_var,
                    width=8, font=("Courier New", 11)).grid(row=2, column=1, pady=(8,0))

        ttk.Label(left, text="Velocidad animación:").grid(row=3, column=0, sticky="w", pady=(8,0))
        self.speed_var = tk.IntVar(value=80)
        self.speed_slider = tk.Scale(
            left, from_=10, to=500, orient="horizontal",
            variable=self.speed_var, length=150,
            bg="#1a1a2e", fg="#a0c4ff", troughcolor="#16213e",
            highlightthickness=0, label="ms / paso")
        self.speed_slider.grid(row=3, column=1, columnspan=2, pady=(8,0))

        # Botones de acción
        btn_frame = ttk.Frame(left)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=14)

        ttk.Button(btn_frame, text="▶  Ver estático",
                   command=self.show_static).grid(row=0, column=0, padx=4)
        ttk.Button(btn_frame, text="⏩  Animar",
                   command=self.show_animation).grid(row=0, column=1, padx=4)
        ttk.Button(btn_frame, text="⏹  Detener",
                   command=self.stop_animation).grid(row=0, column=2, padx=4)

        # Tabla de transiciones
        ttk.Label(left, text="Transiciones:",
                  font=("Courier New", 11, "bold")).grid(row=5, column=0, columnspan=3, sticky="w")
        self.text = tk.Text(left, width=34, height=14,
                            bg="#0d0d1a", fg="#7ecfff",
                            font=("Courier New", 10), bd=0,
                            highlightbackground="#a0c4ff", highlightthickness=1)
        self.text.grid(row=6, column=0, columnspan=3, pady=6)

        # Panel derecho (canvas matplotlib)
        right = ttk.Frame(self.root, padding=6)
        right.grid(row=0, column=1, sticky="nsew")

        self.fig, self.ax = plt.subplots(figsize=(8, 5.5))
        self.fig.patch.set_facecolor("#0d0d1a")
        self.ax.set_facecolor("#0d0d1a")

        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Inicializar con la regla por defecto
        self._update_rule_info()
        self.show_static()

    # LÓGICA
    def _update_rule_info(self):
        try:
            rule = int(self.rule_var.get())
        except ValueError:
            return
        binary, explanation = explain_rule(rule)
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, f"  Regla {rule}  →  {binary}\n\n")
        self.text.insert(tk.END, "  Vecindario → Resultado\n")
        self.text.insert(tk.END, "  " + "─"*22 + "\n")
        self.text.insert(tk.END, explanation)

    def _get_params(self):
        try:
            rule  = int(self.rule_var.get())
            steps = int(self.steps_var.get())
        except ValueError:
            rule, steps = 30, 80
        width = 201
        return rule, steps, width

    def show_static(self):
        self.stop_animation()
        rule, steps, width = self._get_params()
        grid = simulate(rule, width=width, steps=steps)
        self._draw_static(grid, rule)

    def _draw_static(self, grid, rule):
        self.ax.clear()
        self.ax.imshow(grid, cmap="inferno", interpolation="nearest", aspect="auto")
        self.ax.set_title(f"Regla {rule}  —  {grid.shape[0]} generaciones",
                          color="#a0c4ff", fontsize=13, fontfamily="monospace")
        self.ax.set_xlabel("Célula", color="#7ecfff", fontsize=9)
        self.ax.set_ylabel("Generación", color="#7ecfff", fontsize=9)
        self.ax.tick_params(colors="#555577")
        for spine in self.ax.spines.values():
            spine.set_edgecolor("#333355")
        self.fig.tight_layout()
        self.canvas.draw()

    def show_animation(self):
        self.stop_animation()
        rule, steps, width = self._get_params()
        grid = simulate(rule, width=width, steps=steps)
        interval = self.speed_var.get()

        self.ax.clear()
        self.ax.set_facecolor("#0d0d1a")

        # imagen vacía inicial
        display = np.zeros_like(grid)
        self.img = self.ax.imshow(display, cmap="inferno",
                                  interpolation="nearest", aspect="auto",
                                  vmin=0, vmax=1)
        self.ax.set_title(f"Regla {rule}  —  generación 0 / {steps}",
                          color="#a0c4ff", fontsize=13, fontfamily="monospace")
        self.ax.set_xlabel("Célula", color="#7ecfff", fontsize=9)
        self.ax.set_ylabel("Generación", color="#7ecfff", fontsize=9)
        self.ax.tick_params(colors="#555577")
        for spine in self.ax.spines.values():
            spine.set_edgecolor("#333355")
        self.fig.tight_layout()

        self.anim_running = True
        current_frame = [0]
        acc_grid = np.zeros_like(grid)

        def update(frame):
            if not self.anim_running:
                return (self.img,)
            step = current_frame[0]
            if step < steps:
                acc_grid[step] = grid[step]
                self.img.set_data(acc_grid)
                self.ax.set_title(
                    f"Regla {rule}  —  generación {step+1} / {steps}",
                    color="#a0c4ff", fontsize=13, fontfamily="monospace")
                current_frame[0] += 1
            return (self.img,)

        self.anim = animation.FuncAnimation(
            self.fig, update,
            frames=steps + 5,
            interval=interval,
            blit=True,
            repeat=False
        )
        self.canvas.draw()

    def stop_animation(self):
        if self.anim is not None:
            self.anim.event_source.stop()
            self.anim = None
        self.anim_running = False

if __name__ == "__main__":
    root = tk.Tk()
    app = AutomataApp(root)
    root.mainloop()