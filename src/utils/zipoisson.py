import scipy.stats as stats
import numpy as np
from src.utils.utils import utils


class ZIPoisson(stats.rv_discrete):
    def __init__(self, p, mu, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.p = p
        self.mu = mu
        self.bernoulli = stats.bernoulli(self.p)
        self.poisson = stats.poisson(self.mu)

    def zi_pmf(self, x):
        if x == 0:
            pmf = self.p + (1 - self.p) * np.exp(-self.mu)
        else:
            pmf = (1 - self.p) * (
                (self.mu**x * np.exp(-self.mu)) / np.math.factorial(int(x))
            )
        return pmf

    def _pmf(self, x):
        return utils.vectorize(self.zi_pmf, x)
