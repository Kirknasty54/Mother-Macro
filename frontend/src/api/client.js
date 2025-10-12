import axiosClient from "./axiosClient";

export const authApi = {
    register: (email, username, password) =>
        axiosClient.post("/auth/register", { email, username, password }),
    login: (email, password) =>
        axiosClient.post("/auth/login", { email, password }),
    me: () => axiosClient.get("/me"),
};

export const prefsApi = {
    get: () => axiosClient.get("/preferences"),
    save: (p) => axiosClient.put("/preferences", p),
    generate: () => axiosClient.post("/mealplans/generate"),
};
