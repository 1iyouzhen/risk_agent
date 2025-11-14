import json
import math


class TrainableForecaster:
    def __init__(self, features):
        self.features = features
        self.w = [0.0 for _ in features]
        self.b = 0.0

    def sigmoid(self, z):
        if z < -50:
            return 0.0
        if z > 50:
            return 1.0
        return 1.0/(1.0+math.exp(-z))

    def fit(self, X, y, lr=1e-4, epochs=50):
        n = len(X)
        for _ in range(epochs):
            dw = [0.0 for _ in self.w]
            db = 0.0
            for i in range(n):
                z = sum(self.w[j]*X[i][j] for j in range(len(self.w))) + self.b
                p = self.sigmoid(z)
                e = p - y[i]
                for j in range(len(self.w)):
                    dw[j] += e * X[i][j]
                db += e
            for j in range(len(self.w)):
                self.w[j] -= lr * (dw[j]/max(1,n))
            self.b -= lr * (db/max(1,n))

    def score(self, x):
        z = sum(self.w[i]*float(x.get(self.features[i], 0.0)) for i in range(len(self.w))) + self.b
        return self.sigmoid(z)

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"features": self.features, "w": self.w, "b": self.b}, f)

    @staticmethod
    def load(path):
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        m = TrainableForecaster(obj["features"])
        m.w = obj["w"]
        m.b = obj["b"]
        return m

