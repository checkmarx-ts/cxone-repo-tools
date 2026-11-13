import os
from cxone_repo_tools.exceptions import AbortedConversionException

PAT_ENV = "CX_PAT"
"""The environment variable the SCM PAT is read from when it is in the
environment."""


def get_scm_token(token: str | None, token_in_env: bool) -> str | None:
    """Retrieves the SCM PAT from a supplied value or from the environment
    variable named by `PAT_ENV`.

    A supplied `token` takes precedence: it is returned even when
    `token_in_env` is True, so the caller does not need to prevent both from
    being given.  The environment variable is read only when `token` is None
    and `token_in_env` is True.

    :param token: The SCM PAT supplied on the command line, or None if it was
                  not supplied.
    :type token: str | None

    :param token_in_env: True to read the SCM PAT from the environment
                         variable named by `PAT_ENV`.
    :type token_in_env: bool

    :return: `token` if it is not None, otherwise the value of the
             environment variable if `token_in_env` is True, otherwise None.
    :rtype: str | None

    :raises AbortedConversionException: `token` is empty, or `token` is None,
                                        `token_in_env` is True, and the
                                        environment variable is missing or
                                        empty.
    """
    if token is not None:
        if len(token) == 0:
            raise AbortedConversionException.empty_secret("SCM PAT")
        return token

    if token_in_env:
        env_token = os.environ.get(PAT_ENV)
        if env_token is None or len(env_token) == 0:
            raise AbortedConversionException.missing_secret_env(PAT_ENV, "SCM PAT")
        return env_token

    return None
