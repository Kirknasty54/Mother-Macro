// src/components/Login.jsx
import React, { useRef, useState, useLayoutEffect, useCallback } from "react";
import { useNavigate, Link } from "react-router-dom";
import { gsap } from "gsap";
import { authApi } from "../api/client.js"; // ⬅️ add
import motherMacroImage from '../assets/mother_macro_logo.png';
import LogoutButton from "./LogoutButton.jsx";

const Login = () => {
    const navigate = useNavigate();
    const containerRef = useRef(null);
    const cardRef = useRef(null);

    // swap username → email to match backend
    const [formData, setFormData] = useState({ email: "", password: "" });
    const [msg, setMsg] = useState("");

    // ── Entrance sequence (includes h2 reveal)
    useLayoutEffect(() => {
        const ctx = gsap.context(() => {
            const tl = gsap.timeline({ defaults: { ease: "power2.out" } });
            tl.from(".mm-header h2", { opacity: 0, scale: 0.85, duration: 0.7, ease: "back.out(1.6)" })
                .from(".mm-header p", { opacity: 0, y: 15, duration: 0.5 }, "-=0.3")
                .from(cardRef.current, { opacity: 0, y: 24, duration: 0.5 }, "-=0.2")
                .from(".mm-field", { opacity: 0, y: 12, duration: 0.35, stagger: 0.08 }, "-=0.25")
                .from(".mm-submit", { opacity: 0, y: 10, duration: 0.3 }, "-=0.2");
        }, containerRef);
        return () => ctx.revert();
    }, []);

    // ── Floating idle motion for h2
    useLayoutEffect(() => {
        const ctx = gsap.context(() => {
            gsap.to(".mm-header h2", { y: -5, duration: 2.6, ease: "sine.inOut", repeat: -1, yoyo: true });
        }, containerRef);
        return () => ctx.revert();
    }, []);

    // ── ✨ Shimmer / sparkle light sweep across text
    useLayoutEffect(() => {
        const ctx = gsap.context(() => {
            const h2 = document.querySelector(".mm-header h2");
            if (!h2) return;
            h2.style.backgroundImage =
                "linear-gradient(120deg, var(--color-sage-100) 0%, var(--color-beige-50) 50%, var(--color-sage-300) 100%)";
            h2.style.backgroundSize = "200% 100%";
            h2.style.backgroundClip = "text";
            h2.style.webkitBackgroundClip = "text";
            h2.style.color = "transparent";
            gsap.to(h2, { backgroundPosition: "200% center", duration: 5, ease: "power1.inOut", repeat: -1, yoyo: true });
        }, containerRef);
        return () => ctx.revert();
    }, []);

    // ── Animated gradient drift
    useLayoutEffect(() => {
        const ctx = gsap.context(() => {
            gsap.to(containerRef.current, { backgroundPosition: "100% 100%", duration: 5, ease: "linear", repeat: -1, yoyo: true });
        }, containerRef);
        return () => ctx.revert();
    }, []);

    // ── Card hover lift
    useLayoutEffect(() => {
        const node = cardRef.current;
        if (!node) return;
        gsap.set(node, { transformOrigin: "center center" });
        const onEnter = () => gsap.to(node, { scale: 1.03, y: -5, duration: 0.3 });
        const onLeave = () => gsap.to(node, { scale: 1, y: 0, duration: 0.3 });
        node.addEventListener("mouseenter", onEnter);
        node.addEventListener("mouseleave", onLeave);
        return () => {
            node.removeEventListener("mouseenter", onEnter);
            node.removeEventListener("mouseleave", onLeave);
        };
    }, []);

    // ── Form logic
    const handleChange = (e) => setFormData((p) => ({ ...p, [e.target.name]: e.target.value }));

    const handleFocus = useCallback((e) => gsap.to(e.target, { boxShadow: "0 0 10px 2px rgba(134,151,95,0.45)", duration: 0.2 }), []);
    const handleBlur = useCallback((e) => gsap.to(e.target, { boxShadow: "none", duration: 0.2 }), []);
    const shakeCard = () =>
        gsap.fromTo(cardRef.current, { x: -8 }, { x: 8, duration: 0.06, yoyo: true, repeat: 7, clearProps: "x" });

    const handleSubmit = async (e) => {
        e.preventDefault();
        const { email, password } = formData;
        if (!email || !password) return shakeCard();
        setMsg("Signing in…");
        try {
            const res = await authApi.login(email.trim().toLowerCase(), password);
            // store tokens/user
            localStorage.setItem("access_token", res.access_token || "");
            localStorage.setItem("refresh_token", res.refresh_token || "");
            localStorage.setItem("user", JSON.stringify(res.user || {}));
            // animate -> navigate
            gsap.to(containerRef.current, {
                opacity: 0, y: -12, filter: "blur(6px)", duration: 0.4, ease: "power2.inOut",
                onComplete: () => navigate("/preferences"),
            });
        } catch (err) {
            setMsg(err.message);
            shakeCard();
        }
    };

    return (
        <div className="relative w-full h-full">
            {/* Sage/Beige blurred glows */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-[-25%] left-[-15%] w-[620px] h-[620px] bg-gradient-to-tr from-sage-200 to-sage-500 opacity-50 blur-[220px]" />
                <div className="absolute bottom-[-28%] right-[-18%] w-[760px] h-[760px] bg-gradient-to-br from-beige-200 to-sage-400 opacity-45 blur-[260px]" />
            </div>

            {/* Animated gradient background */}
            <div ref={containerRef} className="min-h-screen bg-[length:260%_260%] bg-gradient-to-br from-sage-300 via-sage-500 to-beige-300 flex items-center justify-center px-4 relative">
                <div className="max-w-md w-full space-y-8">
                    {/* Header with shimmer */}
                    <div className="text-center mm-header">
                        <img src={motherMacroImage}  className={"rounded-lg mx-auto w-1/2 max-w-[200px]"} alt="logo"/>
                        <h2 className="mt-6 text-4xl font-bold text-sage-50 drop-shadow-[0_0_12px_rgba(134,151,95,0.4)]">Mother Macro</h2>
                        <p className="mt-2 text-lg text-sage-900 leading-relaxed font-extrabold">
                            Create personalized meal plans that will help you meet your macro goals and taste like they were cooked by your mother.
                        </p>
                    </div>

                    {/* Login Form */}
                    <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
                        <div ref={cardRef} className="bg-beige-50/95 backdrop-blur-md rounded-xl shadow-xl p-8 space-y-6 border border-sage-200">
                            <div className="mm-field">
                                <label htmlFor="email" className="block text-sm font-medium text-sage-700 mb-2">Email</label>
                                <input
                                    id="email" name="email" type="email" required value={formData.email}
                                    onChange={handleChange} onFocus={handleFocus} onBlur={handleBlur}
                                    className="w-full px-4 py-3 border border-sage-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500 transition-colors"
                                    placeholder="you@example.com"
                                />
                            </div>

                            <div className="mm-field">
                                <label htmlFor="password" className="block text-sm font-medium text-sage-700 mb-2">Password</label>
                                <input
                                    id="password" name="password" type="password" required value={formData.password}
                                    onChange={handleChange} onFocus={handleFocus} onBlur={handleBlur}
                                    className="w-full px-4 py-3 border border-sage-300 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500 transition-colors"
                                    placeholder="••••••••"
                                />
                            </div>

                            <button type="submit" className="mm-submit w-full bg-sage-600 hover:bg-sage-700 text-beige-50 font-medium py-3 px-4 rounded-lg transition-colors focus:ring-2 focus:ring-sage-500 focus:ring-offset-2">
                                Sign In
                            </button>
                            {msg && <p className="text-sm text-sage-800 mt-1">{msg}</p>}
                        </div>
                    </form>

                    {/* Footer */}
                    <div className="text-center">
                        <p className="text-m text-sage-700/90 font-extrabold">
                            Don't have an account?{" "}
                            <Link to="/register" className="font-medium text-sage-600 hover:text-sage-500 transition-colors">Sign up here</Link>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Login;
