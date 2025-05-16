let stream = null;
let scanning = false;

function startQRScanner(spaceId, spaceStatus) {
    console.log(`Starting QR scanner for space ${spaceId}, status: ${spaceStatus}`);

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.error('Camera access not supported by this browser or context.');
        window.dispatchEvent(new CustomEvent('qrCodeScanned', { detail: { qrCode: null, error: 'Camera access not supported.' } }));
        return;
    }

    const video = document.getElementById('qr-video');
    const canvas = document.createElement('canvas');
    canvas.style.display = 'none';
    const videoContainer = document.getElementById('video-container');
    videoContainer.appendChild(canvas);
    const canvasContext = canvas.getContext('2d');
    scanning = true;

    // Access the camera
    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
        .then(function(mediaStream) {
            stream = mediaStream;
            video.srcObject = stream;
            video.play();

            // Start scanning loop
            function scanQRCode() {
                if (!scanning) {
                    console.log('Scanning stopped.');
                    return;
                }

                if (video.readyState === video.HAVE_ENOUGH_DATA) {
                    canvas.height = video.videoHeight;
                    canvas.width = video.videoWidth;
                    canvasContext.drawImage(video, 0, 0, canvas.width, canvas.height);
                    const imageData = canvasContext.getImageData(0, 0, canvas.width, canvas.height);
                    const code = jsQR(imageData.data, imageData.width, imageData.height, {
                        inversionAttempts: 'dontInvert',
                    });

                    if (code) {
                        console.log('QR Code detected:', code.data);
                        scanning = false;
                        // Dispatch custom event with the scanned QR code
                        const event = new CustomEvent('qrCodeScanned', { detail: { qrCode: code.data } });
                        window.dispatchEvent(event);
                        stopCamera(video, canvas);
                        return;
                    }
                }
                requestAnimationFrame(scanQRCode);
            }

            requestAnimationFrame(scanQRCode);
        })
        .catch(function(err) {
            console.error('Error accessing camera:', err);
            scanning = false;
            window.dispatchEvent(new CustomEvent('qrCodeScanned', { detail: { qrCode: null, error: `Camera access failed: ${err.message}` } }));
            stopCamera(video, canvas);
        });
}

function stopCamera(video, canvas) {
    scanning = false;
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }
    if (video) video.srcObject = null;
    if (canvas) canvas.remove();
    console.log('Camera stopped.');
}