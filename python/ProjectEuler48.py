"""
ProjectEuler48
"""
import time
modulo = 10**10

def time_cal(func):
    """
    caculate running time of function
    """
    def wrapper(*args, **kw):
        start_time = time.time()
        result = func(*args, **kw)
        print "running time of {0}: {1}s".format(func.__name__, time.time() - start_time)
        return result

    return wrapper

def module_of_pow(a, n):
    """
    caculate module pow
    """
    if n == 0:
        return 1
    if n == 1:
        return a % modulo
    tmp = module_of_pow(a, n/2)
    return (tmp*tmp*module_of_pow(a, n - n/2*2)) % modulo

def module_of_pow_using_memorize(k_prime_list):
    """
    apply memorize pattern to cache previos result
    As you see
    If a == k*b:
        a^a = (k*b)^(k*b)
            = ((k*b)^b)^k
            = (k^b * b^b)^k
    In this case, we only consider k is prime number
    because b always less than or equal to a(b <= a),
    so if we cache caculted of b^b and k^b result,
    and using it to caculate a^a
    """
    # array to store b^b
    memory_b = [1]
    # array to store k^b
    memory_k = []

    for i in range(0, max(k_prime_list) + 1):

        # init data for k^0
        memory_k.append(1)

    def wrapper(a, n):
        if n == 0:
            result = 1
            if n == a:
                memory_b.append(result)
            return result

        if n == 1:
            result = (a % modulo)
            if n == a:
                memory_b.append(result)

            return result

        k = 0

        # cache k^b
        for i in k_prime_list:
            if a %i == 0:
                memory_k[i] = (memory_k[i] * i) % modulo
                k = i

        if k != 0:
            memory_k[k] = (memory_k[k]) % modulo

            # caculate a^a
            b = a/k
            result = ((memory_b[b]*memory_k[k])**k) % modulo

            # cache a^a
            memory_b.append(result)

            return result

        tmp = wrapper(a, n/2)
        result = tmp*tmp*wrapper(a, n - n/2*2) % modulo

        if n == a:
            memory_b.append(result)

        return result
    return wrapper


def module_of_sum(a, b, modulo):
    return (a + b) % modulo

def module_of_loop(func):

    def wrapper(*args, **kw):
        total_of_module = 0
        for i in range(1, 10**6):
            total_of_module = module_of_sum(total_of_module, func(i, i), modulo)
        print "result is {0}".format(total_of_module % modulo)
        return total_of_module

    return wrapper


@time_cal
def test():
    """
    not using memorize pattern
    """
    return module_of_loop(module_of_pow)()


@time_cal
def test2():
    """
    cache only (2x)^(2x) result
    """
    return module_of_loop(module_of_pow_using_memorize([2]))()


@time_cal
def test23():
    """
    cache all (2x)^(2x), (3x)^(3x) result
    """
    return module_of_loop(module_of_pow_using_memorize([2, 3]))()

@time_cal
def test235():
    """
    cache all (2x)^(2x), (3x)^(3x), (5x)^(5x) result
    """
    return module_of_loop(module_of_pow_using_memorize([2, 3, 5]))()

@time_cal
def test2357():
    """
    cache all (2x)^(2x), (3x)^(3x), (5x)^(5x), (7x)^(7x) result
    """
    return module_of_loop(module_of_pow_using_memorize([2, 3, 5, 7]))()

@time_cal
def test23579():
    """
    cache all (2x)^(2x), (3x)^(3x), (5x)^(5x), (7x)^(7x), (9x)^(9x) result
    """
    return module_of_loop(module_of_pow_using_memorize([2, 3, 5, 7, 9]))()



if __name__ == '__main__':
    test()
    test2()
    test23()
    test235()
    test2357()
    test23579()
"""
    running time of test: 14.8649618626s
    running time of test2: 11.8096091747s
    running time of test23: 10.0104529858s
    running time of test235: 9.28809809685s
    running time of test2357: 8.17507195473s
    running time of test23579: 8.46338200569s
"""
