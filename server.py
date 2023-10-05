import asyncio
import cv2
import numpy as np
from aiortc import MediaStreamTrack, RTCPeerConnection
from aiortc.contrib.signaling import TcpSocketSignaling
from av.video.frame import VideoFrame
import random
import time
import multiprocessing
import math

# BALL PARAMETERS
WIDTH = 640
HEIGHT = 480
FPS = 30

BLACK = (0, 0, 0)
RED = (255, 0, 0)
BALL_RADIUS = 20

BALL_CURR_X = multiprocessing.Value('i',0)
BALL_CURR_Y = multiprocessing.Value('i',0)

BALL_LOCK = multiprocessing.Lock()

class BallTrack(MediaStreamTrack):
    """
    A custom MediaStreamTrack implementation for tracking a bouncing ball.
    """

    kind = "video"

    def __init__(self):
        super().__init__()

    async def recv(self):
        """
        Receive video frames with a bouncing ball.

        Returns:
            AsyncIterator: An asynchronous iterator that generates video frames with a bouncing ball.
        """
        print("Generating Frames")
        pts = 0
        center_x = WIDTH // 2  # Start at the center x-coordinate
        center_y = HEIGHT // 2  # Start at the center y-coordinate
        dy = 10  # Change in y-value for bouncing
        BALL_CURR_X.value = center_x
        while True:
            frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
            frame.fill(0)

            center_y += dy  # Update the y-coordinate

            # Check if the ball has reached the top or bottom edge
            if center_y - BALL_RADIUS < 0 or center_y + BALL_RADIUS > HEIGHT:
                dy = -dy  # Reverse the direction of the change

            with BALL_LOCK:
                BALL_CURR_Y.value = center_y
            cv2.circle(frame, (center_x, center_y), BALL_RADIUS, RED, -1)

            frame_bytes = frame.tobytes()

            time_base = 1 / FPS
            pts += int(90000 * time_base)

            video_frame = VideoFrame.from_ndarray(frame, format="bgr24")
            video_frame.pts = pts
            video_frame.time_base = pts

            yield video_frame

            await asyncio.sleep(1/FPS)

async def send_offer(pc, signaling):
    """
    Send the offer to the client for establishing the connection.

    Args:
        pc (RTCPeerConnection): The server's PeerConnection instance.
        signaling (TcpSocketSignaling): The signaling object for communication.

    Returns:
        RTCSessionDescription: The generated offer to be sent to the client.
    """
    print("Creating the offer to connect to the client.")
    offer = await pc.createOffer()
    print("Generated offer:\n")
    print(offer)
    print("\n")
    await pc.setLocalDescription(offer)

    # Send the offer to the client
    try:
        await signaling.send(pc.localDescription)
        print("Offer sent!")
    except ConnectionError as e:
        print("Failed to send offer:", e)
    except OSError as e:
        print("Failed to send offer:", e)

    return offer

async def receive_answer(pc, signaling):
    """
    Receive the answer from the client and set it as the remote description.

    Args:
        pc (RTCPeerConnection): The server's PeerConnection instance.
        signaling (TcpSocketSignaling): The signaling object for communication.
    """
    # Receive the answer from the client
    answer = await signaling.receive()
    print("Answer received:\n")
    print(answer)

    # Set the remote description of the server's PeerConnection
    await pc.setRemoteDescription(answer)

async def compute_error(actual_x, actual_y, est_x, est_y):
    """
    Compute the error between actual and estimated ball coordinates.

    Args:
        actual_x (int): The actual x-coordinate of the ball.
        actual_y (int): The actual y-coordinate of the ball.
        est_x (int): The estimated x-coordinate of the ball.
        est_y (int): The estimated y-coordinate of the ball.

    Returns:
        float: The distance error between actual and estimated coordinates.

    """
    dx = actual_x - est_x
    dy = actual_y - est_y
    distance = math.sqrt(dx**2 + dy**2)
    print(f"Error in estimation: {distance}")
    return distance

async def main():
    """
    Main entry point for the server application.

    This function initializes the server's PeerConnection, sets up a data channel for communication,
    and manages the video frames and coordinate messages received from the client.

    The main steps performed in this function are as follows:

    1. Create an instance of RTCPeerConnection.
    2. Create a BallTrack instance and add it as a media stream track to the PeerConnection.
    3. Create a data channel named "data" for bidirectional communication.
    4. Set up a handler for the "open" event on the data channel.
       - When the channel is opened, start generating video frames with a bouncing ball.
       - Send the frames to the client by converting them to bytes and sending them over the channel.
    5. Set up a handler for the "datachannel" event on the PeerConnection.
       - When a data channel is received from the client, set up a handler for the "message" event.
       - When a coordinate message is received, extract the x and y coordinates and compare them with the actual ball coordinates.
       - Compute and print the error in estimation.
    6. Connect to the signaling server using TcpSocketSignaling.
    7. Start a separate process for computing the error (optional).
    8. Send the offer to the client for establishing the connection.
    9. Wait for the answer from the client.
    10. Terminate the error computation process.
    11. Close the signaling connection.
    12. Sleep for 100 seconds (for testing purposes).

    Note: The BALL_LOCK global variable is used to synchronize access to the ball coordinates.
    """

    # Step 1: Create an instance of RTCPeerConnection
    pc = RTCPeerConnection()

    # Step 2: Create a BallTrack instance and add it as a media stream track to the PeerConnection
    ball_track = BallTrack()
    pc.addTrack(ball_track)

    # Step 3: Create a data channel named "data" for bidirectional communication
    channel = pc.createDataChannel("data")
    print("Created data channel!")

    @channel.on("open")
    def on_open():
        """
        Handler for the "open" event on the data channel.

        This function is called when the data channel is opened and ready for communication.

        It starts generating video frames with a bouncing ball and sends them to the client
        by converting them to bytes and sending them over the channel.
        """
        frames = ball_track.recv()

        async def send_frames():
            """
            Asynchronously send video frames to the client.

            This function is responsible for sending the video frames with a bouncing ball
            to the client over the data channel.

            It converts each frame to bytes and sends them over the channel.
            """
            async for video_frame in frames:
                frame_data = video_frame.to_ndarray(format="bgr24")
                frame_bytes = frame_data.tobytes()
                channel.send(frame_bytes)

        asyncio.create_task(send_frames())

    @pc.on("datachannel")
    def on_receive(coordinates):
        """
        Handler for the "datachannel" event on the PeerConnection.

        This function is called when a data channel is received from the client.

        It sets up a handler for the "message" event on the received data channel.

        When a coordinate message is received, it extracts the x and y coordinates
        and compares them with the actual ball coordinates.

        It computes and prints the error in estimation.
        """
        @coordinates.on("message")
        def rece_msg(msg):
            print(f'received coords: {msg}')

            # Find the index of the first occurrence of ":"
            start_index = msg.index(":") + 1

            # Extract the substring after the ":"
            coords_substring = msg[start_index:]

            # Split the substring by ","
            coords_list = coords_substring.split(",")

            # Extract the x and y coordinates
            est_x = int(coords_list[0].strip())
            est_y = int(coords_list[1].strip())

            with BALL_LOCK:
                act_x = BALL_CURR_X.value
                act_y = BALL_CURR_Y.value

            print(f'act_x:{act_x} act_y:{act_y} est_x:{est_x} est_y:{est_y}')
            asyncio.create_task(compute_error(act_x, act_y, est_x, est_y))

    # Step 6: Connect to the signaling server using TcpSocketSignaling
    signaling = TcpSocketSignaling(host='0.0.0.0', port=8080)
    await signaling.connect()
    print("Signaling connected")

    # Step 7: Start a separate process for computing the error (optional)
    p = multiprocessing.Process(target=compute_error)

    # Step 8: Send the offer to the client for establishing the connection
    await send_offer(pc, signaling)
    p.start()

    # Step 9: Wait for the answer from the client
    await receive_answer(pc, signaling)

    # Step 10: Terminate the error computation process
    p.terminate()
    p.join()

    # Step 11: Close the signaling connection
    await signaling.close()

    # Step 12: Sleep for 100 seconds (for testing purposes)
    await asyncio.sleep(100)



if __name__ == '__main__':
    async def server():
        await main()

    asyncio.run(server())
