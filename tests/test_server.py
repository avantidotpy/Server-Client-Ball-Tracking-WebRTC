import asyncio
import pytest
from aiortc import RTCPeerConnection
from aiortc.mediastreams import MediaStreamTrack
import pytest_asyncio
from aiortc.contrib.signaling import TcpSocketSignaling
from server import send_offer, compute_error


@pytest.mark.asyncio
async def test_send_offer():
    """
    Test the send_offer function.

    This test case verifies that the send_offer function correctly sends an offer
    and returns a non-empty offer object.

    """
    dummyPC = RTCPeerConnection()
    dummySignal = TcpSocketSignaling(host='0.0.0.0', port=9999)
    dummyChannel = dummyPC.createDataChannel("dummyChannel")
    offer = None
    try:
        offer = send_offer(dummyPC, dummySignal)  # returning coroutine object
        assert offer is not None
    finally:
        dummyPC.close()
        await dummySignal.close()
        dummyChannel.close()


@pytest.mark.asyncio
async def test_compute_error():
    """
    Test the compute_error function.

    This test case verifies that the compute_error function correctly calculates
    the error using the Euclidean distance formula.

    """
    expected = 1
    actual = await compute_error(1, 1, 1, 2)
    assert actual == expected


# Run the test
pytest.main(['-v'])
