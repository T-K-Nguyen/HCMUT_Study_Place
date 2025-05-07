let scanning = false;
let stream = null;

function startQRScanner(spaceId, status) {
    console.log('Starting QR scan for spaceId:', spaceId, 'status:', status);
    if (scanning) return;
    scanning = true;

    const video = document.createElement('video');
    const canvasElement = document.createElement('canvas');
    const canvas = canvasElement.getContext('2d');
    video.style.display = 'block';
    video.style.maxWidth = '300px';
    video.style.position = 'fixed';
    video.style.top = '50%';
    video.style.left = '50%';
    video.style.transform = 'translate(-50%, -50%)';
    video.style.border = '2px solid #007bff';
    video.style.borderRadius = '8px';
    video.style.zIndex = '1000';
    canvasElement.style.display = 'none';
    document.body.appendChild(video);
    document.body.appendChild(canvasElement);

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.error('Camera access not supported by this browser.');
        alert('Trình duyệt không hỗ trợ truy cập camera.');
        scanning = false;
        document.body.removeChild(video);
        document.body.removeChild(canvasElement);
        return;
    }

    try {
        console.log('Requesting camera access...');
        stream = navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
        stream.then(stream => {
            console.log('Camera access granted, setting up video...');
            video.srcObject = stream;
            video.play();

            function tick() {
                if (!scanning) return;
                canvasElement.height = video.videoHeight;
                canvasElement.width = video.videoWidth;
                canvas.drawImage(video, 0, 0, canvasElement.width, canvasElement.height);
                const imageData = canvas.getImageData(0, 0, canvasElement.width, canvasElement.height);
                const code = jsQR(imageData.data, imageData.width, imageData.height, {
                    inversionAttempts: 'dontInvert'
                });

                if (code) {
                    const scannedCode = code.data;
                    console.log('QR code detected:', scannedCode);
                    if (status === 'reserved' && scannedCode.startsWith('QR_')) {
                        // Send QR code to server for verification
                        fetch(`/checkin/${spaceId}`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                            body: `qr_code=${encodeURIComponent(scannedCode)}`
                        })
                        .then(response => response.text())
                        .then(text => {
                            alert(text || 'Check-in successful!');
                            if (response.ok) window.location.href = '/dashboard';
                        })
                        .catch(error => {
                            console.error('Check-in error:', error);
                            alert('Check-in failed. Please try again.');
                        });
                    } else {
                        alert(`Mã QR không hợp lệ cho phòng ${spaceId}.`);
                    }
                    stopCamera(video, canvasElement);
                } else {
                    requestAnimationFrame(tick);
                }
            }
            requestAnimationFrame(tick);
        }).catch(error => {
            console.error('Camera error:', error);
            alert('Không thể truy cập camera. Vui lòng kiểm tra quyền truy cập.');
            scanning = false;
            document.body.removeChild(video);
            document.body.removeChild(canvasElement);
        });
    } catch (error) {
        console.error('Camera access failed:', error);
        alert('Không thể truy cập camera. Vui lòng kiểm tra quyền truy cập.');
        scanning = false;
        document.body.removeChild(video);
        document.body.removeChild(canvasElement);
    }
}

function stopCamera(video, canvasElement) {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        document.body.removeChild(video);
        document.body.removeChild(canvasElement);
        scanning = false;
        stream = null;
    }
}