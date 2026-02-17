import logging
import time
import base64
from meshtastic.protobuf import mesh_pb2
from google.protobuf.json_format import MessageToDict
from meshtastic_prometheus_exporter.metrics import *
import json
from meshtastic_prometheus_exporter.util import save_node_metadata_in_cache

logger = logging.getLogger("meshtastic_prometheus_exporter")


def on_meshtastic_nodeinfo_app(cache, packet):
    # Decode the protobuf payload if it exists
    # Newer versions of meshtastic library don't automatically decode all packet types
    if "user" in packet["decoded"]:
        # Already decoded (legacy behavior from older meshtastic library)
        node_info = packet["decoded"]["user"]
    elif "payload" in packet["decoded"]:
        # Need to decode the base64 payload manually
        try:
            payload_bytes = base64.b64decode(packet["decoded"]["payload"])
            user_msg = mesh_pb2.User()
            user_msg.ParseFromString(payload_bytes)
            node_info = MessageToDict(user_msg)
        except Exception as e:
            logger.error(
                f"Failed to decode NODEINFO_APP payload for packet {packet.get('id', 'unknown')}: {e}"
            )
            return
    else:
        logger.error(
            f"NODEINFO_APP packet {packet.get('id', 'unknown')} has neither 'user' nor 'payload' field"
        )
        return

    logger.debug(
        f"Received MeshPacket {packet['id']} with NodeInfo `{json.dumps(node_info, default=repr)}`"
    )

    source = packet["decoded"].get("source", packet["from"])

    if source:
        save_node_metadata_in_cache(cache, source, node_info)

    node_info_attributes = {
        "source": source,
        "user": node_info["id"],
        "source_long_name": node_info["longName"],
        "source_short_name": node_info["shortName"],
        "is_licensed": str(node_info.get("isLicensed", 0)),
    }
    meshtastic_node_info_last_heard_timestamp_seconds.set(
        time.time(), attributes=node_info_attributes
    )
