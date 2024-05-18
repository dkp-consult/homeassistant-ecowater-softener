from homeassistant.helpers.translation import async_get_translations

@dataclass
class EcowaterSensorEntityDescription(SensorEntityDescription):
    """A class that describes sensor entities."""

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the ecowater sensor."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    if config_entry.options:
        config.update(config_entry.options)

    coordinator = EcowaterDataCoordinator(hass, config['username'], config['password'], config['serialnumber'], config['dateformat'])
    await coordinator.async_config_entry_first_refresh()

    # Retrieve translations for the domain
    translations = await async_get_translations(hass, hass.language, DOMAIN)

    async_add_entities(
        EcowaterSensor(coordinator, description, config['serialnumber'], translations)
        for description in SENSOR_TYPES
    )

class EcowaterSensor(
    CoordinatorEntity[EcowaterDataCoordinator],
    SensorEntity,
):
    """Implementation of an ecowater sensor."""

    def __init__(
        self,
        coordinator: EcowaterDataCoordinator,
        description: EcowaterSensorEntityDescription,
        serialnumber,
        translations,
    ) -> None:
        """Initialize the ecowater sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = "ecowater_" + serialnumber.lower() + "_" + self.entity_description.key
        self._attr_native_value = coordinator.data[self.entity_description.key]
        self._serialnumber = serialnumber

        # Apply translation
        self._attr_name = translations.get('sensor.' + self.entity_description.key, self.entity_description.name)

    @property
    def native_unit_of_measurement(self) -> StateType:
        if self.entity_description.key.startswith('water'):
            if self.coordinator.data['water_units'].lower() == 'liters':
                return UnitOfVolume.LITERS
            elif self.coordinator.data['water_units'].lower() == 'gallons':
                return UnitOfVolume.GALLONS
        elif self.entity_description.native_unit_of_measurement is not None:
            return self.entity_description.native_unit_of_measurement

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.coordinator.data[self.entity_description.key]
        self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._serialnumber)},
            name="Ecowater " + self.serialnumber,
            manufacturer="Ecowater",
        )
