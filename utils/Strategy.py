class Strategy:
    """
    OG generator can use different strategy to generate factors
    """
    def __init__(self, total_steps:int, start_factor:float, end_factor:float) -> None:
        self.steps = total_steps
        self.start_factor = start_factor
        self.end_factor = end_factor

        self.factors = {
            'linear': self.linear(),
            'exp':self.exp(),
            'swish':self.swish(total_steps//2),
            'random':self.random(),
        }
    def __call__(self, strategy:str, step:int):
        """
        0 <= step < total_steps
        """
        f = self.factors.get(strategy,None)
        if f and step >= 0 and step < self.steps:
            return f[step]
        return 1.0

    def linear(self):
        """
        Generate a list of [1+steps] lengths, with each element representing the factor of that step
        """
        return [self.start_factor + i/(self.steps-1) * (self.end_factor-self.start_factor) for i in range(self.steps)]

    def exp(self, growth=0.1):
        return [min(self.end_factor, self.start_factor * ((1 + growth) ** i)) for i in range(self.steps)]

    def swish(self, shrinkage_steps, shrinkage = 0.02):
        """
        In shrinkage steps, itlinearly decreases from the start factor to the bottom. 
        The remaining steps increase linearly from the bottom to the end.
        """
        bottom = self.start_factor - shrinkage * shrinkage_steps
        assert bottom > 0
        increment = (self.end_factor - bottom)/(self.steps - shrinkage_steps - 1)
        # print(shrinkage_steps, bottom, increment)
        return [self.start_factor - i * shrinkage for i in range(shrinkage_steps)] + [bottom + i * increment for i in range(self.steps  - shrinkage_steps)]

    def random(self):
        import random
        random.seed(42)
        list = [random.uniform(self.start_factor, 1.0) for _ in range(self.steps-1)]
        list.append(self.start_factor)
        list.append(1.0)
        random.shuffle(list)
        return list

if __name__ == '__main__':
    a = Strategy(9,0.5,1)
    print(a.linear())
    print(a.swish(9//2))
    print(a.exp())
    print(a.random())
    print(a('swish',8))