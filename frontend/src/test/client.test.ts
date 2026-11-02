import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';
import {
  executeTokenRefresh,
  getAccessToken,
  setAccessToken,
  setOnTokenExpired,
} from '../api/client';

vi.mock('axios', async () => {
  const actual = await vi.importActual<typeof import('axios')>('axios');
  return {
    ...actual,
    default: {
      ...actual.default,
      post: vi.fn(),
      create: vi.fn().mockReturnValue({
        interceptors: {
          request: { use: vi.fn() },
          response: { use: vi.fn() },
        },
      }),
    },
  };
});

describe('Axios Client & Auto-Refresh Single-Flight', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setAccessToken(null);
  });

  it('stores access token only in memory', () => {
    expect(getAccessToken()).toBeNull();
    setAccessToken('test-access-token-123');
    expect(getAccessToken()).toBe('test-access-token-123');
    setAccessToken(null);
    expect(getAccessToken()).toBeNull();
  });

  it('coalesces concurrent token refresh requests into exactly one HTTP call', async () => {
    let resolveRefresh: (value: unknown) => void;
    const refreshPromise = new Promise((resolve) => {
      resolveRefresh = resolve;
    });

    vi.mocked(axios.post).mockReturnValueOnce(
      refreshPromise as unknown as ReturnType<typeof axios.post>
    );

    // Call executeTokenRefresh 3 times concurrently
    const p1 = executeTokenRefresh();
    const p2 = executeTokenRefresh();
    const p3 = executeTokenRefresh();

    // Verify axios.post has only been called once
    expect(axios.post).toHaveBeenCalledTimes(1);

    // Resolve the single network call
    resolveRefresh!({
      data: { access_token: 'new-rotated-token', expires_in: 900 },
    });

    const [t1, t2, t3] = await Promise.all([p1, p2, p3]);

    expect(t1).toBe('new-rotated-token');
    expect(t2).toBe('new-rotated-token');
    expect(t3).toBe('new-rotated-token');
    expect(axios.post).toHaveBeenCalledTimes(1);
    expect(getAccessToken()).toBe('new-rotated-token');
  });

  it('handles refresh failure gracefully and calls onTokenExpired without looping', async () => {
    const onExpiredSpy = vi.fn();
    setOnTokenExpired(onExpiredSpy);

    vi.mocked(axios.post).mockRejectedValueOnce(new Error('Network or 401 error'));

    const result = await executeTokenRefresh();

    expect(result).toBeNull();
    expect(getAccessToken()).toBeNull();
    expect(onExpiredSpy).toHaveBeenCalledTimes(1);
  });
});
