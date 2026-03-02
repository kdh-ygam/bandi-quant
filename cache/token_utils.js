/**
 * Token Efficiency Utilities
 * 파파의 토큰 절약 전략 구현
 */

const fs = require('fs');
const path = require('path');

const CACHE_DIR = '/Users/mchom/.openclaw/workspace/cache';
const SEARCH_CACHE = path.join(CACHE_DIR, 'search_cache.json');
const WEB_CACHE = path.join(CACHE_DIR, 'web_cache.json');

// Ensure cache dir exists
if (!fs.existsSync(CACHE_DIR)) {
  fs.mkdirSync(CACHE_DIR, { recursive: true });
}

// Initialize cache files
[SEARCH_CACHE, WEB_CACHE].forEach(f => {
  if (!fs.existsSync(f)) fs.writeFileSync(f, '{}');
});

function loadCache(file) {
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch {
    return {};
  }
}

function saveCache(file, data) {
  fs.writeFileSync(file, JSON.stringify(data, null, 0)); // compact, no spaces
}

/**
 * Get cached search result if valid
 */
function getSearchCache(query, ttlMinutes = 60) {
  const cache = loadCache(SEARCH_CACHE);
  const key = query.toLowerCase().trim();
  const entry = cache[key];
  
  if (!entry) return null;
  
  const age = Date.now() - entry.timestamp;
  const maxAge = ttlMinutes * 60 * 1000;
  
  if (age > maxAge) return null;
  
  return entry.data;
}

/**
 * Save search result to cache
 */
function setSearchCache(query, data) {
  const cache = loadCache(SEARCH_CACHE);
  cache[query.toLowerCase().trim()] = {
    timestamp: Date.now(),
    data: data
  };
  saveCache(SEARCH_CACHE, cache);
}

/**
 * Get cached web page if valid
 */
function getWebCache(url, ttlMinutes = 30) {
  const cache = loadCache(WEB_CACHE);
  const key = url.toLowerCase().trim();
  const entry = cache[key];
  
  if (!entry) return null;
  
  const age = Date.now() - entry.timestamp;
  const maxAge = ttlMinutes * 60 * 1000;
  
  if (age > maxAge) return null;
  
  return entry.data;
}

/**
 * Save web page to cache
 */
function setWebCache(url, data) {
  const cache = loadCache(WEB_CACHE);
  cache[url.toLowerCase().trim()] = {
    timestamp: Date.now(),
    data: data
  };
  saveCache(WEB_CACHE, cache);
}

module.exports = {
  getSearchCache,
  setSearchCache,
  getWebCache,
  setWebCache
};
