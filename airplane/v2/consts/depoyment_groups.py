class StagingDeploymentGroup:
    GA = "ga"
    LATEST = "latest"
    STAGING = "staging"

    @classmethod
    def get_values(cls) -> list[str]:
        return [cls.GA, cls.LATEST, cls.STAGING]


class HostedDeploymentGroup:
    A = "a"
    C = "c"
    E = "e"
    G = "g"
    J = "j"
    L = "l"
    N = "n"
    P = "p"
    Z = "z"
    CPAAS = "cpaas"
    LEGACY_SF = "legacy-sf"

    @classmethod
    def get_values(cls) -> list[str]:
        return [cls.A, cls.C, cls.E, cls.G, cls.J, cls.L, cls.N, cls.P, cls.Z, cls.CPAAS, cls.LEGACY_SF]
