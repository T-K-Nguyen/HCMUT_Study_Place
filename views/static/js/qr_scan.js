let scanning = false;
let stream = null;

async function startQRScanner(spaceId, status) {
    console.log('Starting QR scan for spaceId:', spaceId, 'status:', status);
    if (scanning) {
        console.log('Scanning already in progress, ignoring request.');
        return;
    }
    scanning = true;

    // Create video and canvas elements
    const video = document.createElement('video');
    const canvasElement = document.createElement('canvas');
    const canvas = canvasElement.getContext('2d', { willReadFrequently: true }); // Optimize for frequent reads

    // Style the video element
    video.style.display = 'block';
    video.style.maxWidth = '90%';
    video.style.width = '300px';
    video.style.position = 'fixed';
    video.style.top = '50%';
    video.style.left = '50%';
    video.style.transform = 'translate(-50%, -50%)';
    video.style.border = '2px solid #007bff';
    video.style.borderRadius = '8px';
    video.style.zIndex = '1000';
    video.style.backgroundColor = 'black'; // Ensure visibility
    canvasElement.style.display = 'none';

    // Append elements to the DOM
    document.body.appendChild(video);
    document.body.appendChild(canvasElement);

    // Check for camera support
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
        stream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: 'environment', // Prefer rear camera
                width: { ideal: 1280 }, // Higher resolution for better QR detection
                height: { ideal: 720 }
            }
        });

        console.log('Camera access granted, setting up video...');
        video.srcObject = stream;
        await video.play(); // Ensure video is playing

        // Wait for video metadata to load
        await new Promise(resolve => {
            video.onloadedmetadata = () => {
                console.log('Video metadata loaded:', video.videoWidth, 'x', video.videoHeight);
                resolve();
            };
        });

        // Set canvas dimensions to match video
        canvasElement.width = video.videoWidth;
        canvasElement.height = video.videoHeight;

        // Scanning loop
        async function tick() {
            if (!scanning) {
                console.log('Scanning stopped.');
                return;
            }

            // Draw the current video frame onto the canvas
            canvas.drawImage(video, 0, 0, canvasElement.width, canvasElement.height);
            const imageData = canvas.getImageData(0, 0, canvasElement.width, canvasElement.height);

            // Attempt to detect QR code
            const code = jsQR(imageData.data, imageData.width, imageData.height, {
                inversionAttempts: 'dontInvert' // Optimize for standard QR codes
            });

            if (code) {
                const scannedCode = code.data;
                console.log('QR code detected:', scannedCode);

                // Update UI with scan result
                const qrResults = document.getElementById('qr-reader-results');
                if (qrResults) {
                    qrResults.innerText = `Scan result: ${scannedCode}`;
                }

                // Validate QR code format
                if (status === 'reserved' && scannedCode.startsWith('QR_')) {
                    console.log('Sending QR code to server...');
                    try {
                        const response = await fetch(`/checkin/${spaceId}`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                            body: `qr_code=${encodeURIComponent(scannedCode)}`
                        });

                        const text = await response.text();
                        console.log('Server response:', text);
                        alert(text || 'Check-in successful!');
                        if (response.ok) {
                            window.location.href = '/dashboard';
                        }
                    } catch (error) {
                        console.error('Check-in error:', error);
                        alert('Check-in failed. Please try again.');
                    }
                } else {
                    console.warn('Invalid QR code for spaceId:', spaceId);
                    alert(`Mã QR không hợp lệ cho phòng ${spaceId}.`);
                }
                stopCamera(video, canvasElement);
            } else {
                // Continue scanning
                requestAnimationFrame(tick);
            }
        }

        // Start scanning
        console.log('Starting scanning loop...');
        requestAnimationFrame(tick);

    } catch (error) {
        console.error('Camera access failed:', error);
        alert('Không thể truy cập camera. Vui lòng kiểm tra quyền truy cập.');
        scanning = false;
        document.body.removeChild(video);
        document.body.removeChild(canvasElement);
    }
}

function stopCamera(video, canvasElement) {
    console.log('Stopping camera...');
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        document.body.removeChild(video);
        document.body.removeChild(canvasElement);
        scanning = false;
        stream = null;
    }
}