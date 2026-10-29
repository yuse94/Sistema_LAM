from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from pydantic import AfterValidator


def as_utc(d: datetime) -> datetime:
    """SQLite devuelve fechas sin zona horaria; se guardan en UTC."""
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


# Fecha que siempre se serializa con zona horaria, para que el navegador la muestre en hora local.
UTCDatetime = Annotated[datetime, AfterValidator(as_utc)]
