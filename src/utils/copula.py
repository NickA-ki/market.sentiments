"""
PURPOSE:  Functions to generate correlated random varialbles using copulas

CREATED:  2022/12/29
"""

import scipy.stats as sc
import statsmodels.stats.correlation_tools as ct
import numpy as np
import pandas as pd


class Copula:
    def __init__(self) -> None:
        pass

    def copulaGaussian(
        self, nSims: int, corrM: int, dataframe: bool = False
    ) -> pd.DataFrame:
        nVar = np.size(corrM, 0)
        # Find nearest positive semi definite correlation matrix
        psd = ct.corr_nearest(corrM)
        # Calculate Cholesky Decomposition
        A = np.linalg.cholesky(psd)
        # Simulate nVar i.i.d. from N(0,1)
        l = []
        for i in range(nVar):
            l.append(np.random.normal(0, 1, nSims).tolist())
        z = np.array(l)
        # set x = Az
        x = np.matmul(A, z)
        # set u equal to cdf at x from N(0,1)
        u = sc.norm.cdf(x)
        u = np.transpose(u)

        # optional: return dataframe instead of array
        if dataframe:
            cols = []
            for i in range(nVar):
                cols.append("u" + str(i))
            u = pd.DataFrame(u, columns=cols)

        return u

    def copulaStudentT(
        self, nSims: int, corrM: int, degFree: int = 3, dataframe: bool = False
    ) -> pd.DataFrame:
        nVar = np.size(corrM, 0)
        # Find nearest positive semi definite correlation matrix
        psd = ct.corr_nearest(corrM)
        # Calculate Cholesky Decomposition
        A = np.linalg.cholesky(psd)
        # Simulate nVar i.i.d. from N(0,1)
        l = []
        for i in range(nVar):
            l.append(np.random.normal(0, 1, nSims).tolist())
        z = np.array(l)
        # set y = Az
        y = np.matmul(A, z)
        # Simulate s from chiSq
        s = np.random.chisquare(degFree, nSims)
        # set x = sqrt(df/s) * y
        x = np.sqrt(degFree / s) * y
        # set u equal to cdf at x from T dist
        u = sc.t.cdf(x, degFree)
        u = np.transpose(u)

        # optional: return dataframe instead of array
        if dataframe:
            cols = []
            for i in range(nVar):
                cols.append("u" + str(i))
            u = pd.DataFrame(u, columns=cols)

        return u

    def copulaInvClayton(
        self, nSims: int, nVar: int, alpha: int, dataframe: pd.DataFrame = False
    ) -> pd.DataFrame:
        # generate random values for all variables
        v = np.random.rand(nVar, nSims)

        # apply clayton recursive formula
        uAlphaSum = np.power(v[0], -alpha)
        u = []
        u.append(v[0].tolist())

        for i in range(1, nVar):
            a = uAlphaSum - (i + 1) + 2
            b = np.power(v[i], alpha / (alpha * (1 - (i + 1)) - 1)) - 1
            c = np.multiply(a, b) + 1
            ui = np.power(c, -1 / alpha)
            u.append(ui.tolist())
            uAlphaSum = np.sum((uAlphaSum, np.power(ui, -alpha)), axis=0)
        u = np.array(u)

        # inverse result to concentrate correlation in tails
        u = (u - 1) * -1
        u = np.transpose(u)

        # optional: return dataframe instead of array
        if dataframe:
            cols = []
            for i in range(nVar):
                cols.append("u" + str(i))
            u = pd.DataFrame(u, columns=cols)

        return u


# if __name__ == "__main__":
#     R = np.array([[1, 0.8, 0.8], [0.8, 1, 0.8], [0.8, 0.8, 1]])
#     # print(ct.corr_nearest(R))

#     s = 10
#     # test = copulaGaussian(s, R, True)

#     df = 3
#     # test = copulaStudentT(s, R, df, True)

#     n = 4
#     al = 3
#     test = copulaInvClayton(s, n, al, True)

#     # print(test)
