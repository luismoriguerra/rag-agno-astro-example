import { useEffect, useState } from "react";

interface UserProfile {
  sub: string;
  name: string | null;
  email: string | null;
  picture: string | null;
}

function getInitials(name: string | null, email: string | null, sub: string): string {
  if (name) {
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return parts[0].substring(0, 2).toUpperCase();
  }
  if (email) return email.substring(0, 2).toUpperCase();
  return sub.substring(0, 2).toUpperCase();
}

export default function Navbar() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);

  const currentPath = typeof window !== "undefined" ? window.location.pathname : "/";

  useEffect(() => {
    fetch("/api/auth/me", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => { if (data) setUser(data as UserProfile); })
      .catch(() => {});
  }, []);

  const navLink = (href: string, label: string) => {
    const isActive = currentPath === href || currentPath.startsWith(href + "/");
    return (
      <a
        href={href}
        className={`text-sm font-medium transition-colors ${
          isActive
            ? "text-[#1a1a1a]"
            : "text-[#6b7280] hover:text-[#1a1a1a]"
        }`}
      >
        {label}
      </a>
    );
  };

  return (
    <nav className="flex items-center justify-between px-6 py-3 bg-white border-b border-[#e5e2de]">
      <div className="flex items-center gap-6">
        <a href="/" className="text-lg font-semibold text-[#1a1a1a] tracking-tight">
          Lumen
        </a>
        {navLink("/", "Home")}
        {navLink("/chat", "Chat")}
        <a
          href="/"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-white bg-[#44312a] px-3 py-1.5 rounded-lg hover:bg-[#5a4238] transition-colors"
        >
          + New Research
        </a>
      </div>

      <div className="relative flex items-center gap-3">
        {user && (
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="flex items-center gap-2 hover:opacity-80 transition-opacity"
          >
            {user.picture ? (
              <img
                src={user.picture}
                alt=""
                className="w-8 h-8 rounded-full object-cover"
              />
            ) : (
              <div className="w-8 h-8 rounded-full bg-[#44312a] text-white flex items-center justify-center text-xs font-semibold">
                {getInitials(user.name, user.email, user.sub)}
              </div>
            )}
            <span className="text-sm text-[#1a1a1a] hidden sm:inline">
              {user.name || user.email || "User"}
            </span>
          </button>
        )}

        {menuOpen && (
          <>
            <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
            <div className="absolute right-0 top-full mt-1 z-20 bg-white border border-[#e5e2de] rounded-lg shadow-lg py-1 min-w-[160px]">
              {user?.email && (
                <div className="px-3 py-2 text-xs text-[#6b7280] border-b border-[#e5e2de] truncate">
                  {user.email}
                </div>
              )}
              <a
                href="/api/auth/logout"
                className="block px-3 py-2 text-sm text-[#1a1a1a] hover:bg-[#faf9f7] transition-colors"
              >
                Sign out
              </a>
            </div>
          </>
        )}
      </div>
    </nav>
  );
}
