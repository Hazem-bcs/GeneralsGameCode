"""Deterministic terrain settings; no proprietary assets."""
from dataclasses import dataclass

@dataclass(frozen=True)
class TerrainConfig:
    seed: int = 6014
    base_height: int = 72
    cell_world: int = 10
    base_pad_radius: int = 475
    resource_radius: int = 175
    tech_radius: int = 135
    grade_transition: int = 48
    cliff_height: int = 105
    max_neighbour_change: int = 7
    min_build_fraction: float = 0.97
    max_flat_fraction: float = 0.65

PALETTE = ('SandMediumType6', 'DirtMediumType10', 'CliffLargeType11', 'RocksMediumType1', 'SandMediumType8', 'SandMediumType10', 'SandMediumType7Rocky')
PASS_Y = (480, 1050, 3000, 4950, 5520)
