from datetime import timedelta

from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaBlackhole, MediaRelay
from av.video.frame import VideoFrame

from src.utils.redis_manager import RedisManager
from src.utils.yolov_tracker.drawer import Drawer
from src.utils.yolov_tracker.tracker_manager import Tracker


class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"

    def __init__(self, track: MediaStreamTrack, yolov_tracker: Tracker, user_id: str):
        super().__init__()
        self.track = track
        self.yolov_tracker = yolov_tracker
        self.drawer = Drawer()
        self.redis_obj = RedisManager(
            host="localhost", port=6379, decode_responses=True, test_connection=True
        )

        self.user_id = user_id

    async def recv(self):
        frame = await self.track.recv()
        try:
            if not isinstance(frame, VideoFrame):
                raise Exception("Is not VideoFrame")
            frame_to_process = frame.to_ndarray(format="bgr24")
            results = self.yolov_tracker.get_tracks(frame_to_process)
            for result in results:
                self.redis_obj.set(
                    f"{self.user_id}:{result.track_id}",
                    result.model_dump_json(),
                    px=200,
                )
            frame_result = self.drawer.draw(frame_to_process, results)
            new_frame = VideoFrame.from_ndarray(frame_result, format="bgr24")  # type: ignore
            new_frame.pts = frame.pts
            new_frame.time_base = frame.time_base
            return new_frame
        except Exception as e:
            print("error in redis >> ", e)

        return frame


def on_track(
    track: MediaStreamTrack,
    pc: RTCPeerConnection,
    yolov_tracker: Tracker,
    user_id: str,
    recorder: MediaBlackhole,
):
    relay = MediaRelay()
    pc.addTrack(VideoTransformTrack(relay.subscribe(track), yolov_tracker, user_id))
    track.on("ended", recorder.stop)


async def on_connectionstatechange(pc: RTCPeerConnection):
    if pc.connectionState == "failed":
        await pc.close()


async def create_session(
    sdp: str, session_type: str, user_id: str
) -> RTCSessionDescription:
    offer = RTCSessionDescription(sdp=sdp, type=session_type)

    pc = RTCPeerConnection()
    recorder = MediaBlackhole()
    yolov_tracker = Tracker()
    pc.on("track", lambda track: on_track(track, pc, yolov_tracker, user_id, recorder))
    pc.on("connectionstatechange", lambda: on_connectionstatechange(pc))

    await pc.setRemoteDescription(offer)
    await recorder.start()

    answer = await pc.createAnswer()
    if answer is not None:
        await pc.setLocalDescription(answer)

    return pc.localDescription
