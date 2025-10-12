import React, { useEffect, useMemo } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import ChatWidget from "./ChatWidget";

export default function MealPlan() {
    const { state } = useLocation();
    const navigate = useNavigate();
    const mealplan = state?.mealplan;

    useEffect(() => {
        if (!mealplan) navigate("/preferences", { replace: true });
    }, [mealplan, navigate]);

    const totals = useMemo(() => {
        if (!mealplan?.days?.length) return null;
        let c = 0, p = 0, cb = 0, f = 0;
        for (const d of mealplan.days) {
            for (const m of (d.meals || [])) {
                c += Number(m.calories || 0);
                p += Number(m.protein_g || 0);
                cb += Number(m.carbs_g || 0);
                f += Number(m.fat_g || 0);
            }
        }
        return { calories: c, protein_g: p, carbs_g: cb, fat_g: f };
    }, [mealplan]);

    if (!mealplan) return null;

    return (
        <div className="min-h-screen bg-gradient-to-br from-sage-100 via-beige-50 to-white">
            <div className="max-w-5xl mx-auto p-6">
                <div className="flex items-center justify-between gap-3">
                    <div>
                        <h1 className="text-3xl font-bold text-sage-800">Your 7-Day Meal Plan</h1>
                        <p className="text-sage-700 mt-1">Generated based on your preferences</p>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            className="bg-white border border-sage-300 hover:bg-sage-50 text-sage-800 px-4 py-2 rounded-lg"
                            onClick={() => {
                                const blob = new Blob([JSON.stringify(mealplan, null, 2)], { type: "application/json" });
                                const url = URL.createObjectURL(blob);
                                const a = document.createElement("a");
                                a.href = url; a.download = "mealplan.json"; a.click();
                                URL.revokeObjectURL(url);
                            }}
                        >
                            Download JSON
                        </button>
                        <button
                            className="bg-sage-600 hover:bg-sage-700 text-white px-4 py-2 rounded-lg"
                            onClick={() => navigate("/preferences")}
                        >
                            Edit Preferences
                        </button>
                    </div>
                </div>

                {totals && (
                    <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
                        <div className="bg-white/90 backdrop-blur-sm border border-sage-200 rounded-lg p-3">
                            <div className="text-sm text-sage-600">Total Calories</div>
                            <div className="text-xl font-semibold text-sage-800">{Math.round(totals.calories)} kcal</div>
                        </div>
                        <div className="bg-white/90 backdrop-blur-sm border border-sage-200 rounded-lg p-3">
                            <div className="text-sm text-sage-600">Protein</div>
                            <div className="text-xl font-semibold text-sage-800">{Math.round(totals.protein_g)} g</div>
                        </div>
                        <div className="bg-white/90 backdrop-blur-sm border border-sage-200 rounded-lg p-3">
                            <div className="text-sm text-sage-600">Carbs</div>
                            <div className="text-xl font-semibold text-sage-800">{Math.round(totals.carbs_g)} g</div>
                        </div>
                        <div className="bg-white/90 backdrop-blur-sm border border-sage-200 rounded-lg p-3">
                            <div className="text-sm text-sage-600">Fat</div>
                            <div className="text-xl font-semibold text-sage-800">{Math.round(totals.fat_g)} g</div>
                        </div>
                    </div>
                )}

                <div className="mt-6 grid gap-6 md:grid-cols-2">
                    {(mealplan.days || []).map((d, i) => (
                        <div key={i} className="bg-white/90 backdrop-blur-sm rounded-xl shadow border border-sage-200 p-5">
                            <h2 className="text-xl font-semibold text-sage-700 mb-3">Day {d.day ?? i + 1}</h2>
                            <div className="space-y-3">
                                {(d.meals || []).map((m, j) => (
                                    <div key={j} className="border border-sage-100 rounded-lg p-3">
                                        <div className="flex items-center justify-between">
                                            <h3 className="font-medium text-sage-800">{m.name}</h3>
                                            <span className="text-sm text-sage-700">
                        {m.calories ?? "—"} kcal · {m.protein_g ?? "—"}P / {m.carbs_g ?? "—"}C / {m.fat_g ?? "—"}F
                      </span>
                                        </div>
                                        {m.recipe_text && <p className="text-sm text-sage-700 mt-2 whitespace-pre-wrap">{m.recipe_text}</p>}
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>

                {!mealplan.days?.length && (
                    <p className="mt-6 text-sage-700">No meals returned. Try updating your preferences and generate again.</p>
                )}
            </div>
            <ChatWidget mealplan={mealplan} />
        </div>
    );
}
