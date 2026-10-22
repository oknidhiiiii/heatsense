/**
 * Client-side Least-Recently-Used (LRU) Memory Cache for Heatmap Raster Textures.
 * Caches rendered Data URLs and canvas dimensions across timeline scrub and layer toggles.
 */

export interface CachedHeatmap {
  dataUrl: string;
  width: number;
  height: number;
  timestamp: number;
}

export class HeatmapLruCache {
  private capacity: number;
  private cache: Map<string, CachedHeatmap>;

  constructor(capacity = 36) {
    this.capacity = capacity;
    this.cache = new Map();
  }

  /**
   * Build deterministic cache key from render parameters.
   */
  public static makeKey(
    regionId: string,
    layer: string,
    validAt: string,
    lodSize: number,
    theme: string
  ): string {
    return `${regionId}:${layer}:${validAt}:${lodSize}:${theme}`;
  }

  public get(key: string): CachedHeatmap | undefined {
    const item = this.cache.get(key);
    if (!item) return undefined;

    // Refresh position to mark as recently used
    this.cache.delete(key);
    this.cache.set(key, item);
    return item;
  }

  public set(key: string, value: CachedHeatmap): void {
    if (this.cache.has(key)) {
      this.cache.delete(key);
    } else if (this.cache.size >= this.capacity) {
      // Evict oldest entry (first key in insertion order)
      const oldestKey = this.cache.keys().next().value;
      if (oldestKey !== undefined) {
        this.cache.delete(oldestKey);
      }
    }
    this.cache.set(key, value);
  }

  public has(key: string): boolean {
    return this.cache.has(key);
  }

  public clear(): void {
    this.cache.clear();
  }

  public size(): number {
    return this.cache.size;
  }
}

export const heatmapLruCache = new HeatmapLruCache(40);
