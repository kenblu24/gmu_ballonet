def mean(m):  # polyfill because Micropython has no module 'statistics'
    return sum(m) / len(m)


# returns list as cumulative, starting at element s onwards
def abs_fwd_timegraph(list_, s):
    y = list_.copy()
    for i in range(s, len(y)):
        y[i] += y[i - 1]
    return y


# calculates the slope of a linear regression of past n pairs
# based on https://stackoverflow.com/a/19040841/2712730
def linreg_past(x, y, n, compute_correlation=False):
    sumx = sum(x[-n:])
    sumx2 = sum([i**2 for i in x[-n:]])
    sumy = sum(y[-n:])
    sumy2 = sum([i**2 for i in y[-n:]])
    sumxy = sum([i * j for i, j in zip(x[-n:], y[-n:])])
    denom = n * sumx2 - sumx**2

    m = (n * sumxy - sumx * sumy) / denom
    b = (sumy * sumx2 - sumx * sumxy) / denom

    if compute_correlation:
        r = (
            (sumxy - sumx * sumy / n)
            / ((sumx2 - sumx**2)**0.5 / n)
            * (sumy2 - sumy**2 / n)
        )
    else:
        r = None
    return (m, b, r)
