from flask import Flask, render_template, request, url_for
from models.equations_solver import Gauss
from models.properties import Properties
from models.matrix_equation import MatrixEquation

app = Flask(__name__)

# ========= Filtros Jinja para formatear fracciones y vectores =========
def _fmt_num(x, tol=1e-9):
    # Fraction → "a/b" o "a" si es entero
    if hasattr(x, "numerator") and hasattr(x, "denominator"):
        if x.denominator == 1:
            return str(x.numerator)
        return f"{x.numerator}/{x.denominator}"
    # int/float → entero si está "casi" entero
    try:
        xf = float(x)
        if abs(xf - round(xf)) < tol:
            return str(int(round(xf)))
        # evitar "-0"
        if abs(xf) < tol:
            return "0"
        return f"{xf:.6f}".rstrip("0").rstrip(".")
    except Exception:
        return str(x)

@app.template_filter("fmt_num")
def jinja_fmt_num(x):
    return _fmt_num(x)

@app.template_filter("fmt_vec")
def jinja_fmt_vec(vec):
    return "[" + ", ".join(_fmt_num(v) for v in vec) + "]"


@app.route("/", methods=["GET"])
def home():
    return render_template("home.html")

# Ruta para sistemas de ecuaciones lineales
@app.route("/linear_system", methods=["GET", "POST"])
def linear_system():
    if request.method == "POST":
        num_vars = request.form.get("num_vars")
        num_eqs = request.form.get("num_eqs")

        if num_vars and num_eqs:
            try:
                num_vars = int(num_vars)
                num_eqs = int(num_eqs)
                if num_vars <= 0 or num_eqs <= 0 or num_vars > 10 or num_eqs > 10:
                    return render_template("index.html", step=1, error="El número de variables y ecuaciones debe ser entre 1 y 10.")
                return render_template("index.html", num_vars=num_vars, num_eqs=num_eqs, step=2)
            except ValueError:
                return render_template("index.html", step=1, error="Por favor, ingrese números válidos.")
        else:
            return render_template("index.html", step=1, error="Por favor, complete todos los campos.")

    return render_template("index.html", step=1)

@app.route("/solve", methods=["POST"])
def solve_linear_system():
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
        gauss_solver = Gauss(coefficients, results, use_fractions=True)
        solution = gauss_solver.get_formatted_solution()
        steps = gauss_solver.get_steps()
        info = gauss_solver.get_classification()
        pivot_report = gauss_solver.get_pivot_report()

        return render_template(
            "result.html",
            solution=solution,
            steps=steps,
            consistent=info["consistent"],
            tipo=("Única" if info["status"] == "unique" else ("Infinitas" if info["status"] == "infinite" else "Ninguna")),
            rank=info["rank"],
            n=info["n"],
            pivot_report=pivot_report
        )
    except Exception as e:
        error_msg = str(e) if "No tiene solución" in str(e) else "No tiene solución"
        return render_template("index.html", step=1, error=f"Error al resolver el sistema: {error_msg}")

# Ruta para propiedades algebraicas
@app.route("/properties", methods=["GET", "POST"])
def properties():
    if request.method == "POST":
        dimension = request.form.get("dimension")

        if dimension:
            try:
                dimension = int(dimension)
                if dimension <= 0 or dimension > 10:
                    return render_template("properties.html", step=1, error="La dimensión debe ser entre 1 y 10.")
                return render_template("properties.html", dimension=dimension, step=2)
            except ValueError:
                return render_template("properties.html", step=1, error="Por favor, ingrese un número válido.")
        else:
            return render_template("properties.html", step=1, error="Por favor, complete el campo.")

    return render_template("properties.html", step=1)

@app.route("/compute_properties", methods=["POST"])
def compute_properties():
    dimension = int(request.form["dimension"])
    try:
        u = [float(request.form[f"u_{i}"]) for i in range(dimension)]
        v = [float(request.form[f"v_{i}"]) for i in range(dimension)]
        scalar = float(request.form["scalar"])
    except (ValueError, KeyError):
        return render_template("properties.html", step=1, error="Error: Ingrese valores numéricos válidos.")

    try:
        props = Properties(u, v, scalar, dimension, use_fractions=True)
        verifications = props.get_verifications()
        computations = props.get_computations()

        return render_template("properties_result.html", verifications=verifications, computations=computations)
    except Exception as e:
        return render_template("properties.html", step=1, error=f"Error: {str(e)}")

# Ruta para combinación lineal
@app.route("/linear_combination", methods=["GET", "POST"])
def linear_combination():
    if request.method == "POST":
        dimension = request.form.get("dimension")
        num_vectors = request.form.get("num_vectors")

        if dimension and num_vectors:
            try:
                dimension = int(dimension)
                num_vectors = int(num_vectors)
                if dimension <= 0 or num_vectors <= 0 or dimension > 10 or num_vectors > 10:
                    return render_template("linear_combination.html", step=1, error="Los valores deben ser entre 1 y 10.")
                return render_template("linear_combination.html", dimension=dimension, num_vectors=num_vectors, step=2)
            except ValueError:
                return render_template("linear_combination.html", step=1, error="Por favor, ingrese números válidos.")
        else:
            return render_template("linear_combination.html", step=1, error="Por favor, complete todos los campos.")

    return render_template("linear_combination.html", step=1)

@app.route("/solve_linear_combination", methods=["POST"])
def solve_linear_combination():
    dimension = int(request.form["dimension"])
    num_vectors = int(request.form["num_vectors"])

    try:
        coefficients = [[float(request.form[f"v_{i}_{j}"]) for j in range(num_vectors)] for i in range(dimension)]
        results = [float(request.form[f"b_{i}"]) for i in range(dimension)]
    except (ValueError, KeyError):
        return render_template("linear_combination.html", step=1, error="Error: Ingrese valores numéricos válidos.")

    try:
        gauss_solver = Gauss(coefficients, results, use_fractions=True)
        solution = gauss_solver.get_formatted_solution()
        steps = gauss_solver.get_steps()
        info = gauss_solver.get_classification()
        pivot_report = gauss_solver.get_pivot_report()

        is_combination = info["consistent"]
        interpretation = "El vector objetivo es una combinación lineal." if is_combination else "El vector objetivo NO es una combinación lineal."

        return render_template(
            "result.html",
            solution=solution,
            steps=steps,
            consistent=info["consistent"],
            tipo=("Única" if info["status"] == "unique" else ("Infinitas" if info["status"] == "infinite" else "Ninguna")),
            rank=info["rank"],
            n=info["n"],
            pivot_report=pivot_report,
            interpretation=interpretation
        )
    except Exception as e:
        error_msg = str(e) if "No tiene solución" in str(e) else "No tiene solución"
        return render_template("linear_combination.html", step=1, error=f"Error: {error_msg}")

# Ruta para ecuación vectorial
@app.route("/vector_equation", methods=["GET", "POST"])
def vector_equation():
    if request.method == "POST":
        dimension = request.form.get("dimension")
        num_vectors = request.form.get("num_vectors")

        if dimension and num_vectors:
            try:
                dimension = int(dimension)
                num_vectors = int(num_vectors)
                if dimension <= 0 or num_vectors <= 0 or dimension > 10 or num_vectors > 10:
                    return render_template("vector_equation.html", step=1, error="Los valores deben ser entre 1 y 10.")
                return render_template("vector_equation.html", dimension=dimension, num_vectors=num_vectors, step=2)
            except ValueError:
                return render_template("vector_equation.html", step=1, error="Por favor, ingrese números válidos.")
        else:
            return render_template("vector_equation.html", step=1, error="Por favor, complete todos los campos.")

    return render_template("vector_equation.html", step=1)

@app.route("/solve_vector_equation", methods=["POST"])
def solve_vector_equation():
    dimension = int(request.form["dimension"])
    num_vectors = int(request.form["num_vectors"])

    try:
        coefficients = [[float(request.form[f"v_{i}_{j}"]) for j in range(num_vectors)] for i in range(dimension)]
        results = [float(request.form[f"b_{i}"]) for i in range(dimension)]
    except (ValueError, KeyError):
        return render_template("vector_equation.html", step=1, error="Error: Ingrese valores numéricos válidos.")

    try:
        gauss_solver = Gauss(coefficients, results, use_fractions=True)
        solution = gauss_solver.get_formatted_solution()
        steps = gauss_solver.get_steps()
        info = gauss_solver.get_classification()
        pivot_report = gauss_solver.get_pivot_report()

        return render_template(
            "result.html",
            solution=solution,
            steps=steps,
            consistent=info["consistent"],
            tipo=("Única" if info["status"] == "unique" else ("Infinitas" if info["status"] == "infinite" else "Ninguna")),
            rank=info["rank"],
            n=info["n"],
            pivot_report=pivot_report
        )
    except Exception as e:
        error_msg = str(e) if "No tiene solución" in str(e) else "No tiene solución"
        return render_template("vector_equation.html", step=1, error=f"Error: {error_msg}")

# Ruta para ecuación matricial
@app.route("/matrix_equation", methods=["GET", "POST"])
def matrix_equation():
    if request.method == "POST":
        rows_a = request.form.get("rows_a")
        cols_a = request.form.get("cols_a")
        cols_b = request.form.get("cols_b")

        if rows_a and cols_a and cols_b:
            try:
                rows_a = int(rows_a)
                cols_a = int(cols_a)
                cols_b = int(cols_b)
                if rows_a <= 0 or cols_a <= 0 or cols_b <= 0 or rows_a > 10 or cols_a > 10 or cols_b > 10:
                    return render_template("matrix_form.html", step=1, error="Los valores deben ser entre 1 y 10.")
                return render_template("matrix_form.html", rows_a=rows_a, cols_a=cols_a, cols_b=cols_b, step=2)
            except ValueError:
                return render_template("matrix_form.html", step=1, error="Por favor, ingrese números válidos.")
        else:
            return render_template("matrix_form.html", step=1, error="Por favor, complete todos los campos.")

    return render_template("matrix_form.html", step=1)

@app.route("/solve_matrix_equation", methods=["POST"])
def solve_matrix_equation():
    rows_a = int(request.form["rows_a"])
    cols_a = int(request.form["cols_a"])
    cols_b = int(request.form["cols_b"])

    try:
        A = [[float(request.form[f"a_{i}_{j}"]) for j in range(cols_a)] for i in range(rows_a)]
        B = [[float(request.form[f"b_{i}_{k}"]) for k in range(cols_b)] for i in range(rows_a)]
    except (ValueError, KeyError):
        return render_template("matrix_form.html", step=1, error="Error: Ingrese valores numéricos válidos.")

    try:
        matrix_solver = MatrixEquation(A, B, use_fractions=True)
        solutions = matrix_solver.get_formatted_solutions()
        steps = matrix_solver.get_all_steps()
        infos = matrix_solver.infos
        pivot_reports = matrix_solver.get_all_pivot_reports()
        overall_info = matrix_solver.get_overall_classification()

        return render_template(
            "matrix_result.html",
            solutions=solutions,
            steps=steps,
            infos=infos,
            pivot_reports=pivot_reports,
            overall_info=overall_info
        )
    except Exception as e:
        error_msg = str(e)
        return render_template("matrix_form.html", step=1, error=f"Error: {error_msg}")

if __name__ == "__main__":
    app.run(debug=True)
