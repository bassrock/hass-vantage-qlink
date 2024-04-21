"""Interface for querying and controlling loads."""

from .base import Interface


class LoadInterface(Interface):
    """Interface for querying and controlling loads."""

    method_signatures = {
        "VGA": int,
        "VLO": int,
    }

    async def set_level(self, contractor_number: int, level: int) -> None:
        """Set the level of a load. Passthrough to ramp

        Args:
            contractor_number: The Vantage ID of the load.
            level: The level to set the load to (0-100).
        """

        await self.ramp(contractor_number=contractor_number, level=level, time=0)

    async def get_level(self, contractor_number: int) -> int:
        """Get the level of a load, using cached value if available.

        Args:
            contractor_number: The Vantage ID of the load.

        Returns:
            The level of the load, as a percentage (0-100).
        """
        # VGL <contractor_number>
        # -> <level>
        return await self.invoke(contractor_number, "VGL", as_type=int)

    async def ramp(
        self,
        contractor_number: int,
        level: int = 0,
        time: int = 0,
    ) -> None:
        """Ramp a load to a level over a number of seconds.

        Args:
            contractor_number: The Vantage Contractor Number of the load.
            level: The level to ramp the load to (0-100).
            time: The number of seconds to ramp the load over.
        """
        # Clamp level to 0-100
        level = max(min(level, 100), 0)

        # VLO <contractor_number> <level> <fade>
        # -> <level>
        await self.invoke(contractor_number, "VLO", level, time)

    # Additional convenience methods, not part of the Vantage API
    async def turn_on(
        self,
        contractor_number: int,
        transition: float | None = None,
        level: float | None = None,
    ) -> None:
        """Turn on a load with an optional transition time.

        Args:
            contractor_number: The Vantage ID of the load.
            transition: The time in seconds to transition to the new level, defaults to immediate.
            level: The level to set the load to (0-100), defaults to 100.
        """
        if level is None:
            level = 100

        if transition is None:
            return await self.set_level(contractor_number, level)

        await self.ramp(contractor_number, time=transition, level=level)

    async def turn_off(
        self, contractor_number: int, transition: float | None = None
    ) -> None:
        """Turn off a load with an optional transition time.

        Args:
            contractor_number: The Vantage ID of the load.
            transition: The time in seconds to ramp the load down, defaults to immediate.
        """
        if transition is None:
            return await self.set_level(contractor_number, 0)

        await self.ramp(contractor_number, time=transition, level=0)
