from flask import Flask, render_template, request
from models.equations_solver import Gauss

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        num_vars = request.form.get("num_vars")
        num_eqs = request.form.get("num_eqs")

        if num_vars and num_eqs:
            try:
                num_vars = int(num_vars)
                num_eqs = int(num_eqs)
                if num_vars <= 0 or num_eqs <= 0:
                    return render_template("index.html", step=1, error="El número de variables y ecuaciones debe ser mayor que 0.")
                return render_template("index.html", num_vars=num_vars, num_eqs=num_eqs, step=2)
            except ValueError:
                return render_template("index.html", step=1, error="Por favor, ingrese números válidos.")
        else:
            return render_template("index.html", step=1, error="Por favor, complete todos los campos.")

    return render_template("index.html", step=1)

@app.route("/solve", methods=["POST"])
def solve():
    num_vars = request.form.get("num_vars")
    num_eqs = request.form.get("num_eqs")

    if not num_vars or not num_eqs:
        return render_template("index.html", step=1, error="Error: Número de variables o ecuaciones no proporcionado.")

    try:
        num_vars = int(num_vars)
        num_eqs = int(num_eqs)
        if num_vars <= 0 or num_eqs <= 0:
            return render_template("index.html", step=1, error="El número de variables y ecuaciones debe ser mayor que 0.")
    except ValueError:
        return render_template("index.html", step=1, error="Error: Número de variables o ecuaciones no válido.")

    matrix = []
    try:
        for i in range(num_eqs):
            row = []
            for j in range(num_vars + 1): 
                val = request.form.get(f"cell_{i}_{j}")
                if val is None:
                    return render_template("index.html", step=1, error=f"Error: Falta el valor en la celda ({i}, {j}).")
                row.append(float(val))
            matrix.append(row)
    except ValueError:
        return render_template("index.html", step=1, error="Error: Ingrese valores numéricos válidos en la matriz.")

    coefficients = [row[:-1] for row in matrix] 
    results = [row[-1] for row in matrix]  

    if len(coefficients) != num_eqs or any(len(row) != num_vars for row in coefficients):
        return render_template("index.html", step=1, error="Error: Dimensiones de la matriz no válidas.")
    if len(results) != num_eqs:
        return render_template("index.html", step=1, error="Error: Vector de resultados no válido.")

    try:
        gauss_solver = Gauss(coefficients, results)
        solution = gauss_solver.solve()
        steps = gauss_solver.get_steps()
    except Exception as e:
        error_msg = str(e) if "No tiene solución" in str(e) else "No tiene solución"
        return render_template("index.html", step=1, error=f"Error al resolver el sistema: {error_msg}")

    return render_template("result.html", solution=solution, steps=steps)

# Vercel needs this variable to be named 'app'
if __name__ == "__main__":
    app.run(debug=True)
