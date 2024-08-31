import asyncio
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
import logging
from types import TracebackType
from typing import Self

from .connection import BaseConnection
from .errors import CommandError
from .utils import encode_params, tokenize_response


class CommandConnection(BaseConnection):
    """Connection to a Vantage Host Command service."""

    default_port = 10001


@dataclass
class CommandResponse:
    """Wrapper for command responses."""

    command: str
    args: Sequence[str]
    data: Sequence[str]


class CommandClient:
    """Client to send commands to the Vantage Host Command service."""

    def __init__(
        self,
        host: str,
        port: int | None = None,
        conn_timeout: float = 30,
        read_timeout: float = 60,
    ) -> None:
        """Initialize the client."""
        self._connection = CommandConnection(host, port, conn_timeout)
        self._read_timeout = read_timeout
        self._connection_lock = asyncio.Lock()
        self._command_lock = asyncio.Lock()
        self._logger = logging.getLogger(__name__)

    async def __aenter__(self) -> Self:
        """Return context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Exit context manager."""
        self.close()
        if exc_val:
            raise exc_val

    def close(self) -> None:
        """Close the connection to the Host Command service."""
        self._connection.close()

    async def command(
        self,
        command: str,
        *params: str | int | float | Decimal,
        force_quotes: bool = False,
        connection: CommandConnection | None = None,
    ) -> CommandResponse:
        """Send a command to the Host Command service and wait for a response.

        Args:
            command: The command to send, should be a single word string.
            params: The parameters to send with the command.
            force_quotes: Whether to force string params to be wrapped in double quotes.
            connection: The connection to use, if not the default.

        Returns:
            A CommandResponse instance.
        """
        # Build the request
        request = command
        if params:
            request += f" {encode_params(*params, force_quotes=force_quotes)}"
        request += f"\r"

        # Send the request and parse the response
        *data, return_line = await self.raw_request(request, connection=connection)
        command, *args = tokenize_response(return_line)
        return CommandResponse(command[2:], args, data)

    async def raw_request(
        self, request: str, connection: CommandConnection | None = None
    ) -> Sequence[str]:
        """Send a raw command to the Host Command service and return all response lines.

        Handles authentication if required, and raises an exception if the response line
        contains R:ERROR.

        Args:
            request: The request to send.
            connection: The connection to use, if not the default.

        Returns:
            The response lines received from the server.
        """
        conn = connection or await self.get_connection()

        # Send the command
        async with self._command_lock:
            self._logger.debug("Sending command: %s", request)
            await conn.write(f"{request}\n")

            # Read all lines of the response
            response_lines = []
            while True:
                response_line = await conn.readuntil(b"\r", self._read_timeout)
                response_line = response_line.rstrip()
                self._logger.debug("Recieved response: %s", response_line)

                # Handle error codes
                if response_line == "257":
                    raise self._parse_command_error(response_line)

                # Ignore potentially interleaved "event" messages
                if any(response_line.startswith(x) for x in ("S:", "L:", "LE", "LC")):
                    self._logger.debug("Ignoring event message: %s", response_line)
                    continue

                # The response is the direct response from the system, since we are not subscribing to data atm
                response_lines.append(response_line)
                break

        self._logger.debug("Received response: %s", "\n".join(response_lines))

        return response_lines

    async def get_connection(self) -> CommandConnection:
        """Get a connection to the Host Command service."""
        async with self._connection_lock:
            if self._connection.closed:
                # Open a new connection
                await self._connection.open()

                self._logger.info(
                    "Connected to command client at %s:%d",
                    self._connection.host,
                    self._connection.port,
                )

            return self._connection

    def _parse_command_error(self, message: str) -> CommandError:
        error_code = int(message)

        return CommandError(f"(Error code {error_code})")
