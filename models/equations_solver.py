import math
from fractions import Fraction

class Gauss:
    def __init__(self, matrix, results):
        self.n = len(matrix)
        if any(len(row) != self.n for row in matrix):
            raise ValueError("La matriz de coeficientes debe ser cuadrada.")
        if len(results) != self.n:
            raise ValueError("El vector de resultados debe tener la misma longitud que la matriz.")
        self.matrix = [row[:] for row in matrix]  
        self.results = results[:]
        self.steps = []

    def _format_number(self, num):
        """Format number as fraction or integer when possible"""
        if abs(num) < 1e-10:
            return "0"
        
        # Try to convert to fraction
        try:
            frac = Fraction(num).limit_denominator(1000)
            if abs(float(frac) - num) < 1e-10:
                if frac.denominator == 1:
                    return str(frac.numerator)
                else:
                    return f"{frac.numerator}/{frac.denominator}"
        except:
            pass
        
        # If not a nice fraction, check if it's close to an integer
        if abs(num - round(num)) < 1e-10:
            return str(int(round(num)))
        
        # Otherwise return formatted decimal
        return f"{num:.3f}"

    def _add_step(self, description, matrix_state, results_state):
        """Add a step to the solution process"""
        # Format numbers for display
        formatted_matrix = []
        for row in matrix_state:
            formatted_row = [self._format_number(cell) for cell in row]
            formatted_matrix.append(formatted_row)
        
        formatted_results = [self._format_number(result) for result in results_state]
        
        self.steps.append({
            'description': description,
            'matrix': formatted_matrix,
            'results': formatted_results
        })

    def solve(self):
        n = self.n
        a = self.matrix
        b = self.results

        self._add_step("Matriz inicial del sistema", a, b)

        for i in range(n):
            # Find pivot
            if a[i][i] == 0:
                for k in range(i+1, n):
                    if a[k][i] != 0:
                        self._add_step(f"F{i+1} ↔ F{k+1}", a, b)
                        a[i], a[k] = a[k], a[i]
                        b[i], b[k] = b[k], b[i]
                        break
                else:
                    raise ValueError("No tiene solución")

            # Normalize pivot row
            pivot = a[i][i]
            self._add_step(f"F{i+1} → F{i+1} ÷ {self._format_number(pivot)}", a, b)
            for j in range(i, n):
                a[i][j] /= pivot
            b[i] /= pivot

            # Eliminate column elements (both below AND above for complete elimination)
            for k in range(n):
                if k != i:  # Skip the pivot row
                    factor = a[k][i]
                    if abs(factor) > 1e-10:  # Only if factor is significant
                        self._add_step(f"F{k+1} → F{k+1} - ({self._format_number(factor)}) × F{i+1}", a, b)
                        for j in range(i, n):
                            a[k][j] -= factor * a[i][j]
                        b[k] -= factor * b[i]

        self._add_step("Solución del sistema:", a, b)

        x = [0] * n
        for i in range(n):
            x[i] = b[i]

        return x

    def get_steps(self):
        """Return the solution steps"""
        return self.steps
