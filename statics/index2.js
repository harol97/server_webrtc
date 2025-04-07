// get DOM elements

// peer connection
var pc = null;

// data channel
var dc = null,
  dcInterval = null;

function createPeerConnection() {
  var config = {
    sdpSemantics: "unified-plan",
  };

  if (document.getElementById("use-stun").checked) {
    config.iceServers = [{ urls: ["stun:stun.l.google.com:19302"] }];
  }

  pc = new RTCPeerConnection(config);

  // register some listeners to help debugging

  // connect audio / video
  pc.addEventListener("track", (evt) => {
    if (evt.track.kind == "video")
      document.getElementById("video").srcObject = evt.streams[0];
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
      populateSelect(
        document.getElementById("video-input"),
        devices.filter((device) => device.kind == "videoinput")
      );
    })
    .catch((e) => {
      alert(e + "1");
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

      return fetch("/offer", {
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
    .then((response) => {
      return response.json();
    })
    .then((answer) => {
      console.log(answer);
      return pc.setRemoteDescription(answer);
    })
    .catch((e) => {
      alert(e + "asdsa");
    });
}

function start() {
  document.getElementById("start").style.display = "none";

  pc = createPeerConnection();

  var time_start = null;

  const current_stamp = () => {
    if (time_start === null) {
      time_start = new Date().getTime();
      return 0;
    } else {
      return new Date().getTime() - time_start;
    }
  };

  if (document.getElementById("use-datachannel").checked) {
    var parameters = JSON.parse(
      document.getElementById("datachannel-parameters").value
    );

    dc = pc.createDataChannel("chat", parameters);
    dc.addEventListener("close", () => {
      clearInterval(dcInterval);
    });
    dc.addEventListener("open", () => {
      dcInterval = setInterval(() => {
        var message = "ping " + current_stamp();
        dc.send(message);
      }, 1000);
    });
    dc.addEventListener("message", (evt) => {
      if (evt.data.substring(0, 4) === "pong") {
        var elapsed_ms = current_stamp() - parseInt(evt.data.substring(5), 10);
      }
    });
  }

  // Build media constraints.

  const constraints = {
    audio: false,
    video: false,
  };

  if (document.getElementById("use-video").checked) {
    const videoConstraints = {};

    const device = document.getElementById("video-input").value;
    if (device) {
      videoConstraints.deviceId = { exact: device };
    }

    videoConstraints.width = 100;
    videoConstraints.height = 100;
    constraints.video = Object.keys(videoConstraints).length
      ? videoConstraints
      : true;
  }

  // Acquire media and start negociation.

  if (constraints.audio || constraints.video) {
    if (constraints.video) {
      document.getElementById("media").style.display = "block";
    }
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
  } else {
    negotiate();
  }

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

  // close local audio / video
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

function escapeRegExp(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); // $& means the whole matched string
}

enumerateInputDevices();
