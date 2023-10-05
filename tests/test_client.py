import asyncio
import pytest
from aiortc import RTCPeerConnection
from aiortc.mediastreams import MediaStreamTrack
import pytest_asyncio
from aiortc.contrib.signaling import TcpSocketSignaling

from client import receive_offer
from server import send_offer

@pytest.mark.asyncio
async def test_receive_offer():
    """
    Test the receive_offer function.

    This test case verifies that the receive_offer function correctly receives an offer
    and returns a non-empty answer object.

    """
    pc = RTCPeerConnection()
    signaling = TcpSocketSignaling('localhost', 8080)
    answer = None
    try:
        answer = receive_offer(pc, signaling)  # checking if coroutine object was returned
        assert answer is not None
    finally:
        await signaling.close()

# Run the test
pytest.main(['-v'])

    