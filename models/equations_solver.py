class Gauss:
    def __init__(self, matrix, results):
        self.n = len(matrix)
        if any(len(row) != self.n for row in matrix):
            raise ValueError("La matriz de coeficientes debe ser cuadrada.")
        if len(results) != self.n:
            raise ValueError("El vector de resultados debe tener la misma longitud que la matriz.")
        self.matrix = [row[:] for row in matrix]  
        self.results = results[:]

    def solve(self):
        n = self.n
        a = self.matrix
        b = self.results

        for i in range(n):
            if a[i][i] == 0:
                for k in range(i+1, n):
                    if a[k][i] != 0:
                        a[i], a[k] = a[k], a[i]
                        b[i], b[k] = b[k], b[i]
                        break
                else:
                    raise ValueError("La matriz es singular o no tiene solución única.")

            pivot = a[i][i]
            for j in range(i, n):
                a[i][j] /= pivot
            b[i] /= pivot

            for k in range(i+1, n):
                factor = a[k][i]
                for j in range(i, n):
                    a[k][j] -= factor * a[i][j]
                b[k] -= factor * b[i]

        x = [0] * n
        for i in range(n-1, -1, -1):
            x[i] = b[i] - sum(a[i][j] * x[j] for j in range(i+1, n))

        return x
    