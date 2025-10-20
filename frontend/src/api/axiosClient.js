import axios from "axios";

const axiosClient = axios.create({
    baseURL: import.meta.env.VITE_API_BASE || "http://127.0.0.1:5000",
    headers: { "Content-Type": "application/json" },
});

// Add access token to all requests
axiosClient.interceptors.request.use((config) => {
    const t = localStorage.getItem("access_token");
    if (t) config.headers.Authorization = `Bearer ${t}`;
    return config;
});

// Handle token refresh on 401 errors
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
    failedQueue.forEach(prom => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token);
        }
    });
    failedQueue = [];
};

axiosClient.interceptors.response.use(
    (res) => res.data, // unwrap successful responses
    async (err) => {
        const originalRequest = err.config;

        // If error is 401 and we haven't tried refreshing yet
        if (err.response?.status === 401 && !originalRequest._retry) {
            if (isRefreshing) {
                // If already refreshing, queue this request
                return new Promise((resolve, reject) => {
                    failedQueue.push({ resolve, reject });
                }).then(token => {
                    originalRequest.headers.Authorization = `Bearer ${token}`;
                    return axiosClient(originalRequest);
                }).catch(err => Promise.reject(err));
            }

            originalRequest._retry = true;
            isRefreshing = true;

            const refreshToken = localStorage.getItem("refresh_token");
            if (!refreshToken) {
                // No refresh token, clear everything and force reload to reset state
                localStorage.removeItem("access_token");
                localStorage.removeItem("refresh_token");
                localStorage.removeItem("user");
                window.location.replace("/login");
                return Promise.reject(new Error("Session expired. Please login again."));
            }

            try {
                // Call refresh endpoint
                const response = await axios.post(
                    `${axiosClient.defaults.baseURL}/auth/refresh`,
                    { refresh_token: refreshToken },
                    { headers: { "Content-Type": "application/json" } }
                );

                const { access_token, refresh_token } = response.data;

                // Update tokens in localStorage
                localStorage.setItem("access_token", access_token);
                if (refresh_token) {
                    localStorage.setItem("refresh_token", refresh_token);
                }

                // Update the authorization header
                originalRequest.headers.Authorization = `Bearer ${access_token}`;

                // Process any queued requests
                processQueue(null, access_token);
                isRefreshing = false;

                // Retry the original request
                return axiosClient(originalRequest);
            } catch (refreshError) {
                // Refresh failed, clear everything and force reload to reset state
                processQueue(refreshError, null);
                isRefreshing = false;

                localStorage.removeItem("access_token");
                localStorage.removeItem("refresh_token");
                localStorage.removeItem("user");
                window.location.replace("/login");

                return Promise.reject(new Error("Session expired. Please login again."));
            }
        }

        // For other errors, just reject with a formatted message
        return Promise.reject(new Error(err?.response?.data?.msg || err.message || "Network error"));
    }
);

export default axiosClient;
