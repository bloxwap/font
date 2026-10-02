/**
 * Quick NumberFlow roll for values a person or a loop drives continuously (sliders, the hero readout):
 * shorter than NumberFlow's 900 ms default so the digits keep up, on the site's --ease-spring curve.
 */
export const QUICK_ROLL = { duration: 320, easing: 'cubic-bezier(0.22, 1, 0.36, 1)' } as const;
