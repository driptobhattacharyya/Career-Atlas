import { describe, it, expect } from 'vitest';
import { getRouter } from './router';

describe('getRouter', () => {
  it('should create and return a router instance', () => {
    const router = getRouter();

    // Check if the returned object has standard Router properties/methods
    expect(router).toBeDefined();
    expect(router).toHaveProperty('routeTree');
    expect(router).toHaveProperty('options');
    expect(router).toHaveProperty('navigate');
    expect(router).toHaveProperty('buildLocation');

    // Check if error component is configured
    expect(router.options.defaultErrorComponent).toBeDefined();

    // Check some default options
    expect(router.options.scrollRestoration).toBe(true);
    expect(router.options.defaultPreloadStaleTime).toBe(0);
  });
});
