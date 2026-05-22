"""REST routers for the Class A catalog tables.

Catalogs are plain CRUD -- there is no merge, and the ``project_id`` filter is
ignored for them.
"""

from ..models.catalogs import (
    CatalogCable,
    CatalogDevice,
    CatalogEquipment,
    CatalogInstrument,
    CatalogIOModule,
    CatalogManufacturer,
)
from ..schemas import catalogs as s
from .factory import make_crud_router

routers = [
    make_crud_router(
        model=CatalogManufacturer,
        prefix="/api/catalog-manufacturers",
        label="Manufacturer",
        create_schema=s.ManufacturerCreate,
        read_schema=s.ManufacturerRead,
        update_schema=s.ManufacturerUpdate,
    ),
    make_crud_router(
        model=CatalogEquipment,
        prefix="/api/catalog-equipment",
        label="Catalog equipment",
        create_schema=s.EquipmentCreate,
        read_schema=s.EquipmentRead,
        update_schema=s.EquipmentUpdate,
    ),
    make_crud_router(
        model=CatalogCable,
        prefix="/api/catalog-cables",
        label="Catalog cable",
        create_schema=s.CableCreate,
        read_schema=s.CableRead,
        update_schema=s.CableUpdate,
    ),
    make_crud_router(
        model=CatalogInstrument,
        prefix="/api/catalog-instruments",
        label="Catalog instrument",
        create_schema=s.InstrumentCreate,
        read_schema=s.InstrumentRead,
        update_schema=s.InstrumentUpdate,
    ),
    make_crud_router(
        model=CatalogIOModule,
        prefix="/api/catalog-io-modules",
        label="Catalog I/O module",
        create_schema=s.IOModuleCreate,
        read_schema=s.IOModuleRead,
        update_schema=s.IOModuleUpdate,
    ),
    make_crud_router(
        model=CatalogDevice,
        prefix="/api/catalog-devices",
        label="Catalog device",
        create_schema=s.DeviceCreate,
        read_schema=s.DeviceRead,
        update_schema=s.DeviceUpdate,
    ),
]
