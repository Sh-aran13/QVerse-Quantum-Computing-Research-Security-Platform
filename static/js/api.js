/**
 * QVerse Core API Client
 */

export function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

export async function apiFetch(url, options = {}) {
    const defaultHeaders = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    };

    const csrfToken = getCookie('csrftoken');
    if (csrfToken && !['GET', 'HEAD', 'OPTIONS'].includes(options.method?.toUpperCase())) {
        defaultHeaders['X-CSRFToken'] = csrfToken;
    }

    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers,
        },
    };

    try {
        const response = await fetch(url, config);
        const data = await response.json();

        if (!response.ok) {
            throw {
                status: response.status,
                error: data.error || { message: 'API request failed' },
            };
        }
        return data;
    } catch (err) {
        console.error('API Error:', err);
        throw err;
    }
}
