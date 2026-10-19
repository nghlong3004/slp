"""The adapter boundary: catalog(), prepare(), launch_env(), launch_args()."""

from . import codex, prompt_argument
from ..common import SlpError


def get_adapter(provider):
    adapters = {"codex": codex, "prompt-argument": prompt_argument}
    try:
        return adapters[provider["adapter"]]
    except KeyError:
        raise SlpError(f"Unknown adapter: {provider.get('adapter')}") from None
