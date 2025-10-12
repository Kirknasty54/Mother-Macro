import { useEffect, useRef, useState } from "react";
import { chatApi } from "../api/client";

export default function ChatWidget({ mealplan }) {
    const [open, setOpen] = useState(false);
    const [msgs, setMsgs] = useState(() => [
        { role: "assistant", content: "Hey! I’m your meal coach. Ask me about swaps, groceries, or macros." },
    ]);
    const [input, setInput] = useState("");
    const [pending, setPending] = useState(false);
    const scrollRef = useRef(null);

    // auto scroll on new messages
    useEffect(() => {
        if (!open) return;
        scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
    }, [open, msgs]);

    // handle Escape to close
    useEffect(() => {
        const onKey = (e) => {
            if (e.key === "Escape") setOpen(false);
        };
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
    }, []);

    const send = async () => {
        const text = input.trim();
        if (!text || pending) return;

        const nextMsgs = [...msgs, { role: "user", content: text }];
        setMsgs(nextMsgs);
        setInput("");
        setPending(true);

        try {
            // normalize roles/content so backend never chokes
            const payloadMsgs = nextMsgs.map(m => ({
                role: String(m.role || "").toLowerCase(),
                content: String(m.content ?? "")
            }));

            const res = await chatApi.send(payloadMsgs, mealplan); // two args
            console.log("chat debug <-", res.debug);
            setMsgs(m => [...m, { role: "assistant", content: res.reply }]);
        } catch (e) {
            setMsgs(m => [...m, { role: "assistant", content: e.message || "Sorry—something broke." }]);
        } finally {
            setPending(false);
        }
    };


    const onKeyDown = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            send();
        }
    };

    return (
        <>
            {/* Floating button */}
            <button
                type="button"
                onClick={() => setOpen((v) => !v)}
                className="fixed bottom-4 right-4 z-[60] rounded-full shadow-lg bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-3 flex items-center gap-2"
                aria-expanded={open}
                aria-controls="meal-chat-panel"
            >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" className="opacity-90">
                    <path d="M4 5h16v9H7l-3 3V5z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                <span className="font-medium">Chat</span>
                {pending && <span className="ml-1 size-2 rounded-full bg-white animate-pulse" />}
            </button>

            {/* Panel */}
            {open && (
                <div
                    id="meal-chat-panel"
                    className="fixed bottom-20 right-4 z-[60] w-[min(92vw,380px)] h-[520px] rounded-2xl border border-zinc-800 bg-zinc-950/95 backdrop-blur-lg text-zinc-100 shadow-2xl flex flex-col"
                >
                    <header className="px-4 py-3 border-b border-zinc-800 flex items-center gap-2">
                        <div className={`size-2 rounded-full ${pending ? "bg-emerald-400 animate-pulse" : "bg-emerald-500"}`} />
                        <div className="font-semibold text-sm">Meal Coach</div>
                        <div className="ml-auto">
                            <button
                                onClick={() => setOpen(false)}
                                className="px-2 py-1 text-zinc-400 hover:text-zinc-200"
                                aria-label="Close chat"
                            >
                                ✕
                            </button>
                        </div>
                    </header>

                    <div ref={scrollRef} className="flex-1 overflow-y-auto px-3 py-3 space-y-2">
                        {msgs.map((m, i) => (
                            <div
                                key={i}
                                className={`max-w-[85%] rounded-xl px-3 py-2 text-sm leading-relaxed ${
                                    m.role === "assistant" ? "bg-zinc-800/70" : "bg-emerald-600/80 ml-auto"
                                }`}
                            >
                                {m.content}
                            </div>
                        ))}
                        {pending && (
                            <div className="max-w-[60%] rounded-xl px-3 py-2 bg-zinc-800/70 text-sm text-zinc-300">
                                <span className="inline-block size-2 rounded-full bg-zinc-400 animate-bounce mr-2" />
                                Typing…
                            </div>
                        )}
                    </div>

                    <footer className="border-t border-zinc-800 p-2">
                        <div className="flex items-end gap-2">
              <textarea
                  rows={1}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={onKeyDown}
                  placeholder="Ask about swaps, groceries, macros…"
                  className="flex-1 max-h-28 resize-y rounded-lg bg-zinc-900 border border-zinc-800 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-600"
              />
                            <button
                                onClick={send}
                                disabled={pending || !input.trim()}
                                className="px-3 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50"
                            >
                                Send
                            </button>
                        </div>
                    </footer>
                </div>
            )}
        </>
    );
}
