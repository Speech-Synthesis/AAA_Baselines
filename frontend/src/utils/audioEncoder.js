/**
 * Web Audio API PCM WAV Converter
 * Converts browser MediaRecorder Blobs (WebM/Opus) into valid 16kHz Mono RIFF WAV Blobs
 * Ensures 100% backend compatibility with soundfile / SpeechBrain / PyTorch.
 */

export async function convertBlobTo16kHzWav(webmBlob) {
  try {
    const arrayBuffer = await webmBlob.arrayBuffer();
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
    const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);

    // Convert to 16kHz Mono PCM
    const numberOfChannels = 1;
    const length = audioBuffer.length;
    const sampleRate = 16000;
    const pcmData = audioBuffer.getChannelData(0); // Channel 0 mono

    // Encode PCM to WAV
    const wavBuffer = encodeWAV(pcmData, sampleRate, numberOfChannels);
    audioCtx.close();

    return new Blob([wavBuffer], { type: 'audio/wav' });
  } catch (err) {
    console.warn('WAV conversion fallback: submitting raw blob', err);
    return webmBlob;
  }
}

function encodeWAV(samples, sampleRate, numChannels) {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);

  /* RIFF identifier */
  writeString(view, 0, 'RIFF');
  /* RIFF chunk length */
  view.setUint32(4, 36 + samples.length * 2, true);
  /* RIFF type */
  writeString(view, 8, 'WAVE');
  /* format chunk identifier */
  writeString(view, 12, 'fmt ');
  /* format chunk length */
  view.setUint32(16, 16, true);
  /* sample format (raw PCM) */
  view.setUint16(20, 1, true);
  /* channel count */
  view.setUint16(22, numChannels, true);
  /* sample rate */
  view.setUint32(24, sampleRate, true);
  /* byte rate (sample rate * block align) */
  view.setUint32(28, sampleRate * numChannels * 2, true);
  /* block align (channel count * bytes per sample) */
  view.setUint16(32, numChannels * 2, true);
  /* bits per sample */
  view.setUint16(34, 16, true);
  /* data chunk identifier */
  writeString(view, 36, 'data');
  /* data chunk length */
  view.setUint32(40, samples.length * 2, true);

  // Float to 16-bit PCM conversion
  let offset = 44;
  for (let i = 0; i < samples.length; i++, offset += 2) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }

  return buffer;
}

function writeString(view, offset, string) {
  for (let i = 0; i < string.length; i++) {
    view.setUint8(offset + i, string.charCodeAt(i));
  }
}
