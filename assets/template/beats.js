// Timing for a film without narration (seconds). Hold each text long enough to read it:
// readTime(str) = max(2.5, 1 + words / 3) seconds from when it is fully on screen to the next change.
const BEATS = {
  title: 0.6,
  card: 4.2,
  items: [5.0, 6.6, 8.2],
  end: 12.5,
};
const DURATION = 17;
if (typeof window !== 'undefined') { window.BEATS = BEATS; window.DURATION = DURATION; }
if (typeof module !== 'undefined') module.exports = { BEATS, DURATION };
