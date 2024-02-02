let mediaRecorder;
let audioChunks = [];

document.getElementById("startRecord").onclick = function() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.ondataavailable = function(e) {
                audioChunks.push(e.data);
            };
            mediaRecorder.onstop = function() {
                const audioBlob = new Blob(audioChunks, { 'type' : 'audio/wav; codecs=opus' });
                const formData = new FormData();
                formData.append("audio", audioBlob);

                fetch("/chat", {
                    method: "POST",
                    body: formData,
                }).then(response => response.json()).then(data => {
                    const chatWindow = document.getElementById("chatWindow");
                    const userMessage = document.createElement("div");
                    userMessage.classList.add("message", "user-message");
                    userMessage.innerText = data.response;
                    chatWindow.appendChild(userMessage);

                    const systemMessage = document.createElement("div");
                    systemMessage.classList.add("message", "system-message");
                    systemMessage.innerText = "챗봇응답: 개발중...";
                    chatWindow.appendChild(systemMessage);
                }).catch(console.error);

                audioChunks = [];
            };
            mediaRecorder.start();
            document.getElementById("stopRecord").disabled = false;
        }).catch(console.error);
};

document.getElementById("stopRecord").onclick = function() {
    mediaRecorder.stop();
    document.getElementById("stopRecord").disabled = true;
};
