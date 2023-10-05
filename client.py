import asyncio
import cv2
import numpy as np
import multiprocessing
from aiortc import RTCPeerConnection
from aiortc.contrib.signaling import TcpSocketSignaling

# Global variables
FRAME_DB = multiprocessing.Queue()
queue = list()
coords_list = list()
ball_coordinates = list()
shared_x = multiprocessing.Value('i', 0)
shared_y = multiprocessing.Value('i', 0)


async def receive_offer(pc, signaling):
    """
    Receive the offer from the server and send the answer back.

    This function receives the offer from the server via the signaling channel.
    It sets the received offer as the remote description of the client's PeerConnection.

    Then, it creates an answer and sets it as the local description of the client's PeerConnection.
    The answer is sent back to the server via the signaling channel.

    Parameters:
        - pc (RTCPeerConnection): The client's PeerConnection object.
        - signaling (TcpSocketSignaling): The signaling channel for communication with the server.

    Returns:
        - answer: The created answer.

    """
    print("Attempting to receive offer!")
    # Receive the offer from the server
    offer = await signaling.receive()
    print("Received offer from server:\n")
    print(offer)
    # Set the remote description of the client's PeerConnection
    await pc.setRemoteDescription(offer)

    # Create an answer
    answer = await pc.createAnswer()

    # Set the local description of the client's PeerConnection
    await pc.setLocalDescription(answer)

    # Send the answer back to the server
    await signaling.send(answer)

    return answer


async def process_a(mulqueue, coordinates):
    """
    Process frames and extract ball coordinates.

    This function is a separate process that consumes frames from the shared queue.
    It processes the frames to extract the coordinates of the ball and sends them to the server
    via the coordinates data channel.

    Parameters:
        - mulqueue (multiprocessing.Queue): The shared queue for frames.
        - coordinates: The data channel for sending coordinates to the server.

    """
    received_frame = mulqueue.get()
    queue.append(received_frame)
    print(received_frame)
    ball_coordinates = find_ball_coordinates(received_frame)[0]  # Assuming there is always one ball
    print(ball_coordinates)
    coords_list.append(ball_coordinates)

    print("The length of the coords list is: ", len(coords_list))
    print("Received the frame in process_a")

    shared_x.value = ball_coordinates[0]
    shared_y.value = ball_coordinates[1]
    print(f"shared value coords {shared_x.value},{shared_y.value}")

    message = f"Coordinates: {shared_x.value}, {shared_y.value}"
    coordinates.send(message)
    print("MESSAGE SENT")


def find_ball_coordinates(frame):
    """
    Find the coordinates of the ball in a frame.

    This function takes a frame as input and applies image processing techniques
    to detect and extract the coordinates of the ball.

    Parameters:
        - frame: The frame in which the ball is to be detected.

    Returns:
        - ball_coordinates: A list of detected ball coordinates.

    """
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, threshold = cv2.threshold(gray_frame, 1, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    ball_coordinates = []
    for contour in contours:
        # Find the bounding rectangle of the contour
        x, y, w, h = cv2.boundingRect(contour)

        # Calculate the centroid of the bounding rectangle
        cx = x + w // 2
        cy = y + h // 2

        ball_coordinates.append((cx, cy))

    return ball_coordinates


async def main():
    """
    Main entry point for the client application.

    This function sets up the client's PeerConnection and data channel.
    It establishes a connection with the signaling server and performs the signaling exchange.
    Frames received from the server are processed to extract the ball coordinates.

    """
    pc = RTCPeerConnection()

    # Create a data channel for sending coordinates
    coordinates = pc.createDataChannel("coordinates")

    @pc.on('datachannel')
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(curr_frame):
            # Convert the received frame to OpenCV format
            frame_data = np.frombuffer(curr_frame, dtype=np.uint8)
            frame = frame_data.reshape((480, 640, 3))
            frameUpdated = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            cv2.imshow('CLIENT', frameUpdated)
            cv2.waitKey(500)

            # Put the frame into the shared queue for processing
            FRAME_DB.put(frameUpdated)
            asyncio.create_task(process_a(FRAME_DB, coordinates))

    # Create a signaling channel
    signaling = TcpSocketSignaling('0.0.0.0', 8080)

    # Connect to the signaling server
    print("Attempting to connect to server....")
    await signaling.connect()
    print("Connected!")

    p = multiprocessing.Process(target=process_a)
    p.start()

    # Perform the signaling exchange with the server
    await receive_offer(pc, signaling)

    p.terminate()
    p.join()

    # Close the signaling connection
    await signaling.close()

    # Sleep for 100 seconds (for testing purposes)
    await asyncio.sleep(100)



if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
