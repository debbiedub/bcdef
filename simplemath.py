import random
import math

class Chi2:
    def __init__(self, seed):
        self.rand = random.Random(seed)

    def _normal(self):
        return self.rand.normalvariate(0.0, 1.0)

    def chi2(self, degree_of_freedom):
        sum = 0.0
        for _ in range(degree_of_freedom):
            sum += self._normal()**2.0
        return sum

    def visualize_chi2(self, degree_of_freedom, n):
        d = dict()
        max = 0
        for i in range(n):
            val = self.chi2(degree_of_freedom)
            fl = int(val)
            if fl not in d:
                d[fl] = 0
            d[fl] = d[fl] + 1
            if d[fl] > max:
                max = d[fl]
        for i in range(len(d)):
            x = 0.0 + i
            if x not in d:
                continue
            print x, "".join(["*" for x in range(80 * d[x] / max)])

    def when(self, degree_of_freedom):
        return (datetime.datetime.now() +
                datetime.timedelta(hours=c.chi2(degree_of_freedom)))
