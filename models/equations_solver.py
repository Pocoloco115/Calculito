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

    def _ref(self):
        """
        Lleva la matriz aumentada a FORMA ESCALONADA (REF)
        con pivoteo parcial y eliminación SOLO por debajo.
        Devuelve la lista de posiciones de pivote en orden: [(fila, col), ...]
        """
        m, n = self.m, self.n
        row = 0
        pivot_pos = []
        self._snapshot("Matriz inicial")

        for col in range(n):
            # Buscar pivote (mayor |valor| desde 'row' hacia abajo)
            pivot_row = None
            pivot_abs = 0.0
            for r in range(row, m):
                val = abs(float(self.aug[r][col]))
                if val > pivot_abs:
                    pivot_abs = val
                    pivot_row = r
            if pivot_row is None or pivot_abs <= self.tol:
                continue

            # Intercambio si hace falta
            if pivot_row != row:
                self.aug[row], self.aug[pivot_row] = self.aug[pivot_row], self.aug[row]
                self._snapshot(f"F{row+1} ↔ F{pivot_row+1}")

            # Normalizar pivote a 1
            pivot = self.aug[row][col]
            if pivot != 0:
                self.aug[row] = [v / pivot for v in self.aug[row]]
                self._snapshot(f"F{row+1} ← F{row+1} ÷ {self._format_number(pivot)}")

            # Anular por DEBAJO del pivote
            for r in range(row + 1, m):
                factor = self.aug[r][col]
                if (isinstance(factor, Fraction) and factor == 0) or (not isinstance(factor, Fraction) and abs(float(factor)) <= self.tol):
                    continue
                self.aug[r] = [self.aug[r][j] - factor * self.aug[row][j] for j in range(n + 1)]
                self._snapshot(f"F{r+1} ← F{r+1} − ({self._format_number(factor)})·F{row+1}")

            pivot_pos.append((row, col))
            row += 1
            if row >= m:
                break

        self._snapshot("FORMA ESCALONADA (REF)")
        return pivot_pos

    def _to_rref(self, pivot_pos):
        """
        Parte desde REF y realiza la eliminación hacia ARRIBA
        para obtener RREF (forma escalonada reducida por filas).
        """
        for r, c in reversed(pivot_pos):
            for up in range(r - 1, -1, -1):
                factor = self.aug[up][c]
                if (isinstance(factor, Fraction) and factor == 0) or (not isinstance(factor, Fraction) and abs(float(factor)) <= self.tol):
                    continue
                self.aug[up] = [self.aug[up][j] - factor * self.aug[r][j] for j in range(self.n + 1)]
                self._snapshot(f"F{up+1} ← F{up+1} − ({self._format_number(factor)})·F{r+1}")

        self._snapshot("Matriz en forma reducida (RREF)")


    def solve(self, do_rref=True):
        self.steps = []
        self._solved = False
        self.pivot_cols = []
        self.solution = None
        self.status = None

        pivot_pos = self._ref()
        self._to_rref(pivot_pos)
        
        self.pivot_cols = [c for (_, c) in pivot_pos]

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

    def get_classification(self):
            """
            Devuelve un dict con:
            - consistent: bool
            - status: 'unique' | 'infinite' | 'inconsistent'
            - rank: int
            - m, n
            """
            if not self._solved:
                self.solve()
            return {
                "consistent": self.status != "inconsistent",
                "status": self.status,
                "rank": len(self.pivot_cols),
                "m": self.m,
                "n": self.n,
            }

    def get_pivot_report(self):
        """
        Lista de strings 'Columna j: ...' con el pivote de cada columna.
        Si la columna j tiene pivote, indica en qué fila está (valor 1 en RREF).
        Si no, dice 'sin pivote (variable libre)'.
        """
        if not self._solved:
            self.solve()

        # Mapa columna->fila del pivote (a partir de self.aug ya en RREF)
        col2row = {}
        row = 0
        for c in range(self.n):
            if row < self.m and (abs(float(self.aug[row][c])) if not isinstance(self.aug[row][c], Fraction) else self.aug[row][c] != 0):
                # En RREF, si hay pivote debe ser 1; pero no dependemos de eso para localizarlo
                col2row[c] = row
                row += 1

        report = []
        for j in range(self.n):
            if j in col2row:
                report.append(f"Columna {j+1}: pivote en fila {col2row[j]+1} (valor 1)")
            else:
                report.append(f"Columna {j+1}: sin pivote (variable libre)")
        return report