from decimal import Decimal, getcontext
from vector import Vector

getcontext().prec = 30


class Line(object):

    NO_NONZERO_ELTS_FOUND_MSG = 'No nonzero elements found'

    def __init__(self, normal_vector=None, constant_term=None):
        '''Create a Line Object; Ax + By = k'''
        self.dimension = 2

        if not normal_vector:
            all_zeros = ['0'] * self.dimension
            normal_vector = Vector(all_zeros)
        self.normal_vector = normal_vector

        if not constant_term:
            constant_term = Decimal('0')
        self.constant_term = Decimal(constant_term)

        self.set_basepoint()

    def set_basepoint(self):
        '''calculate basepoint, find the the firstnonzero coordinate,
        either (0, k/B) or (k/A, 0)'''
        try:
            n = self.normal_vector
            c = self.constant_term
            basepoint_coords = ['0'] * self.dimension

            initial_index = Line.first_nonzero_index(n)
            initial_coefficient = n[initial_index]

            basepoint_coords[initial_index] = c / initial_coefficient
            self.basepoint = Vector(basepoint_coords)

        except Exception as e:
            if str(e) == Line.NO_NONZERO_ELTS_FOUND_MSG:
                self.basepoint = None
            else:
                raise e

    def __str__(self):

        num_decimal_places = 3

        def write_coefficient(coefficient, is_initial_term=False):
            coefficient = round(coefficient, num_decimal_places)
            if coefficient % 1 == 0:
                coefficient = int(coefficient)

            output = ''

            if coefficient < 0:
                output += '-'
            if coefficient > 0 and not is_initial_term:
                output += '+'

            if not is_initial_term:
                output += ' '

            if abs(coefficient) != 1:
                output += '{}'.format(abs(coefficient))

            return output

        n = self.normal_vector

        try:
            initial_index = Line.first_nonzero_index(n)
            terms = []
            for i in range(self.dimension):
                if round(n[i], num_decimal_places) != 0:
                    terms.append(write_coefficient(
                        n[i],
                        is_initial_term=(i == initial_index)) +
                        'x_{}'.format(i + 1))
            output = ' '.join(terms)

        except Exception as e:
            if str(e) == self.NO_NONZERO_ELTS_FOUND_MSG:
                output = '0'
            else:
                raise e

        constant = round(self.constant_term, num_decimal_places)
        if constant % 1 == 0:
            constant = int(constant)
        output += ' = {}'.format(constant)

        return output

    @staticmethod
    def first_nonzero_index(iterable):
        for k, item in enumerate(iterable):
            if not MyDecimal(item).is_near_zero():
                return k
        raise Exception(Line.NO_NONZERO_ELTS_FOUND_MSG)

    def is_parallel_to(self, line2):
        '''two lines are parallel if their normal vectors are parallel'''
        return self.normal_vector.is_parallel_to(line2.normal_vector)

    def __eq__(self, line2):
        '''two lines are equal if and only if the vector connecting one point on
        each line is orthogonall to the line\'s normal vector'''
        # normal vector's have to be parallel in order to be equal
        if not self.is_parallel_to(line2):
            return False

        v_connect = self.basepoint.minus(line2.basepoint)
        return v_connect.is_orthogonal_to(self.normal_vector)

    def intersects_with(self, line2):
        '''determine intersection point with line2'''
        a, b = self.normal_vector
        c, d = line2.normal_vector
        k1, k2 = self.constant_term, line2.constant_term
        denom = ((a * d) - (b * c))
        if MyDecimal(denom).is_near_zero():
            if self == line2:
                return self
            else:
                return None
        one_over_denom = Decimal('1') / ((a * d) - (b * c))
        x = (d * k1 - b * k2)
        y = (-c * k1 + a * k2)
        return Vector([x, y]).times_scalar(one_over_denom)


class MyDecimal(Decimal):
    def is_near_zero(self, eps=1e-10):
        return abs(self) < eps


if __name__ == '__main__':

    print('################################')
    print('Quiz: Coding Functions for Lines')

    l1 = Line(Vector([4.046, 2.836]), 1.21)
    l2 = Line(Vector([10.115, 7.09]), 3.025)
    print('intersection at: {0}'.format(l1.intersects_with(l2)))
    print('same line: {0}'.format(l1 == l2))

    l3 = Line(Vector([7.204, 3.182]), 8.68)
    l4 = Line(Vector([8.172, 4.114]), 9.883)
    print('intersection at: {0}'.format(l3.intersects_with(l4)))
    print('same line: {0}'.format(l3 == l4))

    l5 = Line(Vector([1.182, 5.562]), 6.744)
    l6 = Line(Vector([1.773, 8.343]), 9.525)
    print('intersection at: {0}'.format(l5.intersects_with(l6)))
    print('same line: {0}'.format(l5 == l6))
