import { HQ_ASSETS } from './shop-items.js';

const maskedUrlCache = new Map();
let emptyImageData = null;
let emptyDimensions = null;

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error(`Failed to load image: ${src}`));
    img.src = src;
  });
}

async function loadEmptyReference() {
  if (emptyImageData && emptyDimensions) {
    return emptyDimensions;
  }

  const img = await loadImage(HQ_ASSETS.roomBase);
  const canvas = document.createElement('canvas');
  canvas.width = img.naturalWidth;
  canvas.height = img.naturalHeight;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  if (!ctx) {
    throw new Error('Canvas unavailable');
  }

  ctx.drawImage(img, 0, 0);
  emptyImageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
  emptyDimensions = { width: canvas.width, height: canvas.height };
  return emptyDimensions;
}

/**
 * Mask furniture using pixel difference from RoomEmpty (keeps isometric alignment).
 * @param {string} src
 * @param {number} threshold
 */
export async function getMaskedImageUrl(src, threshold = 45) {
  if (maskedUrlCache.has(src)) {
    return maskedUrlCache.get(src);
  }

  const empty = await loadEmptyReference();
  const img = await loadImage(src);
  const canvas = document.createElement('canvas');
  canvas.width = empty.width;
  canvas.height = empty.height;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  if (!ctx || !emptyImageData) return src;

  ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
  const itemData = ctx.getImageData(0, 0, canvas.width, canvas.height);
  const output = ctx.createImageData(canvas.width, canvas.height);
  const emptyPx = emptyImageData.data;
  const itemPx = itemData.data;

  for (let i = 0; i < itemPx.length; i += 4) {
    const delta =
      Math.abs(itemPx[i] - emptyPx[i]) +
      Math.abs(itemPx[i + 1] - emptyPx[i + 1]) +
      Math.abs(itemPx[i + 2] - emptyPx[i + 2]);
    if (delta > threshold) {
      output.data[i] = itemPx[i];
      output.data[i + 1] = itemPx[i + 1];
      output.data[i + 2] = itemPx[i + 2];
      output.data[i + 3] = 255;
    }
  }

  ctx.putImageData(output, 0, 0);
  const url = canvas.toDataURL('image/png');
  maskedUrlCache.set(src, url);
  return url;
}

export function clearMaskedImageCache() {
  maskedUrlCache.clear();
  emptyImageData = null;
  emptyDimensions = null;
}
