import axiosClient from "./axiosClient";

export const authApi = {
    login: (email, password) => axiosClient.post("/auth/login", { email, password }),
    register: (email, username, password) => axiosClient.post("/auth/register", { email, username, password }),
    me: () => axiosClient.get("/me"),
};

export const prefsApi = {
    get: () => axiosClient.get("/preferences"),
    save: (p) => axiosClient.put("/preferences", p),
    generate: () => axiosClient.post("/mealplans/generate"),
};

export const chatApi = {
    send: (messages, mealplan = null) =>
        axiosClient.post("/chat", { messages, mealplan }),
};
