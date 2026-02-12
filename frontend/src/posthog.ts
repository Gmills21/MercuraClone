import posthog from 'posthog-js';

// Initialize PostHog
const posthogApiKey = import.meta.env.VITE_POSTHOG_KEY;
const posthogHost = import.meta.env.VITE_POSTHOG_HOST || 'https://app.posthog.com';

if (posthogApiKey) {
    posthog.init(posthogApiKey, {
        api_host: posthogHost,
        autocapture: true,
        capture_pageview: true,
        persistence: 'localStorage',
    });
} else {
    console.warn('PostHog API key missing. Frontend tracking disabled.');
}

export const trackEvent = (eventName: string, properties?: Record<string, any>) => {
    if (posthogApiKey) {
        posthog.capture(eventName, properties);
    }
};

export const identifyUser = (distinctId: string, properties?: Record<string, any>) => {
    if (posthogApiKey) {
        posthog.identify(distinctId, properties);
    }
};

export const setGroup = (groupType: string, groupKey: string, properties?: Record<string, any>) => {
    if (posthogApiKey) {
        posthog.group(groupType, groupKey, properties);
    }
};

export default posthog;
