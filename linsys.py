from decimal import Decimal, getcontext
from copy import deepcopy

from vector import Vector
from hyperplane import Hyperplane

getcontext().prec = 30


class LinearSystem(object):

    PLANES_SAME_DIM_MSG = 'Hyperplanes in the system should live in the same dim.'
    NO_SOLUTIONS_MSG = 'No solutions'
    INF_SOLUTIONS_MSG = 'Infinitely many solutions'

    def __init__(self, planes):
        try:
            d = planes[0].dimension
            for p in planes:
                assert p.dimension == d

            self.planes = planes
            self.dimension = d

        except AssertionError:
            raise Exception(self.PLANES_SAME_DIM_MSG)

    def __len__(self):
        return len(self.planes)

    def __getitem__(self, i):
        return self.planes[i]

    def __setitem__(self, i, x):
        try:
            assert x.dimension == self.dimension
            self.planes[i] = x
        except AssertionError:
            raise Exception(self.PLANES_SAME_DIM_MSG)

    def __str__(self):
        ret = 'Linear System:\n'
        temp = []
        for i, p in enumerate(self.planes):
            temp.append('Equation {}: {}'.format(i + 1, p))
        ret += '\n'.join(temp)
        return ret

    def indices_of_first_nonzero_terms_in_each_row(self):
        '''calculate pivot variable indices'''
        num_equations = len(self)

        indices = [-1] * num_equations

        for i, p in enumerate(self.planes):
            try:
                indices[i] = p.first_nonzero_index(p.normal_vector.coords)
            except Exception as e:
                if str(e) == Hyperplane.NO_NONZERO_ELTS_FOUND_MSG:
                    continue
                else:
                    raise e
        return indices

    def swap_rows(self, row1, row2):
        '''swap row1 with row2'''
        self[row1], self[row2] = self[row2], self[row1]

    def multiply_coefficient_and_row(self, coefficient, row):
        '''mulitply normal vector and constant term with coefficient'''
        n = self[row].normal_vector
        k = self[row].constant_term
        new_normal_vector = n.times_scalar(coefficient)
        new_constant_term = k * coefficient
        self[row] = Hyperplane(normal_vector=new_normal_vector, constant_term=new_constant_term)

    def add_multiple_times_row_to_row(self, coefficient, from_here, to_here):
        '''add multiple times from_here row to_here row'''
        n1 = self[from_here].normal_vector
        n2 = self[to_here].normal_vector
        k1 = self[from_here].constant_term
        k2 = self[to_here].constant_term

        new_normal_vector = n1.times_scalar(coefficient).plus(n2)
        new_constant_term = (k1 * coefficient) + k2
        self[to_here] = Hyperplane(normal_vector=new_normal_vector, constant_term=new_constant_term)

    def compute_triangular_form(self):
        '''form linear equations into echelon form

        Assumptions for Test Cases:
        1. Swap with topmost row below current row
        2. Don't multiply rows by numbers
        3. Only add a multiple of a row to rows underneath
        '''
        system = deepcopy(self)
        num_equations = len(system)
        num_variables = system.dimension
        j = 0  # current variable
        for i in range(num_equations):
            while j < num_variables:
                c = MyDecimal(system[i][j])
                if c.is_near_zero():
                    swap_succeeded = system.swap_with_row_below(i, j)
                    if not swap_succeeded:
                        j += 1
                        continue
                system.clear_coefficients_below(i, j)
                j += 1
                break
        return system

    def swap_with_row_below(self, row, col):
        '''find row with a value of != 0 in column col and swap'''
        num_equations = len(self)

        for k in range(row + 1, num_equations):
            coefficient = MyDecimal(self[k][col])
            if not coefficient.is_near_zero():
                self.swap_rows(row, k)
                return True
        return False

    def clear_coefficients_below(self, row, col):
        '''all coefficients in column col below this row are getting cleared'''
        num_equations = len(self)
        beta = MyDecimal(self[row][col])

        for k in range(row + 1, num_equations):
            n = self[k].normal_vector
            gamma = n[col]
            alpha = -gamma / beta
            self.add_multiple_times_row_to_row(alpha, row, k)

    def compute_rref(self):
        '''reduced row echelon form'''
        tf = self.compute_triangular_form()

        num_equations = len(tf)
        pivot_indices = tf.indices_of_first_nonzero_terms_in_each_row()

        for i in range(num_equations)[::-1]:
            j = pivot_indices[i]
            if j < 0:
                continue
            tf.scale_row_to_make_coefficient_equal_one(i, j)
            tf.clear_coefficients_above(i, j)
        return tf

    def scale_row_to_make_coefficient_equal_one(self, row, col):
        '''multiply with reciprocal value to make coefficient equal to one'''
        n = self[row].normal_vector
        beta = Decimal('1.0') / n[col]
        self.multiply_coefficient_and_row(beta, row)

    def clear_coefficients_above(self, row, col):
        '''all coefficients in column col above this row are getting cleared'''
        for k in range(row)[::-1]:
            n = self[k].normal_vector
            alpha = -(n[col])
            self.add_multiple_times_row_to_row(alpha, row, k)

    def compute_solution(self):
        '''either unique-, no-, or infinitely many solutions'''
        try:
            # return self.do_gaussian_elminitation_and_extract_solution()
            return self.do_gaussian_elminitation_and_parametrize_solution()

        except Exception as e:
            if str(e) == self.NO_SOLUTIONS_MSG:
                return str(e)
            else:
                raise e

    def do_gaussian_elminitation_and_extract_solution(self):
        '''find unique solution otherwise throw exception'''
        rref = self.compute_rref()

        rref.raise_exception_if_contradictory_equation()
        rref.raise_exception_if_too_few_pivots()

        num_variables = rref.dimension
        solution_coordinates = [rref.planes[i].constant_term for i in
                                range(num_variables)]
        return Vector(solution_coordinates)

    def raise_exception_if_contradictory_equation(self):
        '''check if linear system has got no solution'''
        for p in self.planes:
            try:
                p.first_nonzero_index(p.normal_vector)

            except Exception as e:
                if str(e) == 'No nonzero elements found':
                    constant_term = MyDecimal(p.constant_term)
                    if not constant_term.is_near_zero():
                        raise Exception(self.NO_SOLUTIONS_MSG)
                else:
                    raise e

    def raise_exception_if_too_few_pivots(self):
        '''check if linear system has got infinite many solutions'''
        pivot_indices = self.indices_of_first_nonzero_terms_in_each_row()
        num_pivots = sum([1 if index >= 0 else 0 for index in pivot_indices])
        num_variables = self.dimension

        if num_pivots < num_variables:
            raise Exception(self.INF_SOLUTIONS_MSG)

    def do_gaussian_elminitation_and_parametrize_solution(self):
        '''calculate parametrize solution'''
        rref = self.compute_rref()

        rref.raise_exception_if_contradictory_equation()

        dir_vectors = rref.extract_direction_vectors_for_parametrization()
        basepoint = rref.extract_basepoint_for_parametrization()

        return Parametrization(basepoint, dir_vectors)

    def extract_direction_vectors_for_parametrization(self):
        '''calculate direction vectors for Parametrization'''
        num_variables = self.dimension
        pivot_indices = self.indices_of_first_nonzero_terms_in_each_row()
        free_variable_indices = set(range(num_variables)) - set(pivot_indices)

        direction_vectors = []

        for free_var in free_variable_indices:
            vector_coords = [0] * num_variables
            vector_coords[free_var] = 1
            for i, p in enumerate(self.planes):
                pivot_var = pivot_indices[i]
                if pivot_var < 0:
                    break
                vector_coords[pivot_var] = -p.normal_vector[free_var]
            direction_vectors.append(Vector(vector_coords))

        return direction_vectors

    def extract_basepoint_for_parametrization(self):
        '''calculate basepoint for Parametrization'''
        num_variables = self.dimension
        pivot_indices = self.indices_of_first_nonzero_terms_in_each_row()

        basepoint_coords = [0] * num_variables

        for i, p in enumerate(self.planes):
            pivot_var = pivot_indices[i]
            if pivot_var < 0:
                break
            basepoint_coords[pivot_var] = p.constant_term

        return Vector(basepoint_coords)


class Parametrization(object):

    BASEPT_AND_DIR_VECTORS_MUST_BE_IN_SAME_DIM = (
        'The basepoint and direction vectors should all live in the same  \
        dimension')

    def __init__(self, basepoint, direction_vectors):

        self.basepoint = basepoint
        self.direction_vectors = direction_vectors
        self.dimension = self.basepoint.dimension

        try:
            for v in direction_vectors:
                assert v.dimension == self.dimension

        except AssertionError:
            raise Exception(self.BASEPT_AND_DIR_VECTORS_MUST_BE_IN_SAME_DIM)

    def __str__(self):
        output = ''
        for coord in range(self.dimension):
            output += 'x_{} = {} '.format(coord + 1,
                                          round(self.basepoint[coord], 3))
            for free_var, vector in enumerate(self.direction_vectors):
                output += '+ {} t_{}'.format(round(vector[coord], 3),
                                             free_var + 1)
            output += '\n'
        return output


class MyDecimal(Decimal):
    def is_near_zero(self, eps=1e-10):
        return abs(self) < eps


if __name__ == '__main__':
    # p0 = Hyperplane(Vector(['1', '1', '1']), '1')
    # p1 = Hyperplane(Vector(['0', '1', '0']), '2')
    # p2 = Hyperplane(Vector(['1', '1', '-1']), '3')
    # p3 = Hyperplane(Vector(['1', '0', '-2']), '2')

    # s = LinearSystem([p0, p1, p2, p3])

    # print(s.indices_of_first_nonzero_terms_in_each_row())
    # print('{},{},{},{}'.format(s[0], s[1], s[2], s[3]))
    # print(len(s))
    # print(s)

    # s[0] = p1
    # print(s)

    # print(MyDecimal('1e-9').is_near_zero())
    # print(MyDecimal('1e-11').is_near_zero())

    print('###########################')
    print('Quiz: Coding Row Operations')

    p0 = Hyperplane(normal_vector=Vector(['1', '1', '1']), constant_term='1')
    p1 = Hyperplane(normal_vector=Vector(['0', '1', '0']), constant_term='2')
    p2 = Hyperplane(normal_vector=Vector(['1', '1', '-1']), constant_term='3')
    p3 = Hyperplane(normal_vector=Vector(['1', '0', '-2']), constant_term='2')

    s = LinearSystem([p0, p1, p2, p3])

    s.swap_rows(0, 1)
    if not (s[0] == p1 and s[1] == p0 and s[2] == p2 and s[3] == p3):
        print('test case 1 failed')

    s.swap_rows(1, 3)
    if not (s[0] == p1 and s[1] == p3 and s[2] == p2 and s[3] == p0):
        print('test case 2 failed')

    s.swap_rows(3, 1)
    if not (s[0] == p1 and s[1] == p0 and s[2] == p2 and s[3] == p3):
        print('test case 3 failed')

    s.multiply_coefficient_and_row(1, 0)
    if not (s[0] == p1 and s[1] == p0 and s[2] == p2 and s[3] == p3):
        print('test case 4 failed')

    s.multiply_coefficient_and_row(-1, 2)
    if not (s[0] == p1 and
            s[1] == p0 and
            s[2] == Hyperplane(normal_vector=Vector(['-1', '-1', '1']), constant_term='-3') and
            s[3] == p3):
        print('test case 5 failed')

    s.multiply_coefficient_and_row(10, 1)
    if not (s[0] == p1 and
            s[1] == Hyperplane(normal_vector=Vector(['10', '10', '10']), constant_term='10') and
            s[2] == Hyperplane(normal_vector=Vector(['-1', '-1', '1']), constant_term='-3') and
            s[3] == p3):
        print('test case 6 failed')

    s.add_multiple_times_row_to_row(0, 0, 1)
    if not (s[0] == p1 and
            s[1] == Hyperplane(normal_vector=Vector(['10', '10', '10']), constant_term='10') and
            s[2] == Hyperplane(normal_vector=Vector(['-1', '-1', '1']), constant_term='-3') and
            s[3] == p3):
        print('test case 7 failed')

    s.add_multiple_times_row_to_row(1, 0, 1)
    if not (s[0] == p1 and
            s[1] == Hyperplane(normal_vector=Vector(['10', '11', '10']), constant_term='12') and
            s[2] == Hyperplane(normal_vector=Vector(['-1', '-1', '1']), constant_term='-3') and
            s[3] == p3):
        print('test case 8 failed')

    s.add_multiple_times_row_to_row(-1, 1, 0)
    if not (s[0] == Hyperplane(normal_vector=Vector(['-10', '-10', '-10']), constant_term='-10') and
            s[1] == Hyperplane(normal_vector=Vector(['10', '11', '10']), constant_term='12') and
            s[2] == Hyperplane(normal_vector=Vector(['-1', '-1', '1']), constant_term='-3') and
            s[3] == p3):
        print('test case 9 failed')

    print('############################')
    print('Quiz: Coding Triangular Form')

    p1 = Hyperplane(normal_vector=Vector(['1', '1', '1']), constant_term='1')
    p2 = Hyperplane(normal_vector=Vector(['0', '1', '1']), constant_term='2')
    s = LinearSystem([p1, p2])
    t = s.compute_triangular_form()
    if not (t[0] == p1 and
            t[1] == p2):
        print('test case 1 failed')

    p1 = Hyperplane(normal_vector=Vector(['1', '1', '1']), constant_term='1')
    p2 = Hyperplane(normal_vector=Vector(['1', '1', '1']), constant_term='2')
    s = LinearSystem([p1, p2])
    t = s.compute_triangular_form()
    if not (t[0] == p1 and
            t[1] == Hyperplane(dimension=p1.dimension, constant_term='1')):
        print('test case 2 failed')

    p1 = Hyperplane(normal_vector=Vector(['1', '1', '1']), constant_term='1')
    p2 = Hyperplane(normal_vector=Vector(['0', '1', '0']), constant_term='2')
    p3 = Hyperplane(normal_vector=Vector(['1', '1', '-1']), constant_term='3')
    p4 = Hyperplane(normal_vector=Vector(['1', '0', '-2']), constant_term='2')
    s = LinearSystem([p1, p2, p3, p4])
    t = s.compute_triangular_form()
    if not (t[0] == p1 and
            t[1] == p2 and
            t[2] == Hyperplane(normal_vector=Vector(['0', '0', '-2']), constant_term='2') and
            t[3] == Hyperplane(dimension=p1.dimension)):
        print('test case 3 failed')

    p1 = Hyperplane(normal_vector=Vector(['0', '1', '1']), constant_term='1')
    p2 = Hyperplane(normal_vector=Vector(['1', '-1', '1']), constant_term='2')
    p3 = Hyperplane(normal_vector=Vector(['1', '2', '-5']), constant_term='3')
    s = LinearSystem([p1, p2, p3])
    t = s.compute_triangular_form()
    if not (t[0] == Hyperplane(normal_vector=Vector(['1', '-1', '1']), constant_term='2') and
            t[1] == Hyperplane(normal_vector=Vector(['0', '1', '1']), constant_term='1') and
            t[2] == Hyperplane(normal_vector=Vector(['0', '0', '-9']), constant_term='-2')):
        print('test case 4 failed')

    print('#################')
    print('Quiz: Coding RREF')

    p1 = Hyperplane(normal_vector=Vector(['1', '1', '1']), constant_term='1')
    p2 = Hyperplane(normal_vector=Vector(['0', '1', '1']), constant_term='2')
    s = LinearSystem([p1, p2])
    r = s.compute_rref()
    if not (r[0] == Hyperplane(normal_vector=Vector(['1', '0', '0']), constant_term='-1') and
            r[1] == p2):
        print('test case 1 failed')

    p1 = Hyperplane(normal_vector=Vector(['1', '1', '1']), constant_term='1')
    p2 = Hyperplane(normal_vector=Vector(['1', '1', '1']), constant_term='2')
    s = LinearSystem([p1, p2])
    r = s.compute_rref()
    if not (r[0] == p1 and
            r[1] == Hyperplane(dimension=p1.dimension, constant_term='1')):
        print('test case 2 failed')

    p1 = Hyperplane(normal_vector=Vector(['1', '1', '1']), constant_term='1')
    p2 = Hyperplane(normal_vector=Vector(['0', '1', '0']), constant_term='2')
    p3 = Hyperplane(normal_vector=Vector(['1', '1', '-1']), constant_term='3')
    p4 = Hyperplane(normal_vector=Vector(['1', '0', '-2']), constant_term='2')
    s = LinearSystem([p1, p2, p3, p4])
    r = s.compute_rref()
    if not (r[0] == Hyperplane(normal_vector=Vector(['1', '0', '0']), constant_term='0') and
            r[1] == p2 and
            r[2] == Hyperplane(normal_vector=Vector(['0', '0', '-2']), constant_term='2') and
            r[3] == Hyperplane(dimension=p1.dimension)):
        print('test case 3 failed')

    p1 = Hyperplane(normal_vector=Vector(['0', '1', '1']), constant_term='1')
    p2 = Hyperplane(normal_vector=Vector(['1', '-1', '1']), constant_term='2')
    p3 = Hyperplane(normal_vector=Vector(['1', '2', '-5']), constant_term='3')
    s = LinearSystem([p1, p2, p3])
    r = s.compute_rref()
    if not (r[0] == Hyperplane(normal_vector=Vector(['1', '0', '0']),
                               constant_term=Decimal('23') / Decimal('9')) and
            r[1] == Hyperplane(normal_vector=Vector(['0', '1', '0']),
                               constant_term=Decimal('7') / Decimal('9')) and
            r[2] == Hyperplane(normal_vector=Vector(['0', '0', '1']),
                               constant_term=Decimal('2') / Decimal('9'))):
        print('test case 4 failed')

    print('########################')
    print('Quiz: Coding GE Solution')

    p1 = Hyperplane(normal_vector=Vector([5.862, 1.178, -10.366]), constant_term=-8.15)
    p2 = Hyperplane(normal_vector=Vector([-2.931, -0.589, 5.183]), constant_term=-4.075)
    s = LinearSystem([p1, p2])
    solution = s.compute_solution()
    print(solution)

    p1 = Hyperplane(normal_vector=Vector([8.631, 5.112, -1.816]), constant_term=-5.113)
    p2 = Hyperplane(normal_vector=Vector([4.315, 11.132, -5.27]), constant_term=-6.775)
    p3 = Hyperplane(normal_vector=Vector([-2.158, 3.01, -1.727]), constant_term=-0.831)
    s = LinearSystem([p1, p2, p3])
    solution = s.compute_solution()
    print(solution)

    p1 = Hyperplane(normal_vector=Vector([5.262, 2.739, -9.878]), constant_term=-3.441)
    p2 = Hyperplane(normal_vector=Vector([5.111, 6.358, 7.638]), constant_term=-2.152)
    p3 = Hyperplane(normal_vector=Vector([2.016, -9.924, -1.367]), constant_term=-9.278)
    p4 = Hyperplane(normal_vector=Vector([2.167, -13.543, -18.883]), constant_term=-10.567)
    s = LinearSystem([p1, p2, p3, p4])
    solution = s.compute_solution()
    print(solution)

    print('############################')
    print('Quiz: Coding Parametrization')

    p1 = Hyperplane(normal_vector=Vector([0.786, 0.786, 0.588]), constant_term=-0.714)
    p2 = Hyperplane(normal_vector=Vector([-0.131, -0.131, 0.244]), constant_term=.319)
    s = LinearSystem([p1, p2])
    print('System 1 solution: \n{0}'.format(s.compute_solution()))

    p1 = Hyperplane(normal_vector=Vector([8.631, 5.112, -1.816]), constant_term=-5.113)
    p2 = Hyperplane(normal_vector=Vector([4.315, 11.132, -5.27]), constant_term=-6.775)
    p3 = Hyperplane(normal_vector=Vector([-2.158, 3.01, -1.727]), constant_term=-0.831)
    s = LinearSystem([p1, p2, p3])
    print('System 2 solution: \n{0}'.format(s.compute_solution()))

    p1 = Hyperplane(normal_vector=Vector([0.935, 1.76, -9.365]), constant_term=-9.955)
    p2 = Hyperplane(normal_vector=Vector([0.187, 0.352, -1.873]), constant_term=-1.991)
    p3 = Hyperplane(normal_vector=Vector([0.374, 0.704, -3.746]), constant_term=-3.982)
    p4 = Hyperplane(normal_vector=Vector([-0.561, -1.056, 5.619]), constant_term=5.973)
    s = LinearSystem([p1, p2, p3, p4])
    print('System 3 solution: \n{0}'.format(s.compute_solution()))
