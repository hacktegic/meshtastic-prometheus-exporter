import logging
import json
import base64
from meshtastic.protobuf import mesh_pb2
from google.protobuf.json_format import MessageToDict
from meshtastic_prometheus_exporter.util import get_decoded_node_metadata_from_cache
from meshtastic_prometheus_exporter.metrics import *

logger = logging.getLogger("meshtastic_prometheus_exporter")


def on_meshtastic_neighborinfo_app(cache, packet, source_long_name, source_short_name):
    # Decode the protobuf payload if it exists
    # Newer versions of meshtastic library don't automatically decode all packet types
    if "neighborinfo" in packet["decoded"]:
        # Already decoded (legacy behavior)
        neighbor_info = packet["decoded"]["neighborinfo"]
    elif "payload" in packet["decoded"]:
        # Need to decode the base64 payload manually
        try:
            payload_bytes = base64.b64decode(packet["decoded"]["payload"])
            neighbor_msg = mesh_pb2.NeighborInfo()
            neighbor_msg.ParseFromString(payload_bytes)
            neighbor_info = MessageToDict(neighbor_msg)
        except Exception as e:
            logger.error(
                f"Failed to decode NEIGHBORINFO_APP payload for packet {packet.get('id', 'unknown')}: {e}"
            )
            return
    else:
        logger.error(
            f"NEIGHBORINFO_APP packet {packet.get('id', 'unknown')} has neither 'neighborinfo' nor 'payload' field"
        )
        return
    logger.debug(
        f"Received MeshPacket {packet['id']} with NeighborInfo `{json.dumps(neighbor_info, default=repr)}`"
    )

    source = neighbor_info["nodeId"]
    neighbor_info_attributes = {
        "source": source,
        "source_long_name": source_long_name,
        "source_short_name": source_short_name,
    }
    for n in neighbor_info["neighbors"]:
        neighbor_source = n["nodeId"]

        neighbor_info_attributes["neighbor_source"] = neighbor_source or "unknown"
        neighbor_info_attributes["neighbor_source_long_name"] = (
            get_decoded_node_metadata_from_cache(cache, neighbor_source, "long_name")
            if source
            else "unknown"
        )
        neighbor_info_attributes["neighbor_source_short_name"] = (
            get_decoded_node_metadata_from_cache(cache, neighbor_source, "short_name")
            if source
            else "unknown"
        )

        meshtastic_neighbor_info_snr_decibels.set(
            n["snr"], attributes=neighbor_info_attributes
        )
        # https://buf.build/meshtastic/protobufs/file/main:meshtastic/mesh.proto#L1795
        # meshtastic_neighbor_info_last_rx_time.set(
        #     n["rxTime"], attributes=neighbor_info_attributes
        # )
