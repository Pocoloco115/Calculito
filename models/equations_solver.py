import math
from fractions import Fraction

class Gauss:
    def __init__(self, matrix, results, use_fractions=True, tol=1e-12):
        self.n = len(matrix)
        if any(len(row) != self.n for row in matrix):
            raise ValueError("La matriz de coeficientes debe ser cuadrada.")
        if len(results) != self.n:
            raise ValueError("El vector de resultados debe tener la misma longitud que la matriz.")

        # Copias profundas
        if use_fractions:
            self.matrix = [[Fraction(x).limit_denominator() for x in row] for row in matrix]
            self.results = [Fraction(b).limit_denominator() for b in results]
        else:
            self.matrix = [row[:] for row in matrix]
            self.results = results[:]

        self.use_fractions = use_fractions
        self.tol = tol
        self.steps = []

    # ---------- helpers de formato ----------
    def _format_number(self, num):
        # num puede ser Fraction o float
        if isinstance(num, Fraction):
            if num.denominator == 1:
                return str(num.numerator)
            return f"{num.numerator}/{num.denominator}"
        # float
        if abs(num) < self.tol:
            return "0"
        # intenta fracción “bonita”
        try:
            frac = Fraction(num).limit_denominator(1000)
            if abs(float(frac) - num) < 1e-10:
                if frac.denominator == 1:
                    return str(frac.numerator)
                else:
                    return f"{frac.numerator}/{frac.denominator}"
        except Exception:
            pass
        if abs(num - round(num)) < 1e-10:
            return str(int(round(num)))
        return f"{num:.6f}"

    def _snapshot(self, description):
        fm = [[self._format_number(c) for c in row] for row in self.matrix]
        fb = [self._format_number(v) for v in self.results]
        self.steps.append({"description": description, "matrix": fm, "results": fb})

    # ---------- algoritmo ----------
    def solve(self):
        n = self.n
        a = self.matrix
        b = self.results

        self._snapshot("Matriz inicial del sistema")

        for i in range(n):
            # pivoteo parcial: buscar el mayor |a[k][i]| desde i
            pivot_row = i
            pivot_abs = abs(float(a[i][i]))
            for k in range(i + 1, n):
                cand = abs(float(a[k][i]))
                if cand > pivot_abs:
                    pivot_abs = cand
                    pivot_row = k

            # si el mejor pivote está en otra fila, intercambiar
            if pivot_row != i:
                a[i], a[pivot_row] = a[pivot_row], a[i]
                b[i], b[pivot_row] = b[pivot_row], b[i]
                self._snapshot(f"F{i+1} ↔ F{pivot_row+1} (pivoteo parcial)")

            # verificar pivote no nulo
            if abs(float(a[i][i])) <= self.tol:
                raise ValueError("No tiene solución (pivote cero; sistema singular o no determinado)")

            # normalizar fila i
            pivot = a[i][i]
            a[i] = [x / pivot for x in a[i]]
            b[i] = b[i] / pivot
            self._snapshot(f"F{i+1} ← F{i+1} ÷ {self._format_number(pivot)}")

            # anular columna i en todas las demás filas
            for k in range(n):
                if k == i:
                    continue
                factor = a[k][i]
                if (isinstance(factor, Fraction) and factor == 0) or (not isinstance(factor, Fraction) and abs(float(factor)) <= self.tol):
                    continue
                a[k] = [a_kj - factor * a[i][j] for j, a_kj in enumerate(a[k])]
                b[k] = b[k] - factor * b[i]
                self._snapshot(f"F{k+1} ← F{k+1} − ({self._format_number(factor)})·F{i+1}")

        # solución (ahora A = I)
        self._snapshot("Solución del sistema")
        return [b[i] for i in range(n)]

    def get_steps(self):
        return self.steps

    def get_formatted_solution(self):
        sol = self.solve()  # asegura que esté resuelto
        return [self._format_number(x) for x in sol]