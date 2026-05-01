/**
 * face-auth.js
 * Handles webcam access, countdown animation, and face photo capture.
 * Used by both login and register pages.
 */

class FaceCapture {
    /**
     * @param {object} opts
     * @param {HTMLVideoElement}  opts.video
     * @param {HTMLCanvasElement} opts.canvas
     * @param {HTMLElement}       opts.ring            – the circular container (.webcam-ring)
     * @param {HTMLElement}       opts.countdownEl     – the overlay element (.countdown-ring)
     * @param {HTMLElement}       [opts.placeholder]   – the placeholder shown before camera starts
     */
    constructor({ video, canvas, ring, countdownEl, placeholder }) {
        this.video        = video;
        this.canvas       = canvas;
        this.ring         = ring;
        this.countdownEl  = countdownEl;
        this.placeholder  = placeholder;
        this.stream       = null;
        this.capturedBlob = null;
        this._abortCountdown = false;
    }

    /** Start the webcam stream. */
    async start() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
                audio: false,
            });
        } catch (err) {
            if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
                throw new Error('Camera permission denied. Please allow camera access in your browser.');
            }
            if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
                throw new Error('No camera found. Please connect a camera and try again.');
            }
            throw new Error('Could not start camera: ' + err.message);
        }

        this.video.srcObject = this.stream;

        await new Promise((resolve, reject) => {
            this.video.onloadedmetadata = resolve;
            this.video.onerror          = () => reject(new Error('Camera stream error.'));
            setTimeout(() => reject(new Error('Camera timed out.')), 10_000);
        });

        await this.video.play();

        if (this.ring)        this.ring.classList.add('live');
        if (this.placeholder) this.placeholder.style.display = 'none';
        this.video.style.display = 'block';
    }

    /** Stop the webcam stream and clean up. */
    stop() {
        if (this.stream) {
            this.stream.getTracks().forEach(t => t.stop());
            this.stream = null;
        }
        if (this.ring) this.ring.classList.remove('live');
    }

    /**
     * Capture the current video frame as a JPEG Blob.
     * Note: canvas draw is NOT mirrored – the server needs the real orientation.
     * @returns {Promise<Blob>}
     */
    capture() {
        const ctx = this.canvas.getContext('2d');
        this.canvas.width  = this.video.videoWidth  || 640;
        this.canvas.height = this.video.videoHeight || 480;
        ctx.drawImage(this.video, 0, 0);

        return new Promise(resolve => {
            this.canvas.toBlob(blob => {
                this.capturedBlob = blob;
                resolve(blob);
            }, 'image/jpeg', 0.92);
        });
    }

    /**
     * Show a visual countdown overlay, then return the captured blob.
     * @param {number} seconds
     * @param {function} [onTick]  called each second with remaining count
     * @returns {Promise<Blob>}
     */
    async countdown(seconds = 3, onTick) {
        this._abortCountdown = false;
        if (this.countdownEl) this.countdownEl.classList.add('visible');

        for (let i = seconds; i >= 1; i--) {
            if (this._abortCountdown) break;
            if (this.countdownEl) this.countdownEl.textContent = i;
            if (onTick) onTick(i);
            await _sleep(1000);
        }

        if (!this._abortCountdown) {
            if (this.countdownEl) this.countdownEl.textContent = '📸';
            await _sleep(250);
        }
        if (this.countdownEl) this.countdownEl.classList.remove('visible');

        return this._abortCountdown ? null : this.capture();
    }

    /** Cancel an in-progress countdown. */
    cancelCountdown() {
        this._abortCountdown = true;
        if (this.countdownEl) this.countdownEl.classList.remove('visible');
    }
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function _sleep(ms) {
    return new Promise(r => setTimeout(r, ms));
}

/**
 * Convert a Blob to a base64 data-URL for <img src>.
 * @param {Blob} blob
 * @returns {Promise<string>}
 */
function blobToDataURL(blob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload  = e => resolve(e.target.result);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
    });
}
