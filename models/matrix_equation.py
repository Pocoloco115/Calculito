# models/matrix_equation.py
# Nuevo archivo para resolver A X = B con B posiblemente matriz

from models.equations_solver import Gauss  # Asumiendo que existe este import

class MatrixEquation:
    def __init__(self, A, B, use_fractions=True):
        self.A = A
        self.B = B
        self.cols_b = len(B[0]) if B else 0
        self.use_fractions = use_fractions
        self.solutions = []
        self.steps = []
        self.infos = []
        self.pivot_reports = []

        for col in range(self.cols_b):
            b_col = [row[col] for row in B]
            gauss_solver = Gauss(self.A, b_col, use_fractions=self.use_fractions)
            self.solutions.append(gauss_solver.get_formatted_solution())
            self.steps.append(gauss_solver.get_steps())
            self.infos.append(gauss_solver.get_classification())
            self.pivot_reports.append(gauss_solver.get_pivot_report())

    def get_formatted_solutions(self):
        # Devuelve las soluciones como lista de columnas de X
        return self.solutions

    def get_overall_classification(self):
        # Clasificación general: si todas consistentes, etc.
        consistent = all(info['consistent'] for info in self.infos)
        statuses = set(info['status'] for info in self.infos)
        status = list(statuses)[0] if len(statuses) == 1 else 'mixed'
        rank = self.infos[0]['rank'] if self.infos else None  # Asume mismo rank
        n = self.infos[0]['n'] if self.infos else None
        return {
            'consistent': consistent,
            'status': status,
            'rank': rank,
            'n': n
        }

    def get_all_steps(self):
        return self.steps

    def get_all_pivot_reports(self):
        return self.pivot_reports