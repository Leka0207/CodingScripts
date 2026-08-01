"""
Scientific calculator with graphing capabilities.

- Tkinter GUI with a scientific keypad (trig, logs, powers, roots, constants,
  memory) plus a live expression entry that supports keyboard input.
- A graphing tab that plots y = f(x) expressions using matplotlib, with
  pan/zoom via the standard matplotlib navigation toolbar.

Run with: python scientific_calculator.py
Requires: matplotlib, numpy (pip install matplotlib numpy)
"""

import math
import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

# Names made available inside eval()'d expressions.
SAFE_NAMES = {
    name: getattr(math, name)
    for name in dir(math)
    if not name.startswith("_")
}
SAFE_NAMES.update({
    "abs": abs,
    "round": round,
    "pi": math.pi,
    "e": math.e,
    "ln": math.log,
    "log10": math.log10,
    "log2": math.log2,
    "sqrt": math.sqrt,
})


def safe_eval(expression, variables=None):
    """Evaluate a math expression with only whitelisted names in scope."""
    scope = dict(SAFE_NAMES)
    if variables:
        scope.update(variables)
    expression = expression.replace("^", "**").replace("×", "*").replace("÷", "/")
    return eval(expression, {"__builtins__": {}}, scope)


class ScientificCalculator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Scientific Calculator")
        self.geometry("640x560")
        self.minsize(560, 480)

        self.expression = tk.StringVar(value="")
        self.memory = 0.0
        self.degree_mode = tk.BooleanVar(value=False)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        calc_tab = ttk.Frame(notebook)
        graph_tab = ttk.Frame(notebook)
        notebook.add(calc_tab, text="Calculator")
        notebook.add(graph_tab, text="Graph")

        self._build_calculator(calc_tab)
        self._build_grapher(graph_tab)

    # ---------------------------------------------------------------- calc
    def _build_calculator(self, parent):
        display = ttk.Entry(
            parent, textvariable=self.expression, font=("Consolas", 22),
            justify="right",
        )
        display.pack(fill="x", padx=8, pady=8)
        display.focus_set()
        display.bind("<Return>", lambda e: self._evaluate())

        options = ttk.Frame(parent)
        options.pack(fill="x", padx=8)
        ttk.Checkbutton(options, text="Degrees", variable=self.degree_mode).pack(side="left")

        grid = ttk.Frame(parent)
        grid.pack(fill="both", expand=True, padx=8, pady=8)

        rows = [
            ["sin", "cos", "tan", "(", ")"],
            ["asin", "acos", "atan", "pi", "e"],
            ["log10", "ln", "sqrt", "^", "!"],
            ["MC", "MR", "M+", "M-", "±"],
            ["7", "8", "9", "/", "C"],
            ["4", "5", "6", "*", "←"],
            ["1", "2", "3", "-", "="],
            ["0", ".", "x", "+", "="],
        ]

        for r, row in enumerate(rows):
            grid.columnconfigure(r, weight=1)
            for c, label in enumerate(row):
                grid.columnconfigure(c, weight=1)
                grid.rowconfigure(r, weight=1)
                btn = ttk.Button(
                    grid, text=label, command=lambda l=label: self._on_button(l)
                )
                btn.grid(row=r, column=c, sticky="nsew", padx=2, pady=2)

    def _on_button(self, label):
        if label == "C":
            self.expression.set("")
        elif label == "←":
            self.expression.set(self.expression.get()[:-1])
        elif label == "=":
            self._evaluate()
        elif label == "±":
            self._toggle_sign()
        elif label == "!":
            self._factorial()
        elif label == "MC":
            self.memory = 0.0
        elif label == "MR":
            self.expression.set(self.expression.get() + self._format(self.memory))
        elif label == "M+":
            self._memory_op(1)
        elif label == "M-":
            self._memory_op(-1)
        elif label in ("sin", "cos", "tan", "asin", "acos", "atan", "log10", "sqrt"):
            self.expression.set(self.expression.get() + f"{label}(")
        elif label == "ln":
            self.expression.set(self.expression.get() + "ln(")
        elif label == "x":
            self.expression.set(self.expression.get() + "*")
        else:
            self.expression.set(self.expression.get() + label)

    def _toggle_sign(self):
        try:
            value = self._compute(self.expression.get())
            self.expression.set(self._format(-value))
        except Exception:
            messagebox.showerror("Error", "Nothing to negate yet.")

    def _factorial(self):
        try:
            value = self._compute(self.expression.get())
            if value < 0 or value != int(value):
                raise ValueError("Factorial needs a non-negative integer.")
            self.expression.set(self._format(math.factorial(int(value))))
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _memory_op(self, sign):
        try:
            value = self._compute(self.expression.get())
            self.memory += sign * value
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _compute(self, expr_text):
        """Evaluate expr_text, converting trig args to radians in degree mode."""
        if not expr_text.strip():
            raise ValueError("Enter an expression first.")
        variables = {}
        if self.degree_mode.get():
            variables.update({
                "sin": lambda x: math.sin(math.radians(x)),
                "cos": lambda x: math.cos(math.radians(x)),
                "tan": lambda x: math.tan(math.radians(x)),
                "asin": lambda x: math.degrees(math.asin(x)),
                "acos": lambda x: math.degrees(math.acos(x)),
                "atan": lambda x: math.degrees(math.atan(x)),
            })
        return safe_eval(expr_text, variables)

    def _evaluate(self):
        try:
            result = self._compute(self.expression.get())
            self.expression.set(self._format(result))
        except ZeroDivisionError:
            messagebox.showerror("Error", "Division by zero.")
        except Exception as exc:
            messagebox.showerror("Error", f"Invalid expression: {exc}")

    @staticmethod
    def _format(value):
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        if isinstance(value, float):
            return f"{round(value, 10)}"
        return str(value)

    # -------------------------------------------------------------- grapher
    def _build_grapher(self, parent):
        controls = ttk.Frame(parent)
        controls.pack(fill="x", padx=8, pady=8)

        ttk.Label(controls, text="y =").pack(side="left")
        self.func_entry = tk.StringVar(value="sin(x)")
        entry = ttk.Entry(controls, textvariable=self.func_entry, width=30)
        entry.pack(side="left", padx=6)
        entry.bind("<Return>", lambda e: self._plot())

        ttk.Label(controls, text="x min").pack(side="left", padx=(12, 2))
        self.x_min = tk.StringVar(value="-10")
        ttk.Entry(controls, textvariable=self.x_min, width=6).pack(side="left")

        ttk.Label(controls, text="x max").pack(side="left", padx=(8, 2))
        self.x_max = tk.StringVar(value="10")
        ttk.Entry(controls, textvariable=self.x_max, width=6).pack(side="left")

        ttk.Button(controls, text="Plot", command=self._plot).pack(side="left", padx=8)

        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.axes = self.figure.add_subplot(111)
        self.axes.grid(True)
        self.axes.axhline(0, color="black", linewidth=0.8)
        self.axes.axvline(0, color="black", linewidth=0.8)

        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.canvas = FigureCanvasTkAgg(self.figure, master=canvas_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        toolbar = NavigationToolbar2Tk(self.canvas, canvas_frame)
        toolbar.update()

    def _plot(self):
        expr = self.func_entry.get()
        try:
            x_min = float(self.x_min.get())
            x_max = float(self.x_max.get())
            if x_min >= x_max:
                raise ValueError("x min must be less than x max.")
        except ValueError as exc:
            messagebox.showerror("Error", f"Invalid range: {exc}")
            return

        xs = np.linspace(x_min, x_max, 2000)
        ys = np.empty_like(xs)
        for i, x in enumerate(xs):
            try:
                ys[i] = safe_eval(expr, {"x": x})
            except Exception:
                ys[i] = np.nan

        self.axes.clear()
        self.axes.grid(True)
        self.axes.axhline(0, color="black", linewidth=0.8)
        self.axes.axvline(0, color="black", linewidth=0.8)
        self.axes.plot(xs, ys, label=f"y = {expr}")
        self.axes.legend()
        self.axes.set_xlim(x_min, x_max)
        self.canvas.draw()


if __name__ == "__main__":
    app = ScientificCalculator()
    app.mainloop()
