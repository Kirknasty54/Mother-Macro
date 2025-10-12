import axios from "axios";

const axiosClient = axios.create({
    baseURL: import.meta.env.VITE_API_BASE || "http://127.0.0.1:5000",
    headers: { "Content-Type": "application/json" },
});

axiosClient.interceptors.request.use((config) => {
    const t = localStorage.getItem("access_token");
    if (t) config.headers.Authorization = `Bearer ${t}`;
    return config;
});

axiosClient.interceptors.response.use(
    (res) => res.data, // unwrap
    (err) => Promise.reject(new Error(err?.response?.data?.msg || err.message || "Network error"))
);

export default axiosClient;
