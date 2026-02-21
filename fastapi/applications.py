"""
FastAPI applications.
"""
from typing import Any, AsyncGenerator, Dict, List, Optional, Sequence, Tuple, Union

from fastapi import routing
from fastapi.concurrency import run_in_threadpool
from fastapi.encoders import DictIntStrAny, SetIntStr
from fastapi.exceptions import RequestValidationError
from fastapi.logger import logger
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.openapi.utils import get_openapi
from fastapi.params import Depends
from fastapi.types import ASGIApp, ASGIInstance, Scope
from starlette.applications import Starlette
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.exceptions import ExceptionMiddleware
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.routing import BaseRoute, Match
from starlette.types import Receive, Scope as StarletteScope, Send


class FastAPI(Starlette):
    """
    FastAPI application class.

    This class inherits from Starlette and adds functionality for building APIs.
    """

    def __init__(
        self,
        debug: bool = False,
        routes: Optional[List[BaseRoute]] = None,
        title: str = "FastAPI",
        description: str = "",
        version: str = "0.1.0",
        openapi_url: Optional[str] = "/openapi.json",
        openapi_tags: Optional[List[Dict[str, Any]]] = None,
        servers: Optional[List[Dict[str, Union[str, Any]]]] = None,
        default_response_class: type = JSONResponse,
        docs_url: Optional[str] = "/docs",
        redoc_url: Optional[str] = "/redoc",
        swagger_ui_oauth2_redirect_url: Optional[str] = "/docs/oauth2-redirect",
        swagger_ui_init_oauth: Optional[Dict[str, Any]] = None,
        middleware: Optional[Sequence[Middleware]] = None,
        exception_handlers: Optional[
            Dict[Union[int, type[Exception]], Any]
        ] = None,
        on_startup: Optional[Sequence[Callable]] = None,
        on_shutdown: Optional[Sequence[Callable]] = None,
        **extra: Any,
    ) -> None:
        """
        Initialize the FastAPI application.

        Args:
            debug: Enable debug mode.
            routes: List of routes.
            title: API title.
            description: API description.
            version: API version.
            openapi_url: URL for OpenAPI schema.
            openapi_tags: Tags for OpenAPI documentation.
            servers: Server configuration.
            default_response_class: Default response class.
            docs_url: URL for Swagger UI documentation.
            redoc_url: URL for ReDoc documentation.
            swagger_ui_oauth2_redirect_url: URL for OAuth2 redirect.
            swagger_ui_init_oauth: OAuth2 configuration.
            middleware: Middleware to apply.
            exception_handlers: Exception handlers.
            on_startup: Startup event handlers.
            on_shutdown: Shutdown event handlers.
            **extra: Additional keyword arguments.
        """
        self._debug = debug
        self.router: routing.APIRouter = routing.APIRouter(
            routes=routes,
            dependency_overrides_provider=self,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
        )
        self.title = title
        self.description = description
        self.version = version
        self.openapi_url = openapi_url
        self.openapi_tags = openapi_tags
        self.servers = servers
        self.default_response_class = default_response_class
        self.docs_url = docs_url
        self.redoc_url = redoc_url
        self.swagger_ui_oauth2_redirect_url = swagger_ui_oauth2_redirect_url
        self.swagger_ui_init_oauth = swagger_ui_init_oauth
        self.middleware = middleware
        self.exception_handlers = exception_handlers
        self.extra = extra

        super().__init__(
            debug=debug,
            routes=self.router.routes,
            exception_handlers=exception_handlers,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            middleware=middleware,
        )

        if self.openapi_url:
            self.add_route(self.openapi_url, self.openapi, include_in_schema=False)
        if self.docs_url:
            self.add_route(self.docs_url, self.swagger_ui_html, include_in_schema=False)
            self.add_route(
                self.swagger_ui_oauth2_redirect_url,
                self.swagger_ui_oauth2_redirect_html,
                include_in_schema=False,
            )
        if self.redoc_url:
            self.add_route(self.redoc_url, self.redoc_html, include_in_schema=False)

    def openapi(self) -> Dict[str, Any]:
        """
        Generate the OpenAPI schema.

        Returns:
            OpenAPI schema as a dictionary.
        """
        if not self.openapi_schema:
            self.openapi_schema = get_openapi(
                title=self.title,
                version=self.version,
                description=self.description,
                routes=self.routes,
                tags=self.openapi_tags,
                servers=self.servers,
            )
        return self.openapi_schema

    def swagger_ui_html(self) -> HTMLResponse:
        """
        Generate the Swagger UI HTML.

        Returns:
            HTMLResponse containing the Swagger UI.
        """
        return get_swagger_ui_html(
            openapi_url=self.openapi_url,
            title=self.title + " - Swagger UI",
            oauth2_redirect_url=self.swagger_ui_oauth2_redirect_url,
            init_oauth=self.swagger_ui_init_oauth,
        )

    def swagger_ui_oauth2_redirect_html(self) -> HTMLResponse:
        """
        Generate the OAuth2 redirect HTML for Swagger UI.

        Returns:
            HTMLResponse for OAuth2 redirect.
        """
        return get_swagger_ui_oauth2_redirect_html()

    def redoc_html(self) -> HTMLResponse:
        """
        Generate the ReDoc HTML.

        Returns:
            HTMLResponse containing the ReDoc documentation.
        """
        return get_redoc_html(
            openapi_url=self.openapi_url, title=self.title + " - ReDoc"
        )
