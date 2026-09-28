const AOI_BBOX = { minLon: 68.0, minLat: 6.0, maxLon: 97.5, maxLat: 37.5 };

function hashString(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash |= 0; 
  }
  return Math.abs(hash);
}

export function dummyCoordsFor(sourceId) {
  const h = hashString(sourceId);
  const fracLat = ((h * 2654435761) % 1000) / 1000;
  const fracLon = ((h * 40503) % 1000) / 1000;

  const lat = AOI_BBOX.minLat + fracLat * (AOI_BBOX.maxLat - AOI_BBOX.minLat);
  const lon = AOI_BBOX.minLon + fracLon * (AOI_BBOX.maxLon - AOI_BBOX.minLon);
  return { lat, lon };
}

export const AOI_CENTER = [
  (AOI_BBOX.minLat + AOI_BBOX.maxLat) / 2,
  (AOI_BBOX.minLon + AOI_BBOX.maxLon) / 2,
];
