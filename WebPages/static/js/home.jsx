/* ═══════════════════════════════════════════════════════════════
   Home Page — React SPA (SyntaxError™ Hygiene Vending Machine)
   ═══════════════════════════════════════════════════════════════ */

const { useState, useEffect, useRef, useCallback, useMemo } = React;

// ── URLs from Jinja2 ─────────────────────────────────────────
const LOGIN_URL = window.__LOGIN_URL__ || "/login";
const HOME_URL = window.__HOME_URL__ || "/";

// ═════════════════════════════════════════════════════════════
//   DATA
// ═════════════════════════════════════════════════════════════

const TEAM_MEMBERS = [
    {
        name: "John Renzo G. Dacer",
        role: "Developer",
        roleClass: "role-developer",
        gender: "male",
        bio: "A student in the Bachelor of Engineering Technology major in Computer Engineering Technology at TUP-Manila. He is one of the main programmers on the software system, handling front-end and back-end development. He also assisted in setting up the hardware.",
        initials: "JD",
        gradientFrom: "#6366f1",
        gradientTo: "#8b5cf6",
        hasPhoto: true,
        photo: "/static/images/avatar_male.png",
    },
    {
        name: "Jose Angelo F. Lacerna",
        role: "Developer",
        roleClass: "role-developer",
        gender: "male",
        bio: "A student in the Bachelor of Engineering Technology major in Computer Engineering Technology at TUP-Manila. He is one of the main programmers on the software system, handling front-end and back-end development. He also assisted in setting up the hardware.",
        initials: "JL",
        gradientFrom: "#7c3aed",
        gradientTo: "#a78bfa",
        hasPhoto: true,
        photo: "/static/images/avatar_male.png"
    },
    {
        name: "Gideon P. Soberano",
        role: "Developer",
        roleClass: "role-developer",
        gender: "male",
        bio: "A student in the Bachelor of Engineering Technology major in Computer Engineering Technology at TUP-Manila. He designed the main prototype, ensuring its structure and layout align with the project's objectives. He also assisted the front-end/back-end teams and helped organize the paper.",
        initials: "GS",
        gradientFrom: "#0891b2",
        gradientTo: "#06b6d4",
        hasPhoto: true,
        photo: "/static/images/avatar_male.png"
    },
    {
        name: "Asriel T. Romulo",
        role: "Leader, Papers",
        roleClass: "role-leader",
        gender: "female",
        bio: "A student in the Bachelor of Engineering Technology major in Computer Engineering Technology at TUP-Manila. She contributed to setting up hardware components, helped develop and fabricate the prototype, and serves as editor and proofreader. She manages team logistics and project budgeting.",
        initials: "AR",
        gradientFrom: "#e11d48",
        gradientTo: "#f43f5e",
        hasPhoto: true,
        photo: "/static/images/avatar_male.png"
    },
    {
        name: "Jonamae Tiu",
        role: "Papers",
        roleClass: "role-papers",
        gender: "female",
        bio: "A student in the Bachelor of Engineering Technology major in Computer Engineering Technology at TUP-Manila. She assisted in setting up the hardware components. She is also one of the paper's editors and assisted in organizing and finalizing the entire paper.",
        initials: "JT",
        gradientFrom: "#059669",
        gradientTo: "#34d399",
        hasPhoto: true,
        photo: "/static/images/avatar_male.png"
    },
    {
        name: "Zharie Ann R. Valero",
        role: "Papers",
        roleClass: "role-papers",
        gender: "female",
        bio: "A student in the Bachelor of Engineering Technology major in Computer Engineering Technology at TUP-Manila. She is one of the paper's editors and assisted in organizing and finalizing the entire paper.",
        initials: "ZV",
        gradientFrom: "#d946ef",
        gradientTo: "#e879f9",
        hasPhoto: true,
        photo: "/static/images/avatar_male.png"
    },
];

const FEATURES = [
    {
        title: "Real-Time Analytics",
        desc: "Live sales trends, revenue tracking, and stock level monitoring updated every few seconds.",
        gradient: "gradient-card-emerald",
        borderColor: "border-emerald-100",
        iconBg: "bg-emerald-500",
        icon: (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2" /></svg>
        ),
    },
    {
        title: "ML Forecasting",
        desc: "Predictive analysis powered by machine learning — sales forecasts, peak hours, and restocking recommendations.",
        gradient: "gradient-card-violet",
        borderColor: "border-violet-100",
        iconBg: "bg-violet-500",
        icon: (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2"><path d="M12 2a7 7 0 017 7c0 2.38-1.19 4.47-3 5.74V17a2 2 0 01-2 2h-4a2 2 0 01-2-2v-2.26C6.19 13.47 5 11.38 5 9a7 7 0 017-7z" /><line x1="9" y1="22" x2="15" y2="22" /></svg>
        ),
    },
    {
        title: "SHA-256 Security",
        desc: "Salted SHA-256 password hashing, CSRF protection, rate limiting, and secure session management.",
        gradient: "gradient-card-cyan",
        borderColor: "border-cyan-100",
        iconBg: "bg-cyan-500",
        icon: (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
        ),
    },
    {
        title: "Cash & RFID Payments",
        desc: "TB74 bill acceptor, WEIYU coin slot, and MFRC522 RFID card reader integration.",
        gradient: "gradient-card-amber",
        borderColor: "border-amber-100",
        iconBg: "bg-amber-500",
        icon: (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2"><rect x="1" y="4" width="22" height="16" rx="2" /><path d="M1 10h22" /></svg>
        ),
    },
    {
        title: "Raspberry Pi 5",
        desc: "Built for Raspberry Pi with GPIO hardware control for motors, solenoids, and sensors.",
        gradient: "gradient-card-rose",
        borderColor: "border-rose-100",
        iconBg: "bg-rose-500",
        icon: (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2"><rect x="4" y="4" width="16" height="16" rx="2" /><rect x="9" y="9" width="6" height="6" /><line x1="9" y1="1" x2="9" y2="4" /><line x1="15" y1="1" x2="15" y2="4" /><line x1="9" y1="20" x2="9" y2="23" /><line x1="15" y1="20" x2="15" y2="23" /></svg>
        ),
    },
    {
        title: "Inventory Management",
        desc: "Full product catalog, stock management, restocking alerts, and multi-slot tray dispensing.",
        gradient: "gradient-card-indigo",
        borderColor: "border-indigo-100",
        iconBg: "bg-indigo-500",
        icon: (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2"><path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z" /></svg>
        ),
    },
];

const PAGES_SHOWCASE = [
    {
        title: "Admin Dashboard",
        desc: "Real-time analytics, sales trends, inventory management, and ML predictions in one unified panel.",
        color: "#6366f1",
        icon: (
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="4" rx="1.5" /><rect x="14" y="10" width="7" height="11" rx="1.5" /><rect x="3" y="13" width="7" height="8" rx="1.5" /></svg>
        ),
    },
    {
        title: "Admin Login",
        desc: "Secure authentication with SHA-256 hashing, CSRF protection, and brute-force rate limiting.",
        color: "#8b5cf6",
        icon: (
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>
        ),
    },
    {
        title: "Customer Kiosk",
        desc: "Touch-friendly product selection interface running on a 7-inch Raspberry Pi touchscreen.",
        color: "#0891b2",
        icon: (
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="5" y="2" width="14" height="20" rx="2" /><line x1="12" y1="18" x2="12.01" y2="18" /></svg>
        ),
    },
    {
        title: "Sales Reports",
        desc: "Exportable CSV reports with daily/monthly sales breakdowns, revenue tracking, and product performance insights.",
        color: "#059669",
        icon: (
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /></svg>
        ),
    },
];

const TECH_STACK = [
    "Python", "Flask", "React 18", "Tailwind CSS", "Chart.js",
    "SQLite", "CustomTkinter", "scikit-learn", "Raspberry Pi 5", "RPi.GPIO",
];

// ═════════════════════════════════════════════════════════════
//   UTILITY HOOKS
// ═════════════════════════════════════════════════════════════

function useScrollReveal() {
    useEffect(() => {
        const revealElements = document.querySelectorAll(".reveal");
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("visible");
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
        );
        revealElements.forEach((el) => observer.observe(el));
        return () => observer.disconnect();
    });
}

// ═════════════════════════════════════════════════════════════
//   COMPONENTS
// ═════════════════════════════════════════════════════════════

// ── Avatar Component ─────────────────────────────────────────
function Avatar({ member, size = 110 }) {
    if (member.hasPhoto) {
        return (
            <img
                src={member.photo}
                alt={member.name}
                className="carousel-avatar"
                style={{ width: size, height: size }}
                loading="lazy"
            />
        );
    }

    // SVG gradient avatar with initials
    const svgSize = size;
    const fontSize = size * 0.36;
    return (
        <div className="carousel-avatar" style={{ width: size, height: size, overflow: "hidden", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <svg width={svgSize} height={svgSize} viewBox={`0 0 ${svgSize} ${svgSize}`}>
                <defs>
                    <linearGradient id={`grad-${member.initials}`} x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor={member.gradientFrom} />
                        <stop offset="100%" stopColor={member.gradientTo} />
                    </linearGradient>
                </defs>
                <circle cx={svgSize / 2} cy={svgSize / 2} r={svgSize / 2} fill={`url(#grad-${member.initials})`} />
                <text
                    x="50%" y="50%"
                    dominantBaseline="central"
                    textAnchor="middle"
                    fill="white"
                    fontWeight="700"
                    fontSize={fontSize}
                    fontFamily="Inter, sans-serif"
                >
                    {member.initials}
                </text>
            </svg>
        </div>
    );
}

// ── Navbar ───────────────────────────────────────────────────
function Navbar() {
    const [scrolled, setScrolled] = useState(false);
    const [mobileOpen, setMobileOpen] = useState(false);

    useEffect(() => {
        const onScroll = () => setScrolled(window.scrollY > 20);
        window.addEventListener("scroll", onScroll, { passive: true });
        return () => window.removeEventListener("scroll", onScroll);
    }, []);

    const navLinks = [
        { label: "Features", href: "#features" },
        { label: "Team", href: "#team" },
        { label: "Pages", href: "#pages" },
    ];

    const handleLinkClick = () => setMobileOpen(false);

    return (
        <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled ? "glass border-b border-white/20 shadow-lg shadow-black/5" : ""}`}>
            <div className="max-w-6xl mx-auto px-4 sm:px-6">
                <div className="flex items-center justify-between py-3 sm:py-4">
                    {/* Logo */}
                    <a href={HOME_URL} className="flex items-center gap-2 sm:gap-3 no-select">
                        <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-indigo-600 flex items-center justify-center shadow-lg flex-shrink-0">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.5">
                                <rect x="2" y="3" width="20" height="18" rx="3" />
                                <path d="M8 7h8M8 11h5" />
                            </svg>
                        </div>
                        <span className={`text-base sm:text-lg font-bold tracking-tight transition-colors duration-300 ${scrolled ? "text-gray-900" : "text-white"}`}>
                            SyntaxError&trade;
                        </span>
                    </a>

                    {/* Desktop links */}
                    <div className="hidden md:flex items-center gap-1">
                        {navLinks.map((link) => (
                            <a
                                key={link.href}
                                href={link.href}
                                className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 hover:bg-white/20 ${scrolled ? "text-gray-700 hover:text-indigo-600 hover:bg-indigo-50" : "text-white/90 hover:text-white"}`}
                            >
                                {link.label}
                            </a>
                        ))}
                        <a
                            href={LOGIN_URL}
                            className="ml-3 px-5 py-2.5 rounded-full text-sm font-semibold bg-indigo-600 text-white hover:bg-indigo-700 active:scale-95 transition-all shadow-lg shadow-indigo-500/25"
                        >
                            Admin Login
                        </a>
                    </div>

                    {/* Mobile hamburger */}
                    <button
                        onClick={() => setMobileOpen(!mobileOpen)}
                        className={`md:hidden w-10 h-10 flex flex-col items-center justify-center gap-1.5 rounded-xl transition-colors ${mobileOpen ? "hamburger-open" : ""} ${scrolled ? "text-gray-700" : "text-white"}`}
                        aria-label="Toggle menu"
                    >
                        <span className={`hamburger-line block w-5 h-0.5 rounded-full transition-all ${scrolled ? "bg-gray-700" : "bg-white"}`}></span>
                        <span className={`hamburger-line block w-5 h-0.5 rounded-full transition-all ${scrolled ? "bg-gray-700" : "bg-white"}`}></span>
                        <span className={`hamburger-line block w-5 h-0.5 rounded-full transition-all ${scrolled ? "bg-gray-700" : "bg-white"}`}></span>
                    </button>
                </div>

                {/* Mobile menu */}
                <div className={`mobile-menu md:hidden ${mobileOpen ? "open" : ""}`}>
                    <div className={`pb-4 flex flex-col gap-1 ${scrolled ? "" : "pt-2"}`}>
                        {navLinks.map((link) => (
                            <a
                                key={link.href}
                                href={link.href}
                                onClick={handleLinkClick}
                                className={`px-4 py-3 rounded-xl text-sm font-medium transition-all ${scrolled ? "text-gray-700 hover:bg-indigo-50 hover:text-indigo-600" : "text-white/90 hover:bg-white/10 hover:text-white"}`}
                            >
                                {link.label}
                            </a>
                        ))}
                        <a
                            href={LOGIN_URL}
                            onClick={handleLinkClick}
                            className="mx-2 mt-2 px-5 py-3 rounded-full text-sm font-semibold bg-indigo-600 text-white hover:bg-indigo-700 active:scale-95 transition-all text-center shadow-lg shadow-indigo-500/25"
                        >
                            Admin Login
                        </a>
                    </div>
                </div>
            </div>
        </nav>
    );
}

// ── Hero Section ─────────────────────────────────────────────
function HeroSection() {
    return (
        <section className="relative min-h-screen flex items-center justify-center px-4 sm:px-6 pt-20 pb-16 gradient-hero text-white overflow-hidden">
            {/* Background decoration */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute -top-40 -right-40 w-80 h-80 bg-white/5 rounded-full blur-3xl"></div>
                <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-white/5 rounded-full blur-3xl"></div>
                <div className="absolute top-1/3 left-1/4 w-64 h-64 bg-indigo-400/10 rounded-full blur-2xl"></div>
            </div>

            <div className="max-w-4xl mx-auto text-center w-full relative z-10">
                {/* Animated icon */}
                <div className="fade-up mb-6 sm:mb-8 float-anim">
                    <div className="inline-flex items-center justify-center w-20 h-20 sm:w-24 sm:h-24 rounded-2xl sm:rounded-3xl bg-white/15 backdrop-blur-sm border border-white/25 shadow-2xl">
                        <svg className="w-10 h-10 sm:w-12 sm:h-12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                            <rect x="2" y="3" width="20" height="18" rx="3" />
                            <path d="M8 7h8M8 11h5" />
                            <circle cx="16" cy="16" r="2" fill="white" stroke="none" />
                        </svg>
                    </div>
                </div>

                <h1 className="fade-up fade-up-d1 text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold tracking-tight leading-tight mb-4 sm:mb-6">
                    Hygiene Vending<br />
                    <span className="bg-clip-text text-transparent bg-gradient-to-r from-white to-indigo-200">
                        Machine System
                    </span>
                </h1>

                <p className="fade-up fade-up-d2 text-base sm:text-lg md:text-xl text-indigo-100 max-w-2xl mx-auto mb-8 sm:mb-10 leading-relaxed px-2">
                    A smart, IoT-powered vending solution with real-time inventory tracking,
                    ML-driven sales forecasting, and a secure admin dashboard.
                </p>

                <div className="fade-up fade-up-d3 flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4 w-full px-4 sm:px-0">
                    <a
                        href={LOGIN_URL}
                        className="w-full sm:w-auto px-8 py-3.5 sm:py-4 rounded-full text-base font-bold bg-white text-indigo-700 hover:bg-indigo-50 active:scale-95 transition-all shadow-xl shadow-black/10 text-center min-h-[48px] flex items-center justify-center"
                    >
                        Open Dashboard &rarr;
                    </a>
                    <a
                        href="#features"
                        className="w-full sm:w-auto px-8 py-3.5 sm:py-4 rounded-full text-base font-semibold bg-white/15 text-white border border-white/30 hover:bg-white/25 active:scale-95 transition-all backdrop-blur-sm text-center min-h-[48px] flex items-center justify-center"
                    >
                        Learn More
                    </a>
                </div>

                {/* Trust badges */}
                <div className="fade-up fade-up-d4 mt-10 sm:mt-16 flex flex-wrap items-center justify-center gap-3 sm:gap-6 md:gap-8 text-xs sm:text-sm text-indigo-200 px-2">
                    <div className="flex items-center gap-1.5 sm:gap-2">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
                        SHA-256 Encrypted
                    </div>
                    <div className="flex items-center gap-1.5 sm:gap-2">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" /></svg>
                        Real-Time Data
                    </div>
                    <div className="flex items-center gap-1.5 sm:gap-2">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2a7 7 0 017 7c0 2.38-1.19 4.47-3 5.74V17a2 2 0 01-2 2h-4a2 2 0 01-2-2v-2.26C6.19 13.47 5 11.38 5 9a7 7 0 017-7z" /></svg>
                        ML Forecasting
                    </div>
                </div>
            </div>

            {/* Scroll indicator */}
            <div className="absolute bottom-8 sm:bottom-10 left-1/2 -translate-x-1/2 animate-bounce hidden sm:block">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round">
                    <path d="M12 5v14M5 12l7 7 7-7" />
                </svg>
            </div>
        </section>
    );
}

// ── Features Section ─────────────────────────────────────────
function FeaturesSection() {
    return (
        <section id="features" className="py-16 sm:py-24 px-4 sm:px-6 bg-white text-gray-900">
            <div className="max-w-6xl mx-auto">
                <div className="text-center mb-10 sm:mb-16 reveal">
                    <p className="text-xs sm:text-sm font-bold text-indigo-600 uppercase tracking-widest mb-2 sm:mb-3">
                        Features
                    </p>
                    <h2 className="text-2xl sm:text-3xl md:text-4xl font-extrabold tracking-tight">
                        Everything you need to manage
                    </h2>
                    <p className="mt-3 text-sm sm:text-base text-gray-500 max-w-xl mx-auto">
                        Powerful tools built into one unified system for seamless vending machine operation.
                    </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
                    {FEATURES.map((f, i) => (
                        <div
                            key={f.title}
                            className={`reveal feature-card ${f.gradient} border ${f.borderColor} rounded-2xl p-5 sm:p-7`}
                            style={{ transitionDelay: `${i * 0.08}s` }}
                        >
                            <div className={`w-11 h-11 sm:w-12 sm:h-12 rounded-xl sm:rounded-2xl ${f.iconBg} flex items-center justify-center mb-4 sm:mb-5 shadow-lg`}>
                                {f.icon}
                            </div>
                            <h3 className="text-base sm:text-lg font-bold mb-1.5 sm:mb-2">{f.title}</h3>
                            <p className="text-sm text-gray-500 leading-relaxed">{f.desc}</p>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}

// ── Team Section (IG Carousel) ───────────────────────────────
function TeamSection() {
    const [current, setCurrent] = useState(0);
    const [isAutoPlaying, setIsAutoPlaying] = useState(true);
    const [touchStart, setTouchStart] = useState(null);
    const [touchEnd, setTouchEnd] = useState(null);
    const [slidesPerView, setSlidesPerView] = useState(1);
    const autoPlayRef = useRef(null);
    const trackRef = useRef(null);

    // Calculate slides per view based on window width
    useEffect(() => {
        const updateSlidesPerView = () => {
            const w = window.innerWidth;
            if (w >= 1024) setSlidesPerView(3);
            else if (w >= 768) setSlidesPerView(2);
            else setSlidesPerView(1);
        };
        updateSlidesPerView();
        window.addEventListener("resize", updateSlidesPerView);
        return () => window.removeEventListener("resize", updateSlidesPerView);
    }, []);

    const maxIndex = Math.max(0, TEAM_MEMBERS.length - slidesPerView);
    const totalDots = maxIndex + 1;

    // Auto-play
    useEffect(() => {
        if (!isAutoPlaying) return;
        autoPlayRef.current = setInterval(() => {
            setCurrent((prev) => (prev >= maxIndex ? 0 : prev + 1));
        }, 4000);
        return () => clearInterval(autoPlayRef.current);
    }, [isAutoPlaying, maxIndex]);

    const goTo = useCallback((index) => {
        setCurrent(Math.max(0, Math.min(index, maxIndex)));
    }, [maxIndex]);

    const goNext = useCallback(() => {
        setCurrent((prev) => (prev >= maxIndex ? 0 : prev + 1));
    }, [maxIndex]);

    const goPrev = useCallback(() => {
        setCurrent((prev) => (prev <= 0 ? maxIndex : prev - 1));
    }, [maxIndex]);

    // Touch handling
    const minSwipeDistance = 50;
    const onTouchStart = (e) => {
        setTouchEnd(null);
        setTouchStart(e.targetTouches[0].clientX);
        setIsAutoPlaying(false);
    };
    const onTouchMove = (e) => setTouchEnd(e.targetTouches[0].clientX);
    const onTouchEnd = () => {
        if (!touchStart || !touchEnd) return;
        const distance = touchStart - touchEnd;
        if (Math.abs(distance) >= minSwipeDistance) {
            if (distance > 0) goNext();
            else goPrev();
        }
        setTimeout(() => setIsAutoPlaying(true), 6000);
    };

    const translateX = -(current * (100 / slidesPerView));

    return (
        <section id="team" className="py-16 sm:py-24 px-4 sm:px-6 bg-gradient-to-b from-gray-50 to-white text-gray-900">
            <div className="max-w-6xl mx-auto">
                <div className="text-center mb-10 sm:mb-16 reveal">
                    <p className="text-xs sm:text-sm font-bold text-indigo-600 uppercase tracking-widest mb-2 sm:mb-3">
                        Our Team
                    </p>
                    <h2 className="text-2xl sm:text-3xl md:text-4xl font-extrabold tracking-tight">
                        Meet Team SyntaxError&trade;
                    </h2>
                    <p className="mt-3 text-sm sm:text-base text-gray-500 max-w-xl mx-auto">
                        A dedicated group of Computer Engineering Technology students from TUP-Manila.
                    </p>
                </div>

                {/* Carousel */}
                <div
                    className="reveal carousel-container no-select touch-action-pan-y"
                    onMouseEnter={() => setIsAutoPlaying(false)}
                    onMouseLeave={() => setIsAutoPlaying(true)}
                    onTouchStart={onTouchStart}
                    onTouchMove={onTouchMove}
                    onTouchEnd={onTouchEnd}
                >
                    {/* Arrows */}
                    <button className="carousel-arrow left" onClick={() => { goPrev(); setIsAutoPlaying(false); setTimeout(() => setIsAutoPlaying(true), 6000); }} aria-label="Previous">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><path d="M15 18l-6-6 6-6" /></svg>
                    </button>
                    <button className="carousel-arrow right" onClick={() => { goNext(); setIsAutoPlaying(false); setTimeout(() => setIsAutoPlaying(true), 6000); }} aria-label="Next">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><path d="M9 18l6-6-6-6" /></svg>
                    </button>

                    {/* Track */}
                    <div
                        ref={trackRef}
                        className="carousel-track"
                        style={{ transform: `translateX(${translateX}%)` }}
                    >
                        {TEAM_MEMBERS.map((member, i) => (
                            <div key={member.name} className="carousel-slide">
                                <div className="carousel-card mx-auto" style={{ maxWidth: 360 }}>
                                    {/* Card header gradient */}
                                    <div
                                        className="h-28 sm:h-32 relative"
                                        style={{ background: `linear-gradient(135deg, ${member.gradientFrom}, ${member.gradientTo})` }}
                                    >
                                        {/* IG-style dots decoration */}
                                        <div className="absolute top-3 right-3 flex gap-1">
                                            <div className="w-1.5 h-1.5 rounded-full bg-white/40"></div>
                                            <div className="w-1.5 h-1.5 rounded-full bg-white/40"></div>
                                            <div className="w-1.5 h-1.5 rounded-full bg-white/40"></div>
                                        </div>
                                    </div>

                                    {/* Avatar (overlapping header) */}
                                    <div className="flex justify-center -mt-14 sm:-mt-16 relative z-10">
                                        <Avatar member={member} size={110} />
                                    </div>

                                    {/* Bio content */}
                                    <div className="px-5 sm:px-6 pt-4 pb-6 text-center">
                                        <h3 className="text-lg sm:text-xl font-bold text-gray-900 mb-1">
                                            {member.name}
                                        </h3>
                                        <div className="flex justify-center mb-3">
                                            <span className={`role-badge ${member.roleClass}`}>
                                                {member.role}
                                            </span>
                                        </div>
                                        <p className="text-xs sm:text-sm text-gray-500 leading-relaxed">
                                            {member.bio}
                                        </p>

                                        {/* Social-style icons */}
                                        <div className="flex justify-center gap-3 mt-4 pt-4 border-t border-gray-100">
                                            <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-400 hover:bg-indigo-50 hover:text-indigo-500 transition-colors cursor-pointer">
                                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" /><polyline points="22,6 12,13 2,6" /></svg>
                                            </div>
                                            <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-400 hover:bg-indigo-50 hover:text-indigo-500 transition-colors cursor-pointer">
                                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" /><rect x="2" y="9" width="4" height="12" /><circle cx="4" cy="4" r="2" /></svg>
                                            </div>
                                            <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-400 hover:bg-indigo-50 hover:text-indigo-500 transition-colors cursor-pointer">
                                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" /></svg>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Dots */}
                <div className="carousel-dots">
                    {Array.from({ length: totalDots }).map((_, i) => (
                        <button
                            key={i}
                            className={`carousel-dot ${current === i ? "active" : ""}`}
                            onClick={() => { goTo(i); setIsAutoPlaying(false); setTimeout(() => setIsAutoPlaying(true), 6000); }}
                            aria-label={`Go to slide ${i + 1}`}
                        />
                    ))}
                </div>
            </div>
        </section>
    );
}

// ── Pages Showcase Section ───────────────────────────────────
function PagesSection() {
    return (
        <section id="pages" className="py-16 sm:py-24 px-4 sm:px-6 bg-white text-gray-900">
            <div className="max-w-6xl mx-auto">
                <div className="text-center mb-10 sm:mb-16 reveal">
                    <p className="text-xs sm:text-sm font-bold text-indigo-600 uppercase tracking-widest mb-2 sm:mb-3">
                        Pages
                    </p>
                    <h2 className="text-2xl sm:text-3xl md:text-4xl font-extrabold tracking-tight">
                        System Overview
                    </h2>
                    <p className="mt-3 text-sm sm:text-base text-gray-500 max-w-xl mx-auto">
                        Explore the different interfaces that power the Hygiene Vending Machine system.
                    </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 sm:gap-6">
                    {PAGES_SHOWCASE.map((page, i) => (
                        <div
                            key={page.title}
                            className="reveal page-card"
                            style={{ transitionDelay: `${i * 0.1}s` }}
                        >
                            {/* Preview area */}
                            <div
                                className="page-card-preview"
                                style={{ background: `linear-gradient(135deg, ${page.color}15, ${page.color}08)` }}
                            >
                                {/* Floating UI mockup */}
                                <div className="relative">
                                    {/* Mock browser frame */}
                                    <div className="w-56 sm:w-64 bg-white rounded-xl shadow-xl overflow-hidden border border-gray-100">
                                        {/* Title bar */}
                                        <div className="h-7 sm:h-8 bg-gray-50 border-b border-gray-100 flex items-center px-3 gap-1.5">
                                            <div className="w-2.5 h-2.5 rounded-full bg-red-400"></div>
                                            <div className="w-2.5 h-2.5 rounded-full bg-amber-400"></div>
                                            <div className="w-2.5 h-2.5 rounded-full bg-green-400"></div>
                                            <div className="ml-2 flex-1 h-4 bg-gray-100 rounded-md"></div>
                                        </div>
                                        {/* Content mockup */}
                                        <div className="p-3 sm:p-4 space-y-2.5">
                                            <div className="flex items-center gap-3">
                                                <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${page.color}20`, color: page.color }}>
                                                    {React.cloneElement(page.icon, { width: 18, height: 18 })}
                                                </div>
                                                <div className="flex-1">
                                                    <div className="h-2.5 rounded-full bg-gray-200 w-3/4"></div>
                                                    <div className="h-2 rounded-full bg-gray-100 w-1/2 mt-1.5"></div>
                                                </div>
                                            </div>
                                            <div className="grid grid-cols-3 gap-1.5">
                                                <div className="h-10 rounded-lg" style={{ background: `${page.color}10` }}></div>
                                                <div className="h-10 rounded-lg" style={{ background: `${page.color}08` }}></div>
                                                <div className="h-10 rounded-lg" style={{ background: `${page.color}10` }}></div>
                                            </div>
                                            <div className="h-14 rounded-lg" style={{ background: `${page.color}06` }}></div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Info */}
                            <div className="px-5 sm:px-6 py-5 sm:py-6">
                                <div className="flex items-center gap-3 mb-2">
                                    <div
                                        className="w-9 h-9 rounded-xl flex items-center justify-center"
                                        style={{ background: `${page.color}15`, color: page.color }}
                                    >
                                        {React.cloneElement(page.icon, { width: 20, height: 20 })}
                                    </div>
                                    <h3 className="text-base sm:text-lg font-bold">{page.title}</h3>
                                </div>
                                <p className="text-sm text-gray-500 leading-relaxed">{page.desc}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}

// ── Tech Stack Section ───────────────────────────────────────
function TechStackSection() {
    return (
        <section className="py-14 sm:py-20 px-4 sm:px-6 bg-gray-50 text-gray-900">
            <div className="max-w-4xl mx-auto text-center reveal">
                <p className="text-xs sm:text-sm font-bold text-indigo-600 uppercase tracking-widest mb-2 sm:mb-3">Built With</p>
                <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight mb-8 sm:mb-12">Modern Technology Stack</h2>
                <div className="flex flex-wrap items-center justify-center gap-2.5 sm:gap-3">
                    {TECH_STACK.map((tech, i) => (
                        <span
                            key={tech}
                            className="tech-pill px-4 sm:px-5 py-2 sm:py-2.5 rounded-full bg-white border border-gray-200 text-xs sm:text-sm font-semibold shadow-sm cursor-default"
                            style={{ animationDelay: `${i * 0.05}s` }}
                        >
                            {tech}
                        </span>
                    ))}
                </div>
            </div>
        </section>
    );
}

// ── Footer ───────────────────────────────────────────────────
function Footer() {
    return (
        <footer className="py-10 sm:py-14 px-4 sm:px-6 bg-gray-900 text-gray-400">
            <div className="max-w-6xl mx-auto">
                <div className="flex flex-col md:flex-row items-center justify-between gap-6 md:gap-0">
                    {/* Brand */}
                    <div className="text-center md:text-left">
                        <div className="flex items-center justify-center md:justify-start gap-2 mb-2">
                            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.5">
                                    <rect x="2" y="3" width="20" height="18" rx="3" />
                                    <path d="M8 7h8M8 11h5" />
                                </svg>
                            </div>
                            <span className="text-white font-bold text-sm">SyntaxError&trade;</span>
                        </div>
                        <p className="text-xs text-gray-500">Hygiene Vending Machine — Capstone Project</p>
                    </div>

                    {/* Links */}
                    <div className="flex items-center gap-6 text-sm">
                        <a href="#features" className="hover:text-white transition-colors">Features</a>
                        <a href="#team" className="hover:text-white transition-colors">Team</a>
                        <a href="#pages" className="hover:text-white transition-colors">Pages</a>
                        <a href={LOGIN_URL} className="hover:text-white transition-colors">Admin</a>
                    </div>

                    {/* Info */}
                    <div className="text-center md:text-right text-xs text-gray-500">
                        <p>Secured with SHA-256</p>
                        <p>Built with Python &amp; React</p>
                    </div>
                </div>

                <div className="mt-8 pt-6 border-t border-gray-800 text-center text-xs text-gray-600">
                    &copy; {new Date().getFullYear()} SyntaxError&trade; — Technological University of the Philippines-Manila
                </div>
            </div>
        </footer>
    );
}

// ═════════════════════════════════════════════════════════════
//   APP ROOT
// ═════════════════════════════════════════════════════════════

function App() {
    useScrollReveal();

    return (
        <React.Fragment>
            <Navbar />
            <HeroSection />
            <FeaturesSection />
            <TeamSection />
            <PagesSection />
            <TechStackSection />
            <Footer />
        </React.Fragment>
    );
}

// ── Mount ────────────────────────────────────────────────────
ReactDOM.createRoot(document.getElementById("root")).render(<App />);
