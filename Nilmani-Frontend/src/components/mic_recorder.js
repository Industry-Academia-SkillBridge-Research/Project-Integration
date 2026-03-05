import React, { useState, useRef } from "react";

function MicRecorder({ onStop }) {
  const [recording, setRecording] = useState(false);
  const mediaRecorder = useRef(null);
  const audioChunks = useRef([]);

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder.current = new MediaRecorder(stream);

    mediaRecorder.current.ondataavailable = (e) => {
      audioChunks.current.push(e.data);
    };

    mediaRecorder.current.onstop = () => {
      const blob = new Blob(audioChunks.current, { type: "audio/webm" });
      audioChunks.current = [];
      onStop(blob);
    };

    mediaRecorder.current.start();
    setRecording(true);
  };

  const stopRecording = () => {
    mediaRecorder.current.stop();
    setRecording(false);
  };

  return (
    <div style={{ textAlign: "center" }}>
      <button className="button" onClick={startRecording} disabled={recording}>
        ⏺ Start Recording
      </button>

      <button className="button" onClick={stopRecording} disabled={!recording}>
        ⏹ Stop Recording
      </button>
    </div>
  );
}

export default MicRecorder;
