import React, { useRef, useState, useLayoutEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { gsap } from "gsap";
import { prefsApi } from "../api/client.js";
import Avatar  from './Avatar.jsx';

const CaloriePreferences = () => {
    const rootRef = useRef(null);
    const cardRef = useRef(null);
    const navigate = useNavigate();
    const [saving, setSaving] = useState("");
    const [generating, setGenerating] = useState("");

    const [preferences, setPreferences] = useState({
        dailyCalorieGoal: "",
        activityLevel: "moderate",
        dietType: "balanced",
        allergens: [],
        healthGoals: [],
    });

    const activityLevels = [
        { value: "sedentary", label: "Sedentary (little to no exercise)" },
        { value: "light", label: "Light (light exercise 1-3 d/wk)" },
        { value: "moderate", label: "Moderate (3-5 d/wk)" },
        { value: "active", label: "Active (6-7 d/wk)" },
        { value: "very-active", label: "Very Active (physical job)" },
    ];

    const dietTypes = [
        { value: "balanced", label: "Balanced Diet" },
        { value: "low-carb", label: "Low Carb" },
        { value: "vegetarian", label: "Vegetarian" },
        { value: "vegan", label: "Vegan" },
        { value: "keto", label: "Ketogenic" },
        { value: "mediterranean", label: "Mediterranean" },
    ];

    const commonAllergens = ["Nuts", "Dairy", "Gluten", "Eggs", "Soy", "Shellfish", "Fish"];
    const healthGoalOptions = ["Weight Loss", "Weight Gain", "Muscle Building", "Heart Health", "Diabetes Management", "General Wellness"];

    const handleChange = (e) => {
        const { name, value } = e.target;
        setPreferences((prev) => ({ ...prev, [name]: value }));
    };
    const handleCheckboxChange = (category, value) => {
        setPreferences((prev) => ({
            ...prev,
            [category]: prev[category].includes(value)
                ? prev[category].filter((x) => x !== value)
                : [...prev[category], value],
        }));
    };

    // load existing server prefs on mount
    React.useEffect(() => {
        (async () => {
            try {
                const r = await prefsApi.get();
                if (r?.preferences) {
                    const srv = r.preferences;
                    setPreferences((prev) => ({
                        ...prev,
                        dailyCalorieGoal: srv.calorie_target ?? "",
                        dietType: srv.diet ?? "balanced",
                        allergens: Array.isArray(srv.exclude_ingredients) ? srv.exclude_ingredients : [],
                    }));
                }
            } catch {
                /* ignore */
            }
        })();
    }, []);

    // Build payload in the exact shape the backend expects
    const buildPayload = () => ({
        calorie_target: Number(preferences.dailyCalorieGoal) || undefined,
        diet: preferences.dietType || "balanced",
        exclude_ingredients: preferences.allergens,
        // Add more later if/when your UI collects them:
        // protein_g_target, carb_g_target, fat_g_target, meals_per_day, max_prep_minutes, etc.
    });

    const saveToServer = async () => {
        setSaving("Saving…");
        try {
            const payload = buildPayload();
            console.log("[CaloriePreferences] save payload →", payload);
            await prefsApi.save(payload);
            setSaving("Saved.");
            gsap.to(cardRef.current, { scale: 1.01, duration: 0.15, yoyo: true, repeat: 1 });
        } catch (e) {
            setSaving(e.message || "Save failed");
            gsap.fromTo(cardRef.current, { x: -8 }, { x: 8, duration: 0.06, repeat: 7, yoyo: true, clearProps: "x" });
            throw e;
        }
    };

    // NEW: hop to the loading route; it will call /mealplans/generate and then push to /mealplan
    const generatePlan = async () => {
        setGenerating("Generating…");
        try {
            await saveToServer(); // ensure latest prefs are stored
            setGenerating(""); // clear text before navigating
            navigate("/generating", { state: { from: "prefs" } });
        } catch (e) {
            setGenerating(e.message || "Failed to start generation");
            gsap.fromTo(cardRef.current, { x: -8 }, { x: 8, duration: 0.06, repeat: 7, yoyo: true, clearProps: "x" });
        }
    };

    // === GSAP effects from your original ===
    const prefersReduced =
        typeof window !== "undefined" &&
        window.matchMedia &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    useLayoutEffect(() => {
        if (prefersReduced) return;
        const ctx = gsap.context(() => {
            const tl = gsap.timeline({ defaults: { ease: "power2.out" } });
            tl.from(".cp-header h1", { opacity: 0, scale: 0.9, duration: 0.6, ease: "back.out(1.6)" })
                .from(".cp-header p", { opacity: 0, y: 14, duration: 0.45 }, "-=0.25")
                .from(cardRef.current, { opacity: 0, y: 26, duration: 0.5 }, "-=0.1")
                .from(".cp-field", { opacity: 0, y: 12, duration: 0.35, stagger: 0.07 }, "-=0.15")
                .from(".cp-submit", { opacity: 0, y: 10, duration: 0.3 }, "-=0.2");
        }, rootRef);
        return () => ctx.revert();
    }, [prefersReduced]);

    useLayoutEffect(() => {
        if (prefersReduced) return;
        const ctx = gsap.context(() => {
            gsap.to(".cp-header p", { y: -3, duration: 3, ease: "sine.inOut", repeat: -1, yoyo: true });
        }, rootRef);
        return () => ctx.revert();
    }, [prefersReduced]);

    useLayoutEffect(() => {
        if (prefersReduced) return;
        const ctx = gsap.context(() => {
            const p = document.querySelector(".cp-header p");
            if (!p) return;
            p.style.backgroundImage =
                "linear-gradient(120deg, var(--color-beige-100) 0%, var(--color-sage-50) 50%, var(--color-beige-200) 100%)";
            p.style.backgroundSize = "200% 100%";
            p.style.backgroundClip = "text";
            p.style.webkitBackgroundClip = "text";
            p.style.color = "transparent";
            gsap.to(p, { backgroundPosition: "200% center", duration: 8, ease: "power1.inOut", repeat: -1, yoyo: true });
        }, rootRef);
        return () => ctx.revert();
    }, [prefersReduced]);

    useLayoutEffect(() => {
        if (prefersReduced) return;
        const node = rootRef.current?.querySelector(".cp-submit");
        if (!node) return;
        const onEnter = () => gsap.to(node, { y: -2, scale: 1.02, duration: 0.2, ease: "power2.out" });
        const onLeave = () => gsap.to(node, { y: 0, scale: 1, duration: 0.2, ease: "power2.out" });
        node.addEventListener("mouseenter", onEnter);
        node.addEventListener("mouseleave", onLeave);
        return () => {
            node.removeEventListener("mouseenter", onEnter);
            node.removeEventListener("mouseleave", onLeave);
        };
    }, [prefersReduced]);

    useLayoutEffect(() => {
        if (prefersReduced) return;
        const ctx = gsap.context(() => {
            if (!rootRef.current) return;
            gsap.to(rootRef.current, { backgroundPosition: "100% 100%", duration: 5, ease: "linear", repeat: -1, yoyo: true });
        }, rootRef);
        return () => ctx.revert();
    }, [prefersReduced]);

    const focusGlow = useCallback((e) => {
        if (prefersReduced) return;
        gsap.to(e.target, { boxShadow: "0 0 10px 2px rgba(134,151,95,0.45)", duration: 0.2 });
    }, [prefersReduced]);
    const blurGlow = useCallback((e) => {
        if (prefersReduced) return;
        gsap.to(e.target, { boxShadow: "none", duration: 0.2 });
    }, [prefersReduced]);

    return (
        <div className="relative min-h-screen">
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-[-25%] left-[-15%] w-[620px] h[620px] bg-gradient-to-tr from-sage-200 to-sage-500 opacity-50 blur-[220px]" />
                <div className="absolute bottom-[-28%] right-[-18%] w-[760px] h-[760px] bg-gradient-to-br from-beige-200 to-sage-400 opacity-45 blur-[260px]" />
            </div>

            <div ref={rootRef} className="bg-[length:260%_260%] bg-gradient-to-br from-sage-300 via-sage-500 to-beige-300 py-8">
                <div className="relative max-w-4xl mx-auto px-4">
                    <div className="absolute top-2 right-2"><Avatar /></div>
                    <div className="text-center mb-8 cp-header">
                        <h1 className="text-4xl font-bold text-sage-50 drop-shadow-[0_0_12px_rgba(134,151,95,0.4)] mb-2">
                            Set Your Health Preferences
                        </h1>
                        <p className="text-lg text-sage-700 leading-relaxed">
                            Tell us about your goals so we can personalize your nutrition journey
                        </p>
                    </div>

                    <form className="bg-white/95 backdrop-blur-md rounded-xl shadow-xl p-8 space-y-8 border border-sage-200" ref={cardRef}>
                        <div className="cp-field">
                            <label className="block text-lg font-semibold text-sage-700 mb-3">Daily Calorie Goal</label>
                            <input
                                type="number" name="dailyCalorieGoal" value={preferences.dailyCalorieGoal}
                                onChange={handleChange} onFocus={focusGlow} onBlur={blurGlow}
                                className="w-full px-4 py-3 border border-sage-200 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500 transition-colors"
                                placeholder="e.g., 2000" required
                            />
                            <p className="text-sm text-sage-600 mt-2">Enter your target daily calories (typically 1,500–3,000)</p>
                        </div>

                        <div className="cp-field">
                            <label className="block text-lg font-semibold text-sage-700 mb-3">Activity Level</label>
                            <div className="space-y-3">
                                {activityLevels.map((level) => (
                                    <label key={level.value} className="flex items-center">
                                        <input
                                            type="radio" name="activityLevel" value={level.value} checked={preferences.activityLevel === level.value}
                                            onChange={handleChange} className="mr-3 h-4 w-4 text-sage-600 focus:ring-sage-500 border-sage-300"
                                            onFocus={focusGlow} onBlur={blurGlow}
                                        />
                                        <span className="text-sage-700">{level.label}</span>
                                    </label>
                                ))}
                            </div>
                        </div>

                        <div className="cp-field">
                            <label className="block text-lg font-semibold text-sage-700 mb-3">Preferred Diet Type</label>
                            <select
                                name="dietType" value={preferences.dietType} onChange={handleChange}
                                onFocus={focusGlow} onBlur={blurGlow}
                                className="w-full px-4 py-3 border border-sage-200 rounded-lg focus:ring-2 focus:ring-sage-500 focus:border-sage-500 transition-colors"
                            >
                                {dietTypes.map((diet) => (
                                    <option key={diet.value} value={diet.value}>{diet.label}</option>
                                ))}
                            </select>
                        </div>

                        <div className="cp-field">
                            <label className="block text-lg font-semibold text-sage-700 mb-3">Food Allergies & Restrictions</label>
                            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                                {commonAllergens.map((a) => (
                                    <label key={a} className="flex items-center">
                                        <input
                                            type="checkbox" checked={preferences.allergens.includes(a)}
                                            onChange={() => handleCheckboxChange("allergens", a)}
                                            className="mr-2 h-4 w-4 text-sage-600 focus:ring-sage-500 border-sage-300 rounded"
                                            onFocus={focusGlow} onBlur={blurGlow}
                                        />
                                        <span className="text-sage-700">{a}</span>
                                    </label>
                                ))}
                            </div>
                        </div>

                        <div className="cp-field">
                            <label className="block text-lg font-semibold text-sage-700 mb-3">Health Goals</label>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                {healthGoalOptions.map((g) => (
                                    <label key={g} className="flex items-center">
                                        <input
                                            type="checkbox" checked={preferences.healthGoals.includes(g)}
                                            onChange={() => handleCheckboxChange("healthGoals", g)}
                                            className="mr-2 h-4 w-4 text-sage-600 focus:ring-sage-500 border-sage-300 rounded"
                                            onFocus={focusGlow} onBlur={blurGlow}
                                        />
                                        <span className="text-sage-700">{g}</span>
                                    </label>
                                ))}
                            </div>
                        </div>

                        <div className="flex flex-col sm:flex-row gap-3 pt-2">
                            <button
                                type="button"
                                onClick={saveToServer}
                                className="cp-submit flex-1 bg-sage-600 hover:bg-sage-700 text-white font-medium py-3 px-6 rounded-lg transition-colors focus:ring-2 focus:ring-sage-500 focus:ring-offset-2"
                                disabled={!!generating}
                            >
                                Save Preferences
                            </button>
                            <button
                                type="button"
                                onClick={generatePlan}
                                className="flex-1 bg-sage-700 hover:bg-sage-800 text-white font-medium py-3 px-6 rounded-lg transition-colors focus:ring-2 focus:ring-sage-600 focus:ring-offset-2"
                                disabled={!!generating}
                            >
                                Generate Meal Plan
                            </button>
                        </div>
                        {(saving || generating) && (
                            <p className="text-sm text-sage-800">{saving || generating}</p>
                        )}
                    </form>

                    <div className="mt-8 text-center">
                        <p className="text-sm text-sage-700/90">You can update these preferences anytime in your profile settings</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CaloriePreferences;
