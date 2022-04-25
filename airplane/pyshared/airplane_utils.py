import os


class AirplaneTask:

    @staticmethod
    def is_test_run():
        return is_test_run(ap_params={})

    def main(self):
        raise NotImplementedError


def is_test_run(ap_params):
    test_run = ap_params.get("airplane_test_run")

    if test_run is None:
        env_slug = os.environ.get("AIRPLANE_ENV_SLUG")
        if env_slug is not None:
            is_staging_or_prod = ("staging" in env_slug) or ("prod" in env_slug)
            test_run = not is_staging_or_prod
        else:
            test_run = True

    if test_run:
        print("*** THIS IS A TEST RUN ***")
    return test_run


def _get_task(params):
    subclasses = AirplaneTask.__subclasses__()
    num_subs = len(subclasses)
    if num_subs != 1:
        raise RuntimeError(f"Exactly one class must inherit from AirplaneTask in your task. {num_subs} found")

    subclass = subclasses[0]
    while subclass.__subclasses__():
        subclass = subclass.__subclasses__()[0]
    return subclass(params)


def main(params):
    task = _get_task(params)
    task.main()
