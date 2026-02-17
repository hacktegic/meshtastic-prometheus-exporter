import logging
import json
import base64
from meshtastic.protobuf import telemetry_pb2
from google.protobuf.json_format import MessageToDict
from meshtastic_prometheus_exporter.metrics import *
from meshtastic_prometheus_exporter.util import get_decoded_node_metadata_from_cache

logger = logging.getLogger("meshtastic_prometheus_exporter")


def on_device_metrics_telemetry(telemetry, packet_id, attributes):
    logger.info(f"MeshPacket {packet_id} is device metrics telemetry")
    device_metrics = telemetry.get("deviceMetrics", {})
    if "batteryLevel" in device_metrics:
        meshtastic_telemetry_device_battery_level_percent.set(
            device_metrics["batteryLevel"],
            attributes=attributes,
        )
    if "voltage" in device_metrics:
        meshtastic_telemetry_device_voltage_volts.set(
            device_metrics["voltage"],
            attributes=attributes,
        )
    if "channelUtilization" in device_metrics:
        meshtastic_telemetry_device_channel_utilization_percent.set(
            device_metrics["channelUtilization"],
            attributes=attributes,
        )
    if "airUtilTx" in device_metrics:
        meshtastic_telemetry_device_air_util_tx_percent.set(
            device_metrics["airUtilTx"],
            attributes=attributes,
        )


def on_meshtastic_telemetry_app(packet, source_long_name, source_short_name):
    # Decode the protobuf payload if it exists
    # Newer versions of meshtastic library don't automatically decode all packet types
    if "telemetry" in packet["decoded"]:
        # Already decoded (legacy behavior)
        telemetry = packet["decoded"]["telemetry"]
    elif "payload" in packet["decoded"]:
        # Need to decode the base64 payload manually
        try:
            payload_bytes = base64.b64decode(packet["decoded"]["payload"])
            telemetry_msg = telemetry_pb2.Telemetry()
            telemetry_msg.ParseFromString(payload_bytes)
            telemetry = MessageToDict(telemetry_msg)
        except Exception as e:
            logger.error(
                f"Failed to decode TELEMETRY_APP payload for packet {packet.get('id', 'unknown')}: {e}"
            )
            return
    else:
        logger.error(
            f"TELEMETRY_APP packet {packet.get('id', 'unknown')} has neither 'telemetry' nor 'payload' field"
        )
        return
    logger.debug(
        f"Received MeshPacket {packet['id']} with Telemetry `{json.dumps(telemetry, default=repr)}`"
    )
    source = packet["decoded"].get("source", packet["from"])
    telemetry_attributes = {
        "source": source or "unknown",
        "source_long_name": source_long_name or "unknown",
        "source_short_name": source_short_name or "unknown",
    }
    if "deviceMetrics" in telemetry:
        on_device_metrics_telemetry(telemetry, packet["id"], telemetry_attributes)
        return

    if "environmentMetrics" in telemetry:
        logger.info(f"MeshPacket {packet['id']} is environment metrics telemetry")
        if "temperature" in telemetry["environmentMetrics"]:
            meshtastic_telemetry_env_temperature_celsius.set(
                telemetry["environmentMetrics"]["temperature"],
                attributes=telemetry_attributes,
            )
        if "relativeHumidity" in telemetry["environmentMetrics"]:
            meshtastic_telemetry_env_relative_humidity_percent.set(
                telemetry["environmentMetrics"]["relativeHumidity"],
                attributes=telemetry_attributes,
            )
        if "barometricPressure" in telemetry["environmentMetrics"]:
            meshtastic_telemetry_env_barometric_pressure_pascal.set(
                telemetry["environmentMetrics"]["barometricPressure"] * 10**2,
                attributes=telemetry_attributes,
            )
        if "gasResistance" in telemetry["environmentMetrics"]:
            meshtastic_telemetry_env_gas_resistance_ohms.set(
                telemetry["environmentMetrics"]["gasResistance"] / 10**6,
                attributes=telemetry_attributes,
            )
        if "voltage" in telemetry["environmentMetrics"]:
            meshtastic_telemetry_env_voltage_volts.set(
                telemetry["environmentMetrics"]["voltage"],
                attributes=telemetry_attributes,
            )
        if "current" in telemetry["environmentMetrics"]:
            meshtastic_telemetry_env_current_amperes.set(
                telemetry["environmentMetrics"]["current"] * 10**-3,
                attributes=telemetry_attributes,
            )
    if "airQualityMetrics" in telemetry:
        logger.info(f"MeshPacket {packet['id']} is air quality metrics telemetry")
        meshtastic_telemetry_air_quality_pm10_standard.set(
            telemetry["airQualityMetrics"]["pm10_standard"],
            attributes=telemetry_attributes,
        )
        meshtastic_telemetry_air_quality_pm25_standard.set(
            telemetry["airQualityMetrics"]["pm25_standard"],
            attributes=telemetry_attributes,
        )
        meshtastic_telemetry_air_quality_pm100_standard.set(
            telemetry["airQualityMetrics"]["pm100_standard"],
            attributes=telemetry_attributes,
        )
        meshtastic_telemetry_air_quality_pm10_environmental.set(
            telemetry["airQualityMetrics"]["pm10_environmental"],
            attributes=telemetry_attributes,
        )
        meshtastic_telemetry_air_quality_pm25_environmental.set(
            telemetry["airQualityMetrics"]["pm25_environmental"],
            attributes=telemetry_attributes,
        )
        meshtastic_telemetry_air_quality_pm100_environmental.set(
            telemetry["airQualityMetrics"]["pm100_environmental"],
            attributes=telemetry_attributes,
        )
        meshtastic_telemetry_air_quality_particles_03um.set(
            telemetry["airQualityMetrics"]["particles_03um"],
            attributes=telemetry_attributes,
        )
        meshtastic_telemetry_air_quality_particles_05um.set(
            telemetry["airQualityMetrics"]["particles_05um"],
            attributes=telemetry_attributes,
        )
        meshtastic_telemetry_air_quality_particles_10um.set(
            telemetry["airQualityMetrics"]["particles_10um"],
            attributes=telemetry_attributes,
        )
        meshtastic_telemetry_air_quality_particles_25um.set(
            telemetry["airQualityMetrics"]["particles_25um"],
            attributes=telemetry_attributes,
        )
        meshtastic_telemetry_air_quality_particles_50um.set(
            telemetry["airQualityMetrics"]["particles_50um"],
            attributes=telemetry_attributes,
        )
        meshtastic_telemetry_air_quality_particles_100um.set(
            telemetry["airQualityMetrics"]["particles_100um"],
            attributes=telemetry_attributes,
        )
    if "powerMetrics" in telemetry:
        logger.info(f"MeshPacket {packet['id']} is power metrics telemetry")
        meshtastic_telemetry_power_ch1_voltage_volts.set(
            telemetry["powerMetrics"]["ch1_voltage"],
            attributes=telemetry_attributes,
        )
        meshtastic_telemetry_power_ch1_current_amperes.set(
            telemetry["powerMetrics"]["ch1_current"] * 10**-3,
            attributes=telemetry_attributes,
        )
        meshtastic_telemetry_power_ch2_voltage_volts.set(
            telemetry["powerMetrics"]["ch2_voltage"],
            attributes=telemetry_attributes,
        )
        meshtastic_telemetry_power_ch2_current_amperes.set(
            telemetry["powerMetrics"]["ch2_current"] * 10**-3,
            attributes=telemetry_attributes,
        )
        meshtastic_telemetry_power_ch3_voltage_volts.set(
            telemetry["powerMetrics"]["ch3_voltage"],
            attributes=telemetry_attributes,
        )
        meshtastic_telemetry_power_ch3_current_amperes.set(
            telemetry["powerMetrics"]["ch3_current"] * 10**-3,
            attributes=telemetry_attributes,
        )
