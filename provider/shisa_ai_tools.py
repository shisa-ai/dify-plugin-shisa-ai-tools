from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from shisa_client import get_voice_catalog


class ShisaAIToolsProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            get_voice_catalog(credentials)
        except Exception as error:
            raise ToolProviderCredentialValidationError(str(error)) from error
