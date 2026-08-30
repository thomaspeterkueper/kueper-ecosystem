export type TimelineTemporal = {
  start?: string;
  end?: string;
  precision: string;
  certainty: "exact" | "approximate" | "speculative";
  display: string;
};

export type TimelinePoint = {
  id: string;
  temporal: TimelineTemporal;
};

export type TimelineViewport = {
  min: number;
  max: number;
};

export type TimelineCluster<T> = {
  x: number;
  items: T[];
};

const MIN_SPAN_YEARS = 0.25;
const MAX_SPAN_YEARS = 100_000;

/**
 * Converts supported KG timeline values into a continuous CE/BCE year coordinate.
 * Examples: -60000 -> -60000, 2087 -> 2087, 2087-04-12 -> ~2087.28.
 * The original display value remains authoritative for presentation.
 */
export function temporalToYear(temporal: TimelineTemporal): number | null {
  const raw = temporal.start?.trim();
  if (!raw) return null;

  if (/^-?\d+(?:\.\d+)?$/.test(raw)) {
    const value = Number(raw);
    return Number.isFinite(value) ? value : null;
  }

  const iso = raw.match(/^(-?\d{1,6})-(\d{2})-(\d{2})$/);
  if (iso) {
    const year = Number(iso[1]);
    const month = Number(iso[2]);
    const day = Number(iso[3]);
    if (!Number.isFinite(year) || month < 1 || month > 12 || day < 1 || day > 31) return null;
    return year + (month - 1) / 12 + (day - 1) / 365.2425;
  }

  const leadingYear = raw.match(/^(-?\d{1,6})/);
  if (leadingYear) {
    const year = Number(leadingYear[1]);
    return Number.isFinite(year) ? year : null;
  }

  return null;
}

export function extent<T extends TimelinePoint>(items: T[], fallback: TimelineViewport = { min: -10_000, max: 2100 }): TimelineViewport {
  const years = items
    .map((item) => temporalToYear(item.temporal))
    .filter((year): year is number => year !== null);

  if (years.length === 0) return fallback;

  const min = Math.min(...years);
  const max = Math.max(...years);
  if (min === max) return { min: min - 1, max: max + 1 };

  const padding = Math.max((max - min) * 0.04, 1);
  return { min: min - padding, max: max + padding };
}

export function clampViewport(viewport: TimelineViewport, bounds: TimelineViewport): TimelineViewport {
  let span = viewport.max - viewport.min;
  if (!Number.isFinite(span) || span <= 0) span = Math.max(bounds.max - bounds.min, 1);
  span = Math.min(Math.max(span, MIN_SPAN_YEARS), Math.max(MAX_SPAN_YEARS, bounds.max - bounds.min));

  let min = viewport.min;
  let max = min + span;

  if (min < bounds.min) {
    min = bounds.min;
    max = min + span;
  }
  if (max > bounds.max) {
    max = bounds.max;
    min = max - span;
  }

  if (min < bounds.min) min = bounds.min;
  if (max > bounds.max) max = bounds.max;

  return { min, max };
}

export function zoomViewport(
  viewport: TimelineViewport,
  bounds: TimelineViewport,
  factor: number,
  anchorRatio = 0.5
): TimelineViewport {
  const span = viewport.max - viewport.min;
  const nextSpan = Math.min(Math.max(span * factor, MIN_SPAN_YEARS), Math.max(bounds.max - bounds.min, MIN_SPAN_YEARS));
  const ratio = Math.min(Math.max(anchorRatio, 0), 1);
  const anchor = viewport.min + span * ratio;
  const next = {
    min: anchor - nextSpan * ratio,
    max: anchor + nextSpan * (1 - ratio),
  };
  return clampViewport(next, bounds);
}

export function panViewport(
  viewport: TimelineViewport,
  bounds: TimelineViewport,
  deltaYears: number
): TimelineViewport {
  return clampViewport(
    { min: viewport.min + deltaYears, max: viewport.max + deltaYears },
    bounds
  );
}

export function yearToRatio(year: number, viewport: TimelineViewport): number {
  const span = viewport.max - viewport.min;
  if (span <= 0) return 0.5;
  return (year - viewport.min) / span;
}

export function formatAxisYear(year: number, span: number): string {
  const abs = Math.abs(year);
  const rounded = span < 10 ? Math.round(year * 10) / 10 : Math.round(year);
  if (rounded < 0) return `${Math.abs(rounded).toLocaleString("de-DE")} BCE`;
  if (abs < 1 && rounded === 0) return "1 BCE / 1 CE";
  return `${rounded.toLocaleString("de-DE")} CE`;
}

export function buildTicks(viewport: TimelineViewport, desired = 7): number[] {
  const span = viewport.max - viewport.min;
  if (span <= 0) return [];

  const rough = span / desired;
  const magnitude = 10 ** Math.floor(Math.log10(rough));
  const normalized = rough / magnitude;
  const stepBase = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10;
  const step = stepBase * magnitude;
  const first = Math.ceil(viewport.min / step) * step;
  const ticks: number[] = [];

  for (let value = first; value <= viewport.max + step * 0.001; value += step) {
    ticks.push(Number(value.toFixed(6)));
    if (ticks.length > 100) break;
  }

  return ticks;
}

export function clusterByPixel<T extends TimelinePoint>(
  items: T[],
  viewport: TimelineViewport,
  width: number,
  thresholdPx = 22
): TimelineCluster<T>[] {
  if (width <= 0) return [];

  const positioned = items
    .map((item) => {
      const year = temporalToYear(item.temporal);
      if (year === null || year < viewport.min || year > viewport.max) return null;
      return { item, x: yearToRatio(year, viewport) * width };
    })
    .filter((entry): entry is { item: T; x: number } => entry !== null)
    .sort((a, b) => a.x - b.x);

  const clusters: TimelineCluster<T>[] = [];
  for (const entry of positioned) {
    const current = clusters[clusters.length - 1];
    if (!current || entry.x - current.x > thresholdPx) {
      clusters.push({ x: entry.x, items: [entry.item] });
      continue;
    }

    const count = current.items.length;
    current.x = (current.x * count + entry.x) / (count + 1);
    current.items.push(entry.item);
  }

  return clusters;
}
