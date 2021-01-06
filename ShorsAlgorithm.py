import math
import time

def findFactors(x):
    if x < 0:
        return -1, findFactors(-x)
    elif x == 0 or x == 1:
        return int(x)
    elif x % 2 == 0:
        return 2, x/2
    else:
        period = 0
        baseVal = 1
        foundPrd = False
        start = time.time()
        while not foundPrd:
            periodAdd = math.ceil(math.log(x/baseVal, 2))
            period += periodAdd
            baseVal = (baseVal * 2**periodAdd) % x
            if baseVal == 1:
                foundPrd = True
        end = time.time()
        print(end - start)
        print('  period =', period)
        if period > 1024:
            print('  Too Large Period!')
            return
        high = int(2**(period/2)) + 1
        low = int(2**(period/2)) - 1
        if high % x == 0:
            if math.floor(math.sqrt(x)) == math.sqrt(x):
                return int(math.sqrt(x)), int(math.sqrt(x))
            else:
                return int(x)
        else:
            print(high)
            print(low)
            p = math.gcd(int(high), int(x))
            q = math.gcd(int(low), int(x))
            return float(p), float(q)

if __name__ == '__main__':
    print(findFactors(123456789))
