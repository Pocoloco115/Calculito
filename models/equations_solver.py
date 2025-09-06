from fractions import Fraction

class Gauss:
    def __init__(self, matrix, results, use_fractions=True, tol=1e-12):
        if len(matrix) == 0:
            raise ValueError("La matriz no puede estar vacía.")
        self.m = len(matrix)
        self.n = len(matrix[0])
        if any(len(row) != self.n for row in matrix):
            raise ValueError("Todas las filas deben tener la misma longitud.")
        if len(results) != self.m:
            raise ValueError("El vector de resultados debe tener la misma longitud que las filas de la matriz.")

        if use_fractions:
            self.aug = [[Fraction(x).limit_denominator() for x in row] + [Fraction(b).limit_denominator()]
                        for row, b in zip(matrix, results)]
        else:
            self.aug = [[x for x in row] + [b] for row, b in zip(matrix, results)]

        self.use_fractions = use_fractions
        self.tol = tol
        self.steps = []
        self._solved = False
        self.status = None
        self.pivot_cols = []
        self.solution = None

    def _format_number(self, num):
        if isinstance(num, Fraction):
            if num.denominator == 1:
                return str(num.numerator)
            return f"{num.numerator}/{num.denominator}"
        if abs(num) < self.tol:
            return "0"
        return f"{num:.6f}"

    def _snapshot(self, description):
        matrix = [[self._format_number(c) for c in row[:-1]] for row in self.aug]
        results = [self._format_number(row[-1]) for row in self.aug]
        self.steps.append({
            "description": description,
            "matrix": matrix,
            "results": results
        })

    def _rref(self):
        m, n = self.m, self.n
        row = 0
        self._snapshot("Matriz inicial")
        for col in range(n):
            pivot_row = None
            pivot_abs = 0.0
            for r in range(row, m):
                val = abs(float(self.aug[r][col]))
                if val > pivot_abs:
                    pivot_abs = val
                    pivot_row = r
            if pivot_row is None or pivot_abs <= self.tol:
                continue

            if pivot_row != row:
                self.aug[row], self.aug[pivot_row] = self.aug[pivot_row], self.aug[row]
                self._snapshot(f"F{row+1} ↔ F{pivot_row+1}")

            pivot = self.aug[row][col]
            self.aug[row] = [val / pivot for val in self.aug[row]]
            self._snapshot(f"F{row+1} ← F{row+1} ÷ {self._format_number(pivot)}")

            for r in range(m):
                if r == row:
                    continue
                factor = self.aug[r][col]
                if (isinstance(factor, Fraction) and factor == 0) or (not isinstance(factor, Fraction) and abs(float(factor)) <= self.tol):
                    continue
                self.aug[r] = [self.aug[r][j] - factor * self.aug[row][j] for j in range(n+1)]
                self._snapshot(f"F{r+1} ← F{r+1} − ({self._format_number(factor)})·F{row+1}")

            row += 1
            if row >= m:
                break

        self._snapshot("Matriz en forma reducida (RREF)")

    def solve(self, do_rref=True):
        self.steps = []
        self._solved = False
        self.pivot_cols = []
        self.solution = None
        self.status = None

        self._rref()

        inconsistent = False
        for r in range(self.m):
            all_zero_coeffs = all(abs(float(self.aug[r][c])) <= self.tol for c in range(self.n))
            rhs_nonzero = abs(float(self.aug[r][self.n])) > self.tol
            if all_zero_coeffs and rhs_nonzero:
                inconsistent = True
                break
        if inconsistent:
            self.status = "inconsistent"
            self._snapshot("Sistema incompatible (fila 0...0 | b distinto de 0)")
            self._solved = True
            return {"status": self.status}

        pivots = {}
        for r in range(self.m):
            pivot_col = None
            for c in range(self.n):
                if abs(float(self.aug[r][c])) > self.tol:
                    pivot_col = c
                    break
            if pivot_col is not None:
                pivots[r] = pivot_col
        pivot_cols = sorted(set(pivots.values()))
        self.pivot_cols = pivot_cols
        rank = len(pivot_cols)

        if rank == self.n:
            sol = [Fraction(0) for _ in range(self.n)]
            for r, c in pivots.items():
                sol[c] = self.aug[r][self.n]
            self.status = "unique"
            self.solution = sol
            self._snapshot("Sistema compatible determinado (solución única)")
            self._solved = True
            return {"status": self.status, "solution": sol}

        free_cols = [c for c in range(self.n) if c not in pivot_cols]
        param_names = {free_cols[i]: f"t{i+1}" for i in range(len(free_cols))}

        param_solution = {}
        for j in range(self.n):
            if j in free_cols:
                param_solution[j] = {"const": Fraction(0), "params": {param_names[j]: Fraction(1)}}
            else:
                r = next(r for r, pc in pivots.items() if pc == j)
                const = self.aug[r][self.n]
                coeffs = {}
                for f in free_cols:
                    if abs(float(self.aug[r][f])) > self.tol:
                        coeffs[param_names[f]] = -self.aug[r][f]
                param_solution[j] = {"const": const, "params": coeffs}

        self.status = "infinite"
        self.solution = {"free_cols": free_cols, "params": param_names, "expr": param_solution}
        self._snapshot("Sistema compatible indeterminado (infinitas soluciones, forma paramétrica)")
        self._solved = True
        return {"status": self.status, "solution": self.solution}

    def get_steps(self):
        return self.steps

    def get_formatted_solution(self):
        if not self._solved:
            self.solve()

        if self.status == "inconsistent":
            return ["Sistema incompatible: no tiene soluciones."]
        if self.status == "unique":
            return [f"x{idx+1} = {self._format_number(val)}" for idx, val in enumerate(self.solution)]
        out = []
        expr = self.solution["expr"]
        params = self.solution["params"]
        for col, tname in params.items():
            out.append(f"{tname} = parámetro libre (corresponde a x{col+1})")
        for j in range(self.n):
            e = expr[j]
            const = e["const"]
            terms = []
            for pname, coeff in e["params"].items():
                if isinstance(coeff, Fraction) and coeff == 0:
                    continue
                coeff_str = self._format_number(coeff)
                if coeff_str.startswith('-'):
                    terms.append(f"- {coeff_str[1:]}*{pname}")
                else:
                    terms.append(f"+ {coeff_str}*{pname}")
            const_str = self._format_number(const)
            if terms:
                expr_str = const_str
                for t in terms:
                    expr_str += " " + t
            else:
                expr_str = const_str
            out.append(f"x{j+1} = {expr_str}")
        return out

