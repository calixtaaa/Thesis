/* ================================================================
   Hygiene Vending — Admin Dashboard
   React Application (mirrors desktop admin.py exactly)
   Real-time polling every 5 seconds
   ================================================================ */

const { useState, useEffect, useRef, useCallback, useMemo } = React;

const POLL_MS = 5000;

// ── API helper (includes CSRF token for state-changing requests) ──
async function api(path, opts = {}) {
    const headers = { "Content-Type": "application/json" };
    const csrfToken = window.__CSRF_TOKEN__;
    if (csrfToken && opts.method && opts.method !== "GET") {
        headers["X-CSRF-Token"] = csrfToken;
    }
    const res = await fetch(path, { headers, ...opts });
    if (res.status === 401) {
        window.location.href = "/login";
        return null;
    }
    if (res.status === 403) {
        window.location.href = "/login";
        return null;
    }
    return res.json();
}

// ── Polling hook ───────────────────────────────────────────────────
function usePolling(fetcher, deps, interval) {
    const ms = interval || POLL_MS;
    const [data, setData] = useState(null);
    const fn = useCallback(fetcher, deps || []);

    useEffect(() => {
        let active = true;
        const load = async () => {
            const d = await fn();
            if (active) setData(d);
        };
        load();
        const id = setInterval(load, ms);
        return () => { active = false; clearInterval(id); };
    }, [fn, ms]);

    return data;
}

// ── Toast hook ─────────────────────────────────────────────────────
let _toastTimer;
function useToast() {
    const [msg, setMsg] = useState("");
    const show = useCallback((text) => {
        setMsg(text);
        clearTimeout(_toastTimer);
        _toastTimer = setTimeout(() => setMsg(""), 2800);
    }, []);
    return { msg, show };
}

// ── Theme hook (light/dark, persisted to localStorage) ─────────────
function useTheme() {
    const [dark, setDark] = useState(() => {
        try { return localStorage.getItem("theme") === "dark"; } catch (e) { return false; }
    });
    useEffect(() => {
        document.documentElement.classList.toggle("dark", dark);
        try { localStorage.setItem("theme", dark ? "dark" : "light"); } catch (e) {}
    }, [dark]);
    const toggle = useCallback(() => setDark((d) => !d), []);
    return { dark, toggle };
}

function Toast({ message, dark }) {
    if (!message) return null;
    return (
        <div className="fixed bottom-7 left-1/2 -translate-x-1/2 px-6 py-3 rounded-full text-sm font-medium ios-shadow-lg z-[300] toast-enter text-white" style={{background: "var(--accent)"}}>
            {message}
        </div>
    );
}

// ── Icons ──────────────────────────────────────────────────────────
const I = {
    Grid:    () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>,
    Bag:     () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 01-8 0"/></svg>,
    Users:   () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>,
    Sliders: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/></svg>,
    Cpu:     () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>,
    File:    () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>,
    Gear:    () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 112.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 114 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>,
    Peso:    () => <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><text x="5" y="19" fontSize="18" fontWeight="bold" fill="currentColor" stroke="none">&#x20B1;</text></svg>,
    Brain:   () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a7 7 0 017 7c0 2.38-1.19 4.47-3 5.74V17a2 2 0 01-2 2h-4a2 2 0 01-2-2v-2.26C6.19 13.47 5 11.38 5 9a7 7 0 017-7z"/><line x1="9" y1="22" x2="15" y2="22"/><line x1="10" y1="2" x2="10" y2="7"/><line x1="14" y1="2" x2="14" y2="7"/></svg>,
    Box:     () => <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/></svg>,
    Person:  () => <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>,
    Alert:   () => <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>,
    Menu:    () => <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>,
    Logo:    () => <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="3" width="20" height="18" rx="3"/><path d="M8 7h8M8 11h5"/></svg>,
    Sun:     () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>,
    Moon:    () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg>,
};

// ── Chart theme colors ─────────────────────────────────────────────
function chartColors() {
    const dark = document.documentElement.classList.contains("dark");
    return {
        bar:    dark ? "#22d3ee" : "#10b981",
        line:   dark ? "#8b5cf6" : "#6366f1",
        fill:   dark ? "rgba(34,211,238,.12)" : "rgba(16,185,129,.10)",
        grid:   dark ? "rgba(148,163,184,.1)" : "rgba(15,23,42,.06)",
        text:   dark ? "#94a3b8" : "#64748b",
        point:  dark ? "#a78bfa" : "#4f46e5",
    };
}

// ── Chart component ────────────────────────────────────────────────
function ChartCanvas({ type, data, options, height }) {
    const ref = useRef(null);
    const chart = useRef(null);
    const h = height || "h-64";

    useEffect(() => {
        if (!ref.current || !data) return;
        if (chart.current) chart.current.destroy();

        const c = chartColors();
        const isDark = document.documentElement.classList.contains("dark");
        const defaults = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false, labels: { color: c.text } },
                tooltip: {
                    backgroundColor: isDark ? "#1c1c1e" : "#ffffff",
                    titleColor: isDark ? "#f5f5f7" : "#1c1c1e",
                    bodyColor: isDark ? "#e5e5ea" : "#3c3c43",
                    borderColor: isDark ? "#3a3a3c" : "#d1d1d6",
                    borderWidth: 1,
                    cornerRadius: 10,
                    padding: 10,
                    titleFont: { weight: "600" },
                },
            },
            scales: {
                x: { ticks: { color: c.text }, grid: { color: c.grid } },
                y: { ticks: { color: c.text }, grid: { color: c.grid } },
            },
        };

        const merged = JSON.parse(JSON.stringify(defaults));
        if (options) {
            Object.keys(options).forEach((k) => {
                if (k === "plugins") return;
                if (k === "scales") {
                    Object.keys(options.scales).forEach((axis) => {
                        var base = merged.scales[axis] || {};
                        var defAxis = defaults.scales[axis] || {};
                        merged.scales[axis] = Object.assign({}, base, options.scales[axis]);
                        if (options.scales[axis].ticks) {
                            merged.scales[axis].ticks = Object.assign({}, defAxis.ticks || {}, options.scales[axis].ticks);
                        }
                        if (options.scales[axis].grid) {
                            merged.scales[axis].grid = Object.assign({}, defAxis.grid || {}, options.scales[axis].grid);
                        }
                    });
                } else if (typeof options[k] === "object" && !Array.isArray(options[k]) && defaults[k]) {
                    merged[k] = { ...defaults[k], ...options[k] };
                } else {
                    merged[k] = options[k];
                }
            });
        }
        if (options && options.plugins) {
            merged.plugins = { ...defaults.plugins, ...options.plugins };
            if (options.plugins.legend) merged.plugins.legend = { ...defaults.plugins.legend, ...options.plugins.legend };
            if (options.plugins.tooltip) merged.plugins.tooltip = { ...defaults.plugins.tooltip, ...options.plugins.tooltip };
        }

        chart.current = new Chart(ref.current.getContext("2d"), {
            type: type,
            data: data,
            options: merged,
        });

        return () => { if (chart.current) chart.current.destroy(); };
    }, [data]);

    return (
        <div className={h}>
            <canvas ref={ref}></canvas>
        </div>
    );
}

// ── Modal ──────────────────────────────────────────────────────────
function Modal({ open, onClose, title, subtitle, children }) {
    if (!open) return null;
    return (
        <div className="fixed inset-0 z-[200] flex items-center justify-center modal-backdrop animate-fadein" onClick={onClose}>
            <div className="ios-card rounded-[20px] p-7 w-[90%] max-w-[420px] ios-shadow-lg" onClick={(e) => e.stopPropagation()}>
                <h3 className="text-lg font-bold">{title}</h3>
                {subtitle && <p className="text-sm text-ios-secondary mt-0.5 mb-5">{subtitle}</p>}
                {children}
            </div>
        </div>
    );
}

// ── Nav items (matches admin.py sidebar) ───────────────────────────
const NAV = [
    { id: "overview",    label: "Overview",              icon: I.Grid },
    { id: "products",    label: "Products",              icon: I.Bag },
    { id: "analysis",    label: "Prediction Analysis",   icon: I.Brain },
    { id: "rfid",        label: "RFID Roles",            icon: I.Users },
    { id: "pulse",       label: "Cash Pulse Settings",   icon: I.Sliders },
    { id: "diagnostics", label: "Hardware Diagnostics",  icon: I.Cpu },
    { id: "reports",     label: "Sales Reports",         icon: I.File },
    { id: "credentials", label: "Change Credentials",    icon: I.Gear },
];


/* ================================================================
   PAGE: OVERVIEW
   (matches: show_admin_dashboard in admin.py)
   ================================================================ */
function OverviewPage({ toast, dark }) {
    const stats   = usePolling(() => api("/api/overview"));
    const trend   = usePolling(() => api("/api/sales-trend"));
    const monthly = usePolling(() => api("/api/monthly-sales"));
    const top     = usePolling(() => api("/api/top-products"));
    const low     = usePolling(() => api("/api/low-stock"));

    const [pred, setPred] = useState(null);
    const [predLoading, setPredLoading] = useState(false);

    const runPrediction = async () => {
        setPredLoading(true);
        const res = await api("/api/prediction", { method: "POST" });
        setPredLoading(false);
        if (res) { setPred(res); toast("Prediction analysis complete"); }
    };

    const exportReport = async () => {
        const res = await api("/api/export-report", { method: "POST" });
        if (res && res.status === "ok") toast("Report exported: " + res.path);
    };

    const trendChart = useMemo(() => {
        if (!trend) return null;
        const c = chartColors();
        return {
            labels: trend.map((d) => d.label),
            datasets: [{
                data: trend.map((d) => d.value),
                borderColor: c.line,
                backgroundColor: c.fill,
                fill: true,
                borderWidth: 2,
                pointRadius: 3,
                pointBackgroundColor: c.point,
                tension: 0.35,
            }],
        };
    }, [trend, dark]);

    const monthlyChart = useMemo(() => {
        if (!monthly) return null;
        const c = chartColors();
        return {
            labels: monthly.map((d) => d.label),
            datasets: [{
                data: monthly.map((d) => d.value),
                backgroundColor: c.bar,
                borderRadius: 6,
                maxBarThickness: 40,
            }],
        };
    }, [monthly, dark]);

    const topChart = useMemo(() => {
        if (!top) return null;
        const c = chartColors();
        return {
            labels: top.map((d) => d.label),
            datasets: [{
                data: top.map((d) => d.value),
                backgroundColor: c.bar,
                borderRadius: 6,
                maxBarThickness: 28,
            }],
        };
    }, [top, dark]);

    const lowChart = useMemo(() => {
        if (!low || low.length === 0) return null;
        return {
            labels: low.map((d) => d.label),
            datasets: [
                { label: "Current Stock", data: low.map((d) => d.value), backgroundColor: "#ff9500", borderRadius: 6, maxBarThickness: 28 },
                { label: "Capacity", data: low.map((d) => d.capacity), backgroundColor: dark ? "#3a3a3c" : "#e0e0e0", borderRadius: 6, maxBarThickness: 28 },
            ],
        };
    }, [low, dark]);

    const peso = (v) => {
        return "\u20B1" + Number(v).toLocaleString("en", { minimumFractionDigits: 2 });
    };

    const statCards = [
        { label: "Total Sales",    value: stats ? peso(stats.total_sales) : "--", icon: <I.Peso />, bg: "bg-green-50",  clr: "text-green-600" },
        { label: "Orders",         value: stats ? stats.orders : "--",             icon: <I.Box />,    bg: "bg-blue-50",   clr: "text-blue-600" },
        { label: "RFID Customers", value: stats ? stats.active_customers : "--",   icon: <I.Person />, bg: "bg-purple-50", clr: "text-purple-600" },
        { label: "Low Stock",      value: stats ? stats.low_stock : "--",          icon: <I.Alert />,  bg: "bg-orange-50", clr: "text-orange-500" },
    ];

    return (
        <div className="animate-fadein">
            <div className="mb-7">
                <h1 className="text-3xl font-bold tracking-tight">Overview</h1>
                <p className="text-ios-secondary text-[15px] mt-0.5">Dashboard summary and key metrics</p>
            </div>

            {/* Stat cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-7">
                {statCards.map((s, i) => (
                    <div key={i} className="ios-card ios-card-hover p-5 flex items-center gap-4 transition-all">
                        <div className={"w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 " + s.bg + " " + s.clr}>
                            {s.icon}
                        </div>
                        <div className="flex flex-col">
                            <span className="text-[11px] font-semibold text-ios-secondary uppercase tracking-wider">{s.label}</span>
                            <span className="text-2xl font-bold tracking-tight mt-0.5">{s.value}</span>
                        </div>
                    </div>
                ))}
            </div>

            {/* Charts row 1 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
                <div className="ios-card p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="font-semibold">Sales by Created Date</h3>
                        <span className="text-xs font-medium text-ios-secondary bg-ios-bg px-2.5 py-1 rounded-full">Last 15 days</span>
                    </div>
                    <ChartCanvas
                        type="line"
                        data={trendChart}
                        options={{
                            scales: { y: { beginAtZero: true, ticks: { callback: (v) => "\u20B1" + v } } },
                            plugins: { tooltip: { callbacks: { label: (ctx) => "\u20B1" + ctx.parsed.y.toLocaleString() } } },
                        }}
                    />
                </div>
                <div className="ios-card p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="font-semibold">Monthly Sales</h3>
                        <span className="text-xs font-medium text-ios-secondary bg-ios-bg px-2.5 py-1 rounded-full">Last 6 months</span>
                    </div>
                    <ChartCanvas
                        type="bar"
                        data={monthlyChart}
                        options={{ scales: { y: { beginAtZero: true, ticks: { callback: (v) => "\u20B1" + v } } } }}
                    />
                </div>
            </div>

            {/* Charts row 2 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
                <div className="ios-card p-6">
                    <h3 className="font-semibold mb-4">Top-selling Products</h3>
                    <ChartCanvas
                        type="bar"
                        data={topChart}
                        options={{ indexAxis: "y", scales: { x: { beginAtZero: true } } }}
                    />
                </div>
                <div className="ios-card p-6">
                    <h3 className="font-semibold mb-4">Low-stock Products</h3>
                    {lowChart
                        ? <ChartCanvas type="bar" data={lowChart} options={{ indexAxis: "y", scales: { x: { beginAtZero: true } }, plugins: { legend: { display: true, position: "bottom" } } }} />
                        : <p className="text-ios-secondary text-sm py-10 text-center">All products are sufficiently stocked.</p>
                    }
                </div>
            </div>

            {/* Prediction analysis */}
            <div className="ios-card p-6 mb-4">
                <h3 className="font-semibold">Prediction Analysis (Demand + Restock)</h3>
                <p className="text-sm text-ios-secondary mt-1 mb-4">
                    Predicts sales tomorrow and recommends restock using historical transactions.
                </p>
                <div className="flex flex-wrap items-center gap-3 mb-4">
                    <button className="btn-black" onClick={runPrediction} disabled={predLoading}>
                        {predLoading ? "Running..." : pred ? "Re-run Prediction" : "Run Prediction Analysis"}
                    </button>
                    <button className="btn-black" onClick={exportReport}>Generate Excel Report</button>
                </div>

                {pred && pred.summary && (
                    <p className="text-xs text-ios-secondary mb-3">
                        Based on data up to: {pred.summary.based_on_last_date || "N/A"} &middot; Generated: {pred.summary.generated_at_iso}
                    </p>
                )}

                {pred && pred.results && pred.results.length > 0 && (
                    <div className="overflow-x-auto rounded-xl border border-gray-100">
                        <table className="ios-table">
                            <thead>
                                <tr>
                                    <th>Product</th>
                                    <th>Predicted Sales Tomorrow</th>
                                    <th>Restock Needed</th>
                                </tr>
                            </thead>
                            <tbody>
                                {pred.results.slice(0, 10).map((r, i) => (
                                    <tr key={i}>
                                        <td className="font-medium">{r.product_name}</td>
                                        <td>{r.predicted_sales_tomorrow}</td>
                                        <td>
                                            {r.recommended_restock_qty > 0
                                                ? <span className="font-semibold">Yes ({r.recommended_restock_qty})</span>
                                                : <span className="text-ios-secondary">No</span>
                                            }
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}


/* ================================================================
   PAGE: PREDICTION ANALYSIS
   (integrates: extract_dataset.py, forecast.py, insights.py, plots.py)
   ================================================================ */
function AnalysisPage({ toast, dark }) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const runAnalysis = async () => {
        setLoading(true);
        setError("");
        const res = await api("/api/analysis/run", { method: "POST" });
        setLoading(false);
        if (!res) return;
        if (res.status === "error") {
            setError(res.message || "Analysis failed.");
            return;
        }
        setData(res);
        toast("Prediction analysis complete");
    };

    const ins = data && data.insights;
    const forecasts = data && data.forecasts;
    const metrics = data && data.metrics;

    const monthlyChart = useMemo(() => {
        if (!ins || !ins.monthly_qty || ins.monthly_qty.length === 0) return null;
        const c = chartColors();
        return {
            labels: ins.monthly_qty.map((d) => d.sale_month),
            datasets: [{
                data: ins.monthly_qty.map((d) => d.quantity),
                borderColor: c.line,
                backgroundColor: c.fill,
                fill: true,
                borderWidth: 2,
                pointRadius: 3,
                pointBackgroundColor: c.point,
                tension: 0.35,
            }],
        };
    }, [ins, dark]);

    const peakHoursChart = useMemo(() => {
        if (!ins || !ins.peak_hours || ins.peak_hours.length === 0) return null;
        const c = chartColors();
        return {
            labels: ins.peak_hours.map((d) => {
                const h = parseInt(d.sale_hour, 10);
                const suffix = h >= 12 ? " PM" : " AM";
                const h12 = h === 0 ? 12 : h > 12 ? h - 12 : h;
                return String(h12).padStart(2, "0") + ":00" + suffix;
            }),
            datasets: [{
                data: ins.peak_hours.map((d) => d.quantity),
                backgroundColor: c.bar,
                borderRadius: 6,
                maxBarThickness: 40,
            }],
        };
    }, [ins, dark]);

    const topChart = useMemo(() => {
        if (!ins || !ins.top_products || ins.top_products.length === 0) return null;
        const c = chartColors();
        return {
            labels: ins.top_products.map((d) => d.product_name),
            datasets: [{
                data: ins.top_products.map((d) => d.quantity),
                backgroundColor: c.bar,
                borderRadius: 6,
                maxBarThickness: 28,
            }],
        };
    }, [ins, dark]);

    const weekdayChart = useMemo(() => {
        if (!ins || !ins.weekday_totals || ins.weekday_totals.length === 0) return null;
        const c = chartColors();
        return {
            labels: ins.weekday_totals.map((d) => d.weekday),
            datasets: [{
                data: ins.weekday_totals.map((d) => d.quantity),
                backgroundColor: c.bar,
                borderRadius: 6,
                maxBarThickness: 40,
            }],
        };
    }, [ins, dark]);

    return (
        <div className="animate-fadein">
            <div className="mb-7">
                <h1 className="text-3xl font-bold tracking-tight">Prediction Analysis</h1>
                <p className="text-ios-secondary text-[15px] mt-0.5">
                    Full ML pipeline — extract dataset, compute insights, forecast demand (Random Forest), and restock recommendations
                </p>
            </div>

            <div className="mb-6 flex flex-wrap items-center gap-3">
                <button className="btn-black" onClick={runAnalysis} disabled={loading}>
                    {loading ? "Running Pipeline..." : data ? "Re-run Full Analysis" : "Run Prediction Analysis"}
                </button>
                {error && <span className="text-red-500 text-sm font-medium">{error}</span>}
            </div>

            {!data && !loading && (
                <div className="ios-card p-10 text-center">
                    <p className="text-ios-secondary">Click <strong>"Run Prediction Analysis"</strong> to extract data from vending.db, compute insights, and generate ML forecasts.</p>
                </div>
            )}

            {loading && (
                <div className="ios-card p-10 text-center">
                    <p className="text-ios-secondary">Running the full prediction pipeline (extract, insights, forecast)...</p>
                </div>
            )}

            {ins && (
                <React.Fragment>
                    {/* Insights Section */}
                    <h2 className="text-xl font-bold tracking-tight mb-4">Insights</h2>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
                        <div className="ios-card p-6">
                            <h3 className="font-semibold mb-4">Most Purchased Products (Top 10)</h3>
                            {topChart
                                ? <ChartCanvas type="bar" data={topChart} options={{ indexAxis: "y", scales: { x: { beginAtZero: true } } }} />
                                : <p className="text-ios-secondary text-sm text-center py-6">No data</p>
                            }
                        </div>
                        <div className="ios-card p-6">
                            <h3 className="font-semibold mb-4">Peak Purchase Hours</h3>
                            {peakHoursChart
                                ? <ChartCanvas type="bar" data={peakHoursChart} options={{ scales: { y: { beginAtZero: true } } }} />
                                : <p className="text-ios-secondary text-sm text-center py-6">No data</p>
                            }
                        </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
                        <div className="ios-card p-6">
                            <h3 className="font-semibold mb-4">Purchases by Weekday</h3>
                            {weekdayChart
                                ? <ChartCanvas type="bar" data={weekdayChart} options={{ scales: { y: { beginAtZero: true } } }} />
                                : <p className="text-ios-secondary text-sm text-center py-6">No data</p>
                            }
                        </div>
                        <div className="ios-card p-6">
                            <h3 className="font-semibold mb-4">Monthly Sales Quantity Trend</h3>
                            {monthlyChart
                                ? <ChartCanvas type="line" data={monthlyChart} options={{ scales: { y: { beginAtZero: true } } }} />
                                : <p className="text-ios-secondary text-sm text-center py-6">No data</p>
                            }
                        </div>
                    </div>

                    {/* Forecast Section */}
                    {forecasts && forecasts.length > 0 && (
                        <React.Fragment>
                            <h2 className="text-xl font-bold tracking-tight mb-4">Forecast &amp; Restock Recommendations</h2>
                            <div className="ios-card overflow-hidden mb-6">
                                <div className="overflow-x-auto">
                                    <table className="ios-table">
                                        <thead>
                                            <tr>
                                                <th>Product</th>
                                                <th>Predicted Sales Tomorrow</th>
                                                <th>Current Stock</th>
                                                <th>Capacity</th>
                                                <th>Restock Qty</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {forecasts.map((f, i) => (
                                                <tr key={i}>
                                                    <td className="font-semibold">{f.product_name}</td>
                                                    <td>{typeof f.predicted_sales_tomorrow === "number" ? f.predicted_sales_tomorrow.toFixed(2) : f.predicted_sales_tomorrow}</td>
                                                    <td>{f.current_stock}</td>
                                                    <td>{f.capacity || "\u2014"}</td>
                                                    <td>
                                                        {f.recommended_restock_qty > 0
                                                            ? <span className="font-semibold">{f.recommended_restock_qty}</span>
                                                            : <span className="text-ios-secondary">0</span>
                                                        }
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </React.Fragment>
                    )}

                    {/* Model Metrics */}
                    {metrics && metrics.length > 0 && (
                        <React.Fragment>
                            <h2 className="text-xl font-bold tracking-tight mb-4">Model Performance (Random Forest)</h2>
                            <div className="ios-card overflow-hidden mb-6">
                                <div className="overflow-x-auto">
                                    <table className="ios-table">
                                        <thead>
                                            <tr>
                                                <th>Product</th>
                                                <th>MAE</th>
                                                <th>RMSE</th>
                                                <th>Train Days</th>
                                                <th>Test Days</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {metrics.map((m, i) => (
                                                <tr key={i}>
                                                    <td className="font-semibold">{m.product_name}</td>
                                                    <td>{typeof m.mae === "number" ? m.mae.toFixed(3) : m.mae}</td>
                                                    <td>{typeof m.rmse === "number" ? m.rmse.toFixed(3) : m.rmse}</td>
                                                    <td>{m.train_days}</td>
                                                    <td>{m.test_days}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </React.Fragment>
                    )}

                    {data && data.message && (
                        <div className="ios-card p-6">
                            <p className="text-ios-secondary text-sm">{data.message}</p>
                        </div>
                    )}
                </React.Fragment>
            )}
        </div>
    );
}


/* ================================================================
   PAGE: PRODUCTS
   (matches: product management + restock in admin.py)
   ================================================================ */
function ProductsPage({ toast, dark }) {
    const products = usePolling(() => api("/api/products"));
    const [modal, setModal] = useState(null);
    const [amount, setAmount] = useState(5);
    const [price, setPrice] = useState("");

    const openRestock = (p) => {
        setModal(p);
        setAmount(5);
        setPrice("");
    };

    const doRestock = async (e) => {
        e.preventDefault();
        const body = { amount: parseInt(amount, 10) };
        if (price) body.new_price = parseFloat(price);
        await api("/api/products/" + modal.id + "/restock", { method: "POST", body: JSON.stringify(body) });
        setModal(null);
        toast("Product restocked successfully");
    };

    const stockPill = (p) => {
        const pct = p.capacity > 0 ? (p.current_stock / p.capacity) * 100 : 0;
        if (p.current_stock === 0) return <span className="pill pill-red">Empty</span>;
        if (pct < 40) return <span className="pill pill-orange">Low</span>;
        return <span className="pill pill-green">In Stock</span>;
    };

    return (
        <div className="animate-fadein">
            <div className="mb-7">
                <h1 className="text-3xl font-bold tracking-tight">Products</h1>
                <p className="text-ios-secondary text-[15px] mt-0.5">Manage inventory and restock products</p>
            </div>

            <div className="ios-card overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="ios-table">
                        <thead>
                            <tr>
                                <th>Slot</th>
                                <th>Product Name</th>
                                <th>Price</th>
                                <th>Stock</th>
                                <th>Capacity</th>
                                <th>Status</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {products && products.map((p) => (
                                <tr key={p.id}>
                                    <td>{p.slot_number}</td>
                                    <td className="font-semibold">{p.name}</td>
                                    <td>{"\u20B1" + Number(p.price).toFixed(2)}</td>
                                    <td>{p.current_stock}</td>
                                    <td>{p.capacity}</td>
                                    <td>{stockPill(p)}</td>
                                    <td><button className="btn-black btn-sm" onClick={() => openRestock(p)}>Restock</button></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            <Modal open={!!modal} onClose={() => setModal(null)} title="Restock Product" subtitle={modal ? modal.name : ""}>
                <form onSubmit={doRestock} className="flex flex-col gap-4">
                    <div>
                        <label className="ios-label">Quantity to Add</label>
                        <input type="number" min="1" value={amount} onChange={(e) => setAmount(e.target.value)} required className="ios-input" />
                    </div>
                    <div>
                        <label className="ios-label">New Price (optional)</label>
                        <input type="number" step="0.01" value={price} onChange={(e) => setPrice(e.target.value)} placeholder="Leave blank to keep current" className="ios-input" />
                    </div>
                    <div className="flex gap-2.5 mt-2">
                        <button type="button" className="btn-white flex-1" onClick={() => setModal(null)}>Cancel</button>
                        <button type="submit" className="btn-black flex-1">Restock</button>
                    </div>
                </form>
            </Modal>
        </div>
    );
}


/* ================================================================
   PAGE: RFID ROLES
   (matches: show_rfid_roles_screen in admin.py)
   ================================================================ */
function RFIDPage({ toast, dark }) {
    const users = usePolling(() => api("/api/rfid-users"));
    const [modal, setModal] = useState(null);
    const [role, setRole] = useState("customer");
    const roles = ["customer", "restocker", "researcher", "troubleshooter", "admin"];

    const openRole = (u) => {
        setModal(u);
        setRole(u.role || "customer");
    };

    const saveRole = async (e) => {
        e.preventDefault();
        await api("/api/rfid-users/" + modal.id + "/role", { method: "PUT", body: JSON.stringify({ role: role }) });
        setModal(null);
        toast("Role updated successfully");
    };

    return (
        <div className="animate-fadein">
            <div className="mb-7">
                <h1 className="text-3xl font-bold tracking-tight">RFID Role Management</h1>
                <p className="text-ios-secondary text-[15px] mt-0.5">Roles: customer, restocker, researcher, troubleshooter, admin</p>
            </div>

            <div className="ios-card overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="ios-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>RFID UID</th>
                                <th>Name</th>
                                <th>Balance</th>
                                <th>Staff</th>
                                <th>Role</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users && users.map((u) => (
                                <tr key={u.id}>
                                    <td>{u.id}</td>
                                    <td className="font-mono text-sm">{u.rfid_uid}</td>
                                    <td>{u.name || "\u2014"}</td>
                                    <td>{"\u20B1" + Number(u.balance).toFixed(2)}</td>
                                    <td>{u.is_staff ? "Yes" : "No"}</td>
                                    <td className="font-medium">{u.role}</td>
                                    <td><button className="btn-white btn-sm" onClick={() => openRole(u)}>Edit Role</button></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            <Modal open={!!modal} onClose={() => setModal(null)} title="Change User Role" subtitle={modal ? (modal.name || modal.rfid_uid) : ""}>
                <form onSubmit={saveRole} className="flex flex-col gap-4">
                    <div>
                        <label className="ios-label">Role</label>
                        <select value={role} onChange={(e) => setRole(e.target.value)} className="ios-input">
                            {roles.map((r) => <option key={r} value={r}>{r}</option>)}
                        </select>
                    </div>
                    <div className="flex gap-2.5 mt-2">
                        <button type="button" className="btn-white flex-1" onClick={() => setModal(null)}>Cancel</button>
                        <button type="submit" className="btn-black flex-1">Save Role</button>
                    </div>
                </form>
            </Modal>
        </div>
    );
}


/* ================================================================
   PAGE: CASH PULSE SETTINGS
   (matches: show_cash_pulse_settings_screen in admin.py)
   ================================================================ */
function PulseSettingsPage({ toast, dark }) {
    const [coin, setCoin] = useState("");
    const [bill, setBill] = useState("");
    const [loaded, setLoaded] = useState(false);

    useEffect(() => {
        api("/api/hardware-settings").then((data) => {
            if (data) {
                setCoin(data.coin_pulse_value);
                setBill(data.bill_pulse_value);
                setLoaded(true);
            }
        });
    }, []);

    const save = async (e) => {
        e.preventDefault();
        const c = parseFloat(coin);
        const b = parseFloat(bill);
        if (isNaN(c) || isNaN(b) || c <= 0 || b <= 0) {
            toast("Values must be positive numbers");
            return;
        }
        await api("/api/hardware-settings", {
            method: "PUT",
            body: JSON.stringify({ coin_pulse_value: c, bill_pulse_value: b }),
        });
        toast("Cash pulse settings saved");
    };

    return (
        <div className="animate-fadein">
            <div className="mb-7">
                <h1 className="text-3xl font-bold tracking-tight">Cash Pulse Settings</h1>
                <p className="text-ios-secondary text-[15px] mt-0.5">Set how much peso value each input pulse represents.</p>
            </div>

            <div className="ios-card p-7 max-w-lg">
                {loaded && (
                    <form onSubmit={save} className="flex flex-col gap-4">
                        <div>
                            <label className="ios-label">Coin Acceptor Pulse Value (PHP)</label>
                            <input type="number" step="0.01" value={coin} onChange={(e) => setCoin(e.target.value)} required className="ios-input" />
                        </div>
                        <div>
                            <label className="ios-label">Bill Acceptor Pulse Value (PHP)</label>
                            <input type="number" step="0.01" value={bill} onChange={(e) => setBill(e.target.value)} required className="ios-input" />
                        </div>
                        <button type="submit" className="btn-black self-start mt-2">Save Settings</button>
                    </form>
                )}
            </div>
        </div>
    );
}


/* ================================================================
   PAGE: HARDWARE DIAGNOSTICS
   (matches: show_hardware_diagnostics_screen in admin.py)
   ================================================================ */
function DiagnosticsPage({ dark }) {
    const settings = usePolling(() => api("/api/hardware-settings"), [], 2000);

    return (
        <div className="animate-fadein">
            <div className="mb-7">
                <h1 className="text-3xl font-bold tracking-tight">Hardware Diagnostics</h1>
                <p className="text-ios-secondary text-[15px] mt-0.5">Monitor hardware pulse values and RFID reader status</p>
            </div>

            <div className="ios-card p-7 max-w-lg">
                <div className="space-y-1 mb-6">
                    <div className="flex items-center justify-between py-3 border-b border-gray-100">
                        <span className="text-sm text-ios-secondary">Coin pulse value</span>
                        <span className="text-sm font-semibold">{settings ? settings.coin_pulse_value : "..."} PHP</span>
                    </div>
                    <div className="flex items-center justify-between py-3 border-b border-gray-100">
                        <span className="text-sm text-ios-secondary">Bill pulse value</span>
                        <span className="text-sm font-semibold">{settings ? settings.bill_pulse_value : "..."} PHP</span>
                    </div>
                </div>
                <div className="bg-ios-bg rounded-xl p-4">
                    <p className="text-sm text-ios-secondary">
                        <strong className="text-ios-text">Note:</strong> RFID reader tap tests and live pulse counters are only available on the vending machine touchscreen interface. This page shows current hardware configuration, updated in real-time.
                    </p>
                </div>
            </div>
        </div>
    );
}


/* ================================================================
   PAGE: SALES REPORTS
   (matches: show_sales_reports_screen in admin.py)
   ================================================================ */
function ReportsPage({ toast, dark }) {
    const reports = usePolling(() => api("/api/sales-reports"));

    const exportReport = async () => {
        const res = await api("/api/export-report", { method: "POST" });
        if (res && res.status === "ok") toast("Report exported: " + res.path);
    };

    return (
        <div className="animate-fadein">
            <div className="mb-7">
                <h1 className="text-3xl font-bold tracking-tight">Sales Reports</h1>
                <p className="text-ios-secondary text-[15px] mt-0.5">Generated Excel reports</p>
            </div>

            <div className="mb-5">
                <button className="btn-black" onClick={exportReport}>Generate Excel Report</button>
            </div>

            <div className="ios-card overflow-hidden">
                {reports && reports.length > 0 ? (
                    <div className="divide-y divide-gray-50">
                        {reports.map((r, i) => (
                            <div key={i} className="flex items-center justify-between px-5 py-4 hover:bg-ios-bg transition-colors">
                                <span className="text-sm font-medium">{r.name}</span>
                                <span className="text-xs text-ios-secondary font-mono truncate ml-4 max-w-[300px]">{r.path}</span>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="text-ios-secondary text-sm text-center py-10">No sales reports found. Generate one first.</p>
                )}
            </div>
        </div>
    );
}


/* ================================================================
   PAGE: CHANGE CREDENTIALS
   (matches: change_admin_credentials_screen in admin.py)
   ================================================================ */
function CredentialsPage({ toast, dark }) {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [confirm, setConfirm] = useState("");
    const [msg, setMsg] = useState({ text: "", ok: false });

    const save = async (e) => {
        e.preventDefault();
        if (password !== confirm) {
            setMsg({ text: "Passwords do not match.", ok: false });
            return;
        }
        if (password.length < 4) {
            setMsg({ text: "Password must be at least 4 characters.", ok: false });
            return;
        }
        const res = await api("/api/change-password", {
            method: "POST",
            body: JSON.stringify({ username: username, password: password }),
        });
        if (res && res.status === "ok") {
            setMsg({ text: "Credentials updated successfully.", ok: true });
            setUsername("");
            setPassword("");
            setConfirm("");
            toast("Credentials updated");
        } else {
            setMsg({ text: (res && res.message) || "Failed to update.", ok: false });
        }
    };

    return (
        <div className="animate-fadein">
            <div className="mb-7">
                <h1 className="text-3xl font-bold tracking-tight">Change Credentials</h1>
                <p className="text-ios-secondary text-[15px] mt-0.5">Update admin username and password</p>
            </div>

            <div className="ios-card p-7 max-w-lg">
                <form onSubmit={save} className="flex flex-col gap-4">
                    <div>
                        <label className="ios-label">New Username</label>
                        <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} required placeholder="Enter new username" className="ios-input" />
                    </div>
                    <div>
                        <label className="ios-label">New Password</label>
                        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required placeholder="Enter new password" className="ios-input" />
                    </div>
                    <div>
                        <label className="ios-label">Confirm Password</label>
                        <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required placeholder="Confirm new password" className="ios-input" />
                    </div>
                    {msg.text && (
                        <p className={"text-sm font-medium " + (msg.ok ? "text-green-600" : "text-red-500")}>{msg.text}</p>
                    )}
                    <button type="submit" className="btn-black self-start mt-1">Update Credentials</button>
                </form>
            </div>
        </div>
    );
}


/* ================================================================
   COMPONENT: Real-time Philippines Clock (UTC+8)
   ================================================================ */
function PHClock() {
    const [time, setTime] = useState("");
    const [date, setDate] = useState("");

    useEffect(() => {
        const tick = () => {
            const now = new Date();
            const ph = new Date(now.toLocaleString("en-US", { timeZone: "Asia/Manila" }));
            setTime(ph.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: true }));
            setDate(ph.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric", year: "numeric" }));
        };
        tick();
        const id = setInterval(tick, 1000);
        return () => clearInterval(id);
    }, []);

    return (
        <div className="px-5 py-3 border-t border-ios-separator text-center">
            <div className="text-xs text-ios-secondary uppercase tracking-wider font-semibold mb-0.5">Philippines Time</div>
            <div className="text-lg font-bold tracking-tight tabular-nums">{time}</div>
            <div className="text-xs text-ios-secondary">{date}</div>
        </div>
    );
}


/* ================================================================
   APP (root component)
   ================================================================ */
function App() {
    const [page, setPage] = useState("overview");
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const { msg: toastMsg, show: toast } = useToast();
    const { dark, toggle: toggleTheme } = useTheme();
    const username = window.__USERNAME__;

    const renderPage = () => {
        switch (page) {
            case "overview":    return <OverviewPage toast={toast} dark={dark} />;
            case "products":    return <ProductsPage toast={toast} dark={dark} />;
            case "analysis":    return <AnalysisPage toast={toast} dark={dark} />;
            case "rfid":        return <RFIDPage toast={toast} dark={dark} />;
            case "pulse":       return <PulseSettingsPage toast={toast} dark={dark} />;
            case "diagnostics": return <DiagnosticsPage dark={dark} />;
            case "reports":     return <ReportsPage toast={toast} dark={dark} />;
            case "credentials": return <CredentialsPage toast={toast} dark={dark} />;
            default:            return <OverviewPage toast={toast} dark={dark} />;
        }
    };

    const navClick = (id) => {
        setPage(id);
        setSidebarOpen(false);
    };

    return (
        <React.Fragment>
            {/* Sidebar */}
            <aside className={
                "fixed top-0 left-0 w-[260px] h-screen sidebar-surface border-r border-ios-separator flex flex-col z-[100] transition-transform duration-300 " +
                (sidebarOpen ? "" : "max-md:-translate-x-full")
            }>
                <div className="px-5 pt-7 pb-5 border-b border-ios-separator flex items-center justify-between">
                    <div className="flex items-center gap-2.5 font-bold text-[17px] tracking-tight">
                        <I.Logo />
                        <span>Vending Admin</span>
                    </div>
                    <button
                        onClick={toggleTheme}
                        className="theme-toggle-btn"
                        title={dark ? "Switch to Light Mode" : "Switch to Dark Mode"}
                    >
                        {dark ? <I.Sun /> : <I.Moon />}
                    </button>
                </div>

                <nav className="flex-1 p-2.5 flex flex-col gap-0.5 overflow-y-auto">
                    {NAV.map((n) => (
                        <a
                            key={n.id}
                            href="#"
                            onClick={(e) => { e.preventDefault(); navClick(n.id); }}
                            className={
                                "flex items-center gap-3 px-3.5 py-2.5 rounded-[10px] text-[15px] font-medium transition-colors no-underline " +
                                (page === n.id
                                    ? "text-white"
                                    : "nav-item-inactive")
                            }
                            style={page === n.id ? {background: "var(--accent)"} : {}}
                        >
                            <n.icon />
                            <span>{n.label}</span>
                        </a>
                    ))}
                </nav>

                <PHClock />

                <div className="p-5 border-t border-ios-separator flex flex-col gap-3">
                    <div className="flex items-center gap-2.5">
                        <div className="w-9 h-9 rounded-full flex items-center justify-center font-bold text-sm text-white" style={{background: "var(--accent)"}}>
                            {username ? username[0].toUpperCase() : "A"}
                        </div>
                        <div className="flex flex-col">
                            <span className="font-semibold text-sm">{username}</span>
                            <span className="text-xs text-ios-secondary">Administrator</span>
                        </div>
                    </div>
                    <a href={window.__LOGOUT_URL__} className="btn-white text-center no-underline">Sign Out</a>
                </div>
            </aside>

            {/* Mobile overlay */}
            {sidebarOpen && (
                <div className="fixed inset-0 bg-black/30 z-[99] md:hidden" onClick={() => setSidebarOpen(false)} />
            )}

            {/* Mobile header */}
            <header className="hidden max-md:flex fixed top-0 left-0 right-0 h-14 frosted-header border-b border-ios-separator z-[90] items-center px-4 gap-3.5">
                <button onClick={() => setSidebarOpen(true)} className="p-1 bg-transparent border-none cursor-pointer">
                    <I.Menu />
                </button>
                <span className="font-bold text-[17px] tracking-tight">Vending Admin</span>
            </header>

            {/* Main content */}
            <main className="ml-[260px] max-md:ml-0 max-md:pt-[72px] p-9 max-md:p-4 min-h-screen main-surface">
                {renderPage()}
            </main>

            <Toast message={toastMsg} dark={dark} />
        </React.Fragment>
    );
}

// ── Mount ──────────────────────────────────────────────────────────
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
