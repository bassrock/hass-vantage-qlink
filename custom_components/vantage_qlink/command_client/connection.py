"""Wrapper for an asyncio connection to a Vantage controller."""

import asyncio

from .errors import ClientConnectionError, ClientTimeoutError


class BaseConnection:
    """Wrapper for an asyncio connection to a Vantage controller."""

    default_port: int
    buffer_limit: int = 2**16

    def __init__(
        self,
        host: str,
        port: int | None = None,
        conn_timeout: float | None = None,
    ) -> None:
        """Initialize the connection."""
        self._host = host
        self._conn_timeout = conn_timeout
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

        # Set up the port
        self._port: int
        if port is None:
            self._port = self.default_port
        else:
            self._port = port

    async def open(self) -> None:
        """Open the connection."""
        # If we're already connected, do nothing
        if self._writer is not None and not self._writer.is_closing():
            return

        # Create the connection
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(
                    self._host,
                    self._port,
                    ssl=None,
                    limit=self.buffer_limit,
                ),
                timeout=self._conn_timeout,
            )
        except asyncio.TimeoutError as exc:
            raise ClientTimeoutError(
                f"Timeout connecting to {self._host}:{self._port}"
            ) from exc
        except OSError as exc:
            raise ClientConnectionError(
                f"Failed to connect to {self._host}:{self._port}"
            ) from exc

    def close(self) -> None:
        """Close the connection."""
        if self._writer is not None and not self._writer.is_closing():
            self._writer.close()
            self._writer = None

    @property
    def host(self) -> str:
        """Return the host."""
        return self._host

    @property
    def port(self) -> int:
        """Return the port."""
        return self._port

    @property
    def closed(self) -> bool:
        """Return whether the connection is closed."""
        return self._writer is None or self._writer.is_closing()

    async def write(self, message: str) -> None:
        """Send a plaintext message.

        Args:
            message: The message to send, as a string.
        """
        # Make sure we're connected
        if self._writer is None or self._writer.is_closing():
            raise ClientConnectionError("Client not connected.")

        # Send the request
        try:
            self._writer.write(message.encode())
            await self._writer.drain()
        except OSError as err:
            raise ClientConnectionError from err

    async def readuntil(self, separator: bytes, timeout: float | None = None) -> str:
        """Read data until the separator is found or the optional timeout is reached.

        Args:
            separator: The separator to read until.
            timeout: The optional timeout in seconds.

        Returns:
            The data read, as a string.
        """
        # Make sure we're connected
        if self._reader is None or self.closed:
            raise ClientConnectionError("Client not connected.")

        # Read the response, with optional timeout
        try:
            data = await asyncio.wait_for(self._reader.readuntil(separator), timeout)
        except asyncio.TimeoutError as err:
            raise ClientTimeoutError from err
        except (OSError, asyncio.IncompleteReadError) as err:
            raise ClientConnectionError from err

        return data.decode()