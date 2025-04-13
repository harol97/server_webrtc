var pc = null;
var dc = null,
  dcInterval = null;
const ZoomVideo = window.WebVideoSDK.default;
const TwilioVideo = Twilio.Video;

function createPeerConnection() {
  var config = {
    sdpSemantics: "unified-plan",
  };
  if (document.getElementById("use-stun").checked) {
    config.iceServers = [{ urls: ["stun:stun.l.google.com:19302"] }];
  }
  pc = new RTCPeerConnection(config);
  pc.addEventListener("icegatheringstatechange", () => {}, false);
  pc.addEventListener("iceconnectionstatechange", () => {}, false);
  pc.addEventListener("signalingstatechange", () => {}, false);
  pc.addEventListener("track", (evt) => {
    console.log("eventos", evt.track);
    document.getElementById("video").srcObject = evt.streams[0];
    // startVideoTwilio(evt.track);
  });

  return pc;
}

function enumerateInputDevices() {
  const populateSelect = (select, devices) => {
    let counter = 1;
    devices.forEach((device) => {
      const option = document.createElement("option");
      option.value = device.deviceId;
      option.text = device.label || "Device #" + counter;
      select.appendChild(option);
      counter += 1;
    });
  };

  navigator.mediaDevices
    .enumerateDevices()
    .then((devices) => {
      console.log(devices);
      populateSelect(
        document.getElementById("video-input"),
        devices.filter((device) => device.kind == "videoinput")
      );
    })
    .catch((e) => {
      alert("hola" + e);
    });
}

function negotiate() {
  return pc
    .createOffer()
    .then((offer) => {
      return pc.setLocalDescription(offer);
    })
    .then(() => {
      // wait for ICE gathering to complete
      return new Promise((resolve) => {
        if (pc.iceGatheringState === "complete") {
          resolve();
        } else {
          function checkState() {
            if (pc.iceGatheringState === "complete") {
              pc.removeEventListener("icegatheringstatechange", checkState);
              resolve();
            }
          }
          pc.addEventListener("icegatheringstatechange", checkState);
        }
      });
    })
    .then(() => {
      var offer = pc.localDescription;
      var codec;

      codec = document.getElementById("video-codec").value;
      if (codec !== "default") {
        offer.sdp = sdpFilterCodec("video", codec, offer.sdp);
      }

      return fetch("/api/offer", {
        body: JSON.stringify({
          sdp: offer.sdp,
          type: offer.type,
          userId: "harol",
        }),
        headers: {
          "Content-Type": "application/json",
        },
        method: "POST",
      });
    })
    .then((response) => response.json())
    .then((answer) => pc.setRemoteDescription({ ...answer }))
    .catch((e) => alert("error" + e));
}

function start() {
  pc = createPeerConnection();

  if (document.getElementById("use-datachannel").checked) {
    var parameters = JSON.parse(
      document.getElementById("datachannel-parameters").value
    );

    dc = pc.createDataChannel("chat", parameters);
    dc.addEventListener("close", () => {
      clearInterval(dcInterval);
    });
    dc.addEventListener("open", () => {
      // dcInterval = setInterval(() => {
      //   dc.send(message);
      // }, 1000);
    });
    dc.addEventListener("message", (evt) => {});
  }

  const constraints = {
    audio: false,
    video: {
      height: 300,
      width: 300,
    },
  };

  const device = document.getElementById("video-input").value;
  if (device) {
    constraints.video.deviceId = { exact: device };
  }

  document.getElementById("media").style.display = "block";
  navigator.mediaDevices.getUserMedia(constraints).then(
    (stream) => {
      stream.getTracks().forEach((track) => {
        pc.addTrack(track, stream);
      });
      return negotiate();
    },
    (err) => {
      alert("Could not acquire media: " + err);
    }
  );

  document.getElementById("stop").style.display = "inline-block";
}

function stop() {
  document.getElementById("stop").style.display = "none";

  // close data channel
  if (dc) {
    dc.close();
  }

  // close transceivers
  if (pc.getTransceivers) {
    pc.getTransceivers().forEach((transceiver) => {
      if (transceiver.stop) {
        transceiver.stop();
      }
    });
  }

  pc.getSenders().forEach((sender) => {
    sender.track.stop();
  });

  // close peer connection
  setTimeout(() => {
    pc.close();
  }, 500);
}

function sdpFilterCodec(kind, codec, realSdp) {
  var allowed = [];
  var rtxRegex = new RegExp("a=fmtp:(\\d+) apt=(\\d+)\r$");
  var codecRegex = new RegExp("a=rtpmap:([0-9]+) " + escapeRegExp(codec));
  var videoRegex = new RegExp("(m=" + kind + " .*?)( ([0-9]+))*\\s*$");

  var lines = realSdp.split("\n");

  var isKind = false;
  for (var i = 0; i < lines.length; i++) {
    if (lines[i].startsWith("m=" + kind + " ")) {
      isKind = true;
    } else if (lines[i].startsWith("m=")) {
      isKind = false;
    }

    if (isKind) {
      var match = lines[i].match(codecRegex);
      if (match) {
        allowed.push(parseInt(match[1]));
      }

      match = lines[i].match(rtxRegex);
      if (match && allowed.includes(parseInt(match[2]))) {
        allowed.push(parseInt(match[1]));
      }
    }
  }

  var skipRegex = "a=(fmtp|rtcp-fb|rtpmap):([0-9]+)";
  var sdp = "";

  isKind = false;
  for (var i = 0; i < lines.length; i++) {
    if (lines[i].startsWith("m=" + kind + " ")) {
      isKind = true;
    } else if (lines[i].startsWith("m=")) {
      isKind = false;
    }

    if (isKind) {
      var skipMatch = lines[i].match(skipRegex);
      if (skipMatch && !allowed.includes(parseInt(skipMatch[2]))) {
        continue;
      } else if (lines[i].match(videoRegex)) {
        sdp += lines[i].replace(videoRegex, "$1 " + allowed.join(" ")) + "\n";
      } else {
        sdp += lines[i] + "\n";
      }
    } else {
      sdp += lines[i] + "\n";
    }
  }

  return sdp;
}

function startVideoTwilio(track) {
  const token = document.getElementById("username").value;

  // TwilioVideo.connect(
  //   token,
  //   { name: "testing", tracks: [track] }
  // ).then(
  //   (room) => {
  //     console.log(`Successfully joined a Room: ${room}`);

  //     room.on("participantConnected", (participant) => {
  //       console.log(`A remote Participant connected: ${participant}`);
  //     });
  //   },
  //   (error) => {
  //     console.error(`Unable to connect to Room: ${error.message}`);
  //   }
  // );
  //
  TwilioVideo.connect(token, { name: "test", tracks: [track] }).then(
    (room) => {
      console.log(`Successfully joined a Room: ${room}`);
      console.log(room.participants);
      room.participants.forEach((participant) => {
        participant.tracks.forEach((publication) => {
          if (publication.isSubscribed) {
            const track = publication.track;

            document
              .getElementById("remote-media-div")
              .appendChild(track.attach());
          }
        });

        participant.on("trackSubscribed", (track) => {
          document
            .getElementById("remote-media-div")
            .appendChild(track.attach());
        });
      });
      room.on("participantConnected", (participant) => {
        console.log(`Participant "${participant.identity}" connected`);

        participant.tracks.forEach((publication) => {
          if (publication.isSubscribed) {
            const track = publication.track;

            document
              .getElementById("remote-media-div")
              .appendChild(track.attach());
          }
        });

        participant.on("trackSubscribed", (track) => {
          document
            .getElementById("remote-media-div")
            .appendChild(track.attach());
        });
      });
    },
    (error) => {
      console.error(`Unable to connect to Room: ${error.message}`);
    }
  );
}

function startVideoZoom(track) {
  console.log(document.getElementById("video").captureStream());
  const localVideoTrack = ZoomVideo.createLocalVideoTrack(track);
  getZoomStream().then(({ stream, client }) => {
    stream.startVideo({ originalRatio: true }).then(() => {
      stream.renderVideo(
        document.getElementById("canvas-local"),
        client.getCurrentUserInfo().userId,
        400,
        400,
        0,
        0,
        3
      );
    });
  });
  // ZoomVideo.getZoomStream().startVideo();
}

function escapeRegExp(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); // $& means the whole matched string
}

function generateSignature() {
  const iat = Math.round(new Date().getTime() / 1000) - 30;
  const exp = iat + 60 * 600 * 2;
  const oHeader = { alg: "HS256", typ: "JWT" };

  const oPayload = {
    app_key: "DTC6f93OSNuJrMj57yqaUQ",
    tpc: "nuevo",
    role_type: 1,
    session_key: "1234",
    version: 1,
    iat: iat,
    exp: exp,
  };
  const sHeader = JSON.stringify(oHeader);
  const sPayload = JSON.stringify(oPayload);
  // @ts-ignore
  const sdkJWT = KJUR.jws.JWS.sign(
    "HS256",
    sHeader,
    sPayload,
    "LKX4EmXNz2sQvFhXYweeMyXUkyI1bhTXNOuD"
  );
  return sdkJWT;
}

enumerateInputDevices();
