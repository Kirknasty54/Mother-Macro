import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { prefsApi } from "../api/client"; // or wherever your api client lives

export default function Generating() {
    const navigate = useNavigate();
    const location = useLocation();
    const [error, setError] = useState(null);

    useEffect(() => {
        let stopped = false;

        (async () => {
            try {
                setError(null);
                // optionally: if you passed anything in location.state from preferences
                // you could use it here; we just kick off generation
                const res = await prefsApi.generate();
                if (!stopped) {
                    navigate("/mealplan", { state: { mealplan: res.mealplan } });
                }
            } catch (e) {
                if (!stopped) setError(e?.message || "Failed to generate meal plan.");
            }
        })();

        return () => { stopped = true; };
    }, [navigate]);

    return (
        <div className="min-h-screen w-full flex items-center justify-center bg-gradient-to-b from-zinc-900 to-black text-white">
            <div className="w-full max-w-md p-8 rounded-2xl bg-zinc-900/70 backdrop-blur-lg shadow-xl border border-zinc-800">
                <div className="flex items-center gap-3 mb-4">
                    <div className="size-6 rounded-full border-2 border-zinc-500 border-t-white animate-spin" />
                    <h1 className="text-xl font-semibold tracking-tight">Generating your 7-day meal plan…</h1>
                </div>
                <p className="text-zinc-400 text-sm">
                    This usually takes a few seconds while we crunch macros and recipes.
                </p>

                {error && (
                    <div className="mt-6 rounded-lg border border-red-500/40 bg-red-500/10 p-4">
                        <p className="text-red-300 text-sm mb-3">{error}</p>
                        <div className="flex gap-2">
                            <button
                                onClick={() => location?.state?.from === "prefs"
                                    ? navigate(-1)
                                    : navigate("/")}
                                className="px-3 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 transition"
                            >
                                Go back
                            </button>
                            <button
                                onClick={() => navigate(0)}
                                className="px-3 py-2 rounded-lg bg-white text-black font-medium hover:bg-zinc-200 transition"
                            >
                                Try again
                            </button>
                        </div>
                    </div>
                )}

                {!error && (
                    <div className="mt-6 text-xs text-zinc-500">
                        Tip: keep this tab open—your plan will appear automatically.
                    </div>
                )}
            </div>
        </div>
    );
}
