# models/properties.py
from fractions import Fraction

class Properties:
    def __init__(self, u, v, scalar, dimension, use_fractions=True):
        # conversión opcional a fracciones
        toF = (lambda x: Fraction(x).limit_denominator()) if use_fractions else (lambda x: x)
        self.u = [toF(x) for x in u]
        self.v = [toF(x) for x in v]
        self.scalar = toF(scalar)
        self.dimension = dimension
        self.use_fractions = use_fractions

        self.zero = [toF(0)] * dimension
        self.opposite_u = [-x for x in self.u]

    def sum_vectors(self, a, b):
        return [ai + bi for ai, bi in zip(a, b)]

    def scalar_mult(self, k, a):
        return [k * ai for ai in a]

    def get_computations(self):
        u, v, k = self.u, self.v, self.scalar
        sum_uv     = self.sum_vectors(u, v)
        sum_vu     = self.sum_vectors(v, u)
        k_u        = self.scalar_mult(k, u)
        sum_u_zero = self.sum_vectors(u, self.zero)
        sum_u_opp  = self.sum_vectors(u, self.opposite_u)

        # asociativa de la suma: tomamos w = k·v
        w          = self.scalar_mult(k, v)
        sum_uv_w   = self.sum_vectors(sum_uv, w)
        sum_u_vw   = self.sum_vectors(u, self.sum_vectors(v, w))

        return {
            'sum_uv': sum_uv,
            'sum_vu': sum_vu,
            'k_u': k_u,
            'zero': self.zero,
            'opposite_u': self.opposite_u,
            'sum_u_zero': sum_u_zero,
            'sum_u_opp': sum_u_opp,
            'w': w,
            'sum_uv_w': sum_uv_w,
            'sum_u_vw': sum_u_vw
        }

    def get_verifications(self):
        c = self.get_computations()
        return {
            'commutative':     c['sum_uv'] == c['sum_vu'],
            'associative':     c['sum_uv_w'] == c['sum_u_vw'],
            'zero_exists':     c['sum_u_zero'] == self.u,
            'opposite_exists': c['sum_u_opp'] == self.zero
        }
