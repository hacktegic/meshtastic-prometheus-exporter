#!/usr/bin/env python3
"""
Test script to verify the NODEINFO_APP packet decoding fix.
This uses real packet data from the error logs to validate the solution.
"""

import base64
import json
from meshtastic.protobuf import mesh_pb2
from google.protobuf.json_format import MessageToDict

# Real packet data from the error logs
test_packets = [
    {
        "from": 1770324184,
        "to": 4294967295,
        "decoded": {
            "portnum": "NODEINFO_APP",
            "payload": "CgkhNjk4NTAwZDgSDERhdmUgLSBBQjBEQhoERGF2ZSIGkHBphQDYKG5CIFmfS9CyDvaGBtg32gaBGskVEQgn/EvJaEo2/0mxa5BJSAA=",
            "bitfield": 1,
        },
        "id": 2849806127,
        "rxTime": 1771350137,
        "rxSnr": -4.5,
        "hopLimit": 3,
        "rxRssi": -115,
        "hopStart": 3,
        "relayNode": 216,
    },
    {
        "from": 649425065,
        "to": 4294967295,
        "decoded": {
            "portnum": "NODEINFO_APP",
            "payload": "CgkhMjZiNTcwYTkSH05WME4gUVRIIGh0dHBzOi8vZGVudmVybWVzaC5vcmcaBPCfj6AiBvmOJrVwqSgJOAFCIJkRD1Mu/yLE74nGS70/UY8Daqz92p/UAAuOPs9yTMo/SAA=",
            "bitfield": 1,
        },
        "id": 986512456,
        "rxTime": 1771350154,
        "rxSnr": -5.0,
        "hopLimit": 5,
        "rxRssi": -116,
        "hopStart": 7,
        "relayNode": 81,
    },
]


def decode_nodeinfo_packet(packet):
    """
    Decode a NODEINFO_APP packet using the new fix.
    """
    print(f"\n{'='*60}")
    print(f"Processing Packet ID: {packet['id']}")
    print(f"From Node: {packet['from']}")
    print(f"{'='*60}")

    if "user" in packet["decoded"]:
        # Already decoded (legacy behavior)
        print("✓ Using pre-decoded 'user' field (legacy)")
        node_info = packet["decoded"]["user"]
    elif "payload" in packet["decoded"]:
        # Need to decode the base64 payload manually
        print("✓ Decoding base64 payload manually (new fix)")
        try:
            payload_bytes = base64.b64decode(packet["decoded"]["payload"])
            user_msg = mesh_pb2.User()
            user_msg.ParseFromString(payload_bytes)
            node_info = MessageToDict(user_msg)
            print(f"✓ Successfully decoded User message")
        except Exception as e:
            print(f"✗ Failed to decode: {e}")
            return None
    else:
        print("✗ Packet has neither 'user' nor 'payload' field")
        return None

    # Print the decoded node info
    print(f"\nDecoded Node Info:")
    print(f"  ID: {node_info.get('id', 'N/A')}")
    print(f"  Long Name: {node_info.get('longName', 'N/A')}")
    print(f"  Short Name: {node_info.get('shortName', 'N/A')}")
    print(f"  HW Model: {node_info.get('hwModel', 'N/A')}")
    print(f"  Is Licensed: {node_info.get('isLicensed', False)}")
    print(f"  Role: {node_info.get('role', 'N/A')}")

    # Verify all required fields are present
    required_fields = ["id", "longName", "shortName"]
    missing_fields = [f for f in required_fields if f not in node_info]

    if missing_fields:
        print(f"\n⚠ Warning: Missing required fields: {missing_fields}")
    else:
        print(f"\n✓ All required fields present")

    return node_info


def main():
    print("="*60)
    print("Testing NODEINFO_APP Packet Decoding Fix")
    print("="*60)

    success_count = 0
    for i, packet in enumerate(test_packets, 1):
        try:
            node_info = decode_nodeinfo_packet(packet)
            if node_info:
                success_count += 1
                print(f"\n✓ Packet {i}/{len(test_packets)} decoded successfully")
            else:
                print(f"\n✗ Packet {i}/{len(test_packets)} failed to decode")
        except Exception as e:
            print(f"\n✗ Packet {i}/{len(test_packets)} threw exception: {e}")
            import traceback

            traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"Results: {success_count}/{len(test_packets)} packets decoded successfully")
    print(f"{'='*60}")

    if success_count == len(test_packets):
        print("\n✓ All tests passed! The fix is working correctly.")
        return 0
    else:
        print(f"\n✗ {len(test_packets) - success_count} test(s) failed.")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
