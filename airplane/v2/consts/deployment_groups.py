class StagingDeploymentGroup:
    GA = "ga"
    LATEST = "latest"
    STAGING = "staging"

    @classmethod
    def get_values(cls) -> list[str]:
        return [cls.GA, cls.LATEST, cls.STAGING]


class HostedDeploymentGroup:
    A = "a"
    B = "b"
    C = "c"
    D = "d"
    E = "e"
    G = "g"
    J = "j"
    K = "k"
    L = "l"
    M = "m"
    N = "n"
    O = "o"
    P = "p"
    Q = "q"
    R = "r"
    S = "s"
    T = "t"
    U = "u"
    V = "v"
    W = "w"
    X = "x"
    Y = "y"
    Z = "z"
    CPAAS = "cpaas"

    @classmethod
    def get_values(cls) -> list[str]:
        return [
            cls.A, cls.B, cls.C, cls.D, cls.E, cls.G, cls.J, cls.K, cls.L, cls.M, cls.N, cls.O, cls.P, cls.Q, cls.R,
            cls.S, cls.T, cls.U, cls.V, cls.W, cls.X, cls.Y, cls.Z, cls.CPAAS
        ]

    @classmethod
    def is_hosted_deployment_group(cls, deployment_group):
        return deployment_group.lower() in cls.get_values()
