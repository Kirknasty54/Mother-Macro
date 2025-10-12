import React, { createContext, useContext, useEffect, useState } from "react";
import { authApi } from "../api/client";

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);

    useEffect(() => {
        const u = localStorage.getItem("user");
        if (u) setUser(JSON.parse(u));
    }, []);

    const login = async (email, password) => {
        const res = await authApi.login(email, password);
        localStorage.setItem("access_token", res.access_token || "");
        localStorage.setItem("refresh_token", res.refresh_token || "");
        localStorage.setItem("user", JSON.stringify(res.user));
        setUser(res.user);
        return res.user;
    };

    const register = async (email, username, password) => {
        const res = await authApi.register(email, username, password);
        localStorage.setItem("access_token", res.access_token || "");
        localStorage.setItem("refresh_token", res.refresh_token || "");
        localStorage.setItem("user", JSON.stringify(res.user));
        setUser(res.user);
        return res.user;
    };

    const logout = () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("user");
        setUser(null);
    };

    return <AuthCtx.Provider value={{ user, login, register, logout }}>{children}</AuthCtx.Provider>;
}

export const useAuth = () => useContext(AuthCtx);
