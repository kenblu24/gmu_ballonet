class thermistor:
    def __init__(self, file):
        self.file = file
        self.table_tc = []
        self.table_r = []
        try:
            with open(self.file, "r") as f:
                while True:
                    line = f.readline()
                    if line:
                        split = line.rstrip().split("\t")
                        self.table_tc.append(float(split[0]))
                        self.table_r.append(float(split[1]))
                    else:
                        break
        except IOError:
            pass
        self.table = zip(self.table_r, self.table_tc)

    def linear_approximation(self, i1, i2, r):
        x1 = self.table_r[i1]
        x2 = self.table_r[i2]
        y1 = self.table_tc[i1]
        y2 = self.table_tc[i2]
        m = (y2 - y1) / (x2 - x1)
        return m * (r - x1) + y1

    def get_temperature(self, r_ntc):
        nearest_r = min(self.table_r, key=lambda x: abs(x - r_ntc))
        i = self.table_r.index(nearest_r)
        if i <= 0:
            return self.linear_approximation(i, i + 1, r_ntc)
        elif i >= len(self.table_r):
            return self.linear_approximation(i, i - 1, r_ntc)
        else:
            if self.table_r[i] > self.table_r[i + 1]:
                if r_ntc <= self.table_r[i] and r_ntc >= self.table_r[i + 1]:
                    return self.linear_approximation(i, i + 1, r_ntc)
                if r_ntc <= self.table_r[i - 1] and r_ntc > self.table_r[i]:
                    return self.linear_approximation(i, i - 1, r_ntc)
            else:
                raise Exception("Table not sorted in descending order")
