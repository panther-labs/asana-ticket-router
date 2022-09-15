class GithubRepo:
    AWS_VAULT_CONFIG = "aws-vault-config"
    HOSTED_DEPLOYMENTS = "hosted-deployments"
    STAGING_DEPLOYMENTS = "staging-deployments"
    CONDUIT_DEPLOYMENTS = "conduit-deployments"
    HOSTED_AWS_MANAGEMENT = "hosted-aws-management"
    PANTHER_ENTERPRISE = "panther-enterprise"

    @classmethod
    def get_values(cls) -> list[str]:
        return [
            cls.AWS_VAULT_CONFIG, cls.HOSTED_DEPLOYMENTS, cls.STAGING_DEPLOYMENTS, cls.CONDUIT_DEPLOYMENTS,
            cls.HOSTED_AWS_MANAGEMENT, cls.PANTHER_ENTERPRISE
        ]

    @classmethod
    def _validate_repo(cls, repo_name: str) -> None:
        if repo_name not in cls.get_values():
            raise AttributeError(f"'{repo_name}' is not found in the list of supported repos.")

    @classmethod
    def get_repo_url(cls, repo_name: str) -> str:
        cls._validate_repo(repo_name)
        return f"git@github.com:panther-labs/{repo_name}"

    @classmethod
    def get_deploy_key_secret_name(cls, repo_name: str) -> str:
        cls._validate_repo(repo_name)
        return f"airplane/{repo_name}-deploy-key-base64"
