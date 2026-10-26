from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.lam import View
from app.lam.catalog import PointInfo


class MeasurementOut(BaseModel):
    table: str
    item: str


class PointOut(BaseModel):
    id: str
    name: str
    side: str | None = None
    region: str
    definition: str
    location: str = Field(description="Cómo localizar o palpar el punto")
    views: list[View]
    figure: Literal["anterior", "posterior", "lateral"]
    position: tuple[float, float] = Field(description="(x, y) en la silueta de 100 x 200")
    measurements: list[MeasurementOut]
    diagnostics: list[str]

    @classmethod
    def from_domain(cls, p: PointInfo) -> "PointOut":
        return cls(
            id=p.id, name=p.name, side=p.side, region=p.region, definition=p.definition, location=p.location,
            views=list(p.views), figure=p.figure, position=p.position,
            measurements=[MeasurementOut(table=m.table, item=m.item) for m in p.measurements],
            diagnostics=list(p.diagnostics),
        )
