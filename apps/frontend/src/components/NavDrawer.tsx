import { useEffect, useRef } from "react";

interface NavDrawerProps {
  open: boolean;
  onClose: () => void;
  currentPath: string;
}

const FOCUSABLE =
  'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])';

export default function NavDrawer({ open, onClose, currentPath }: NavDrawerProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;

    const previousFocus = document.activeElement as HTMLElement | null;
    closeButtonRef.current?.focus();

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
        return;
      }
      if (e.key !== "Tab" || !panelRef.current) return;

      const focusables = Array.from(
        panelRef.current.querySelectorAll<HTMLElement>(FOCUSABLE),
      ).filter((el) => el.offsetParent !== null);

      if (focusables.length === 0) return;

      const first = focusables[0];
      const last = focusables[focusables.length - 1];

      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };

    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      previousFocus?.focus();
    };
  }, [open, onClose]);

  if (!open) return null;

  const linkClass = (href: string) => {
    const isActive =
      href === "/"
        ? currentPath === "/"
        : currentPath === href || currentPath.startsWith(`${href}/`);
    return `block px-4 py-3 text-sm font-medium rounded-lg transition-colors min-h-11 flex items-center ${
      isActive ? "bg-[#44312a] text-white" : "text-[#1a1a1a] hover:bg-[#faf9f7]"
    }`;
  };

  return (
    <>
      <div
        className="fixed inset-0 z-40 bg-black/30 md:hidden"
        onClick={onClose}
        aria-hidden="true"
      />
      <div
        ref={panelRef}
        id="nav-drawer"
        role="dialog"
        aria-modal="true"
        aria-label="Navigation menu"
        className="fixed inset-y-0 left-0 z-50 w-72 max-w-[85vw] bg-white border-r border-[#e5e2de] shadow-xl md:hidden flex flex-col"
      >
        <div className="flex items-center justify-between px-4 py-3 border-b border-[#e5e2de]">
          <span className="text-sm font-semibold text-[#1a1a1a]">Menu</span>
          <button
            ref={closeButtonRef}
            type="button"
            onClick={onClose}
            aria-label="Close navigation menu"
            className="min-h-11 min-w-11 flex items-center justify-center rounded-lg text-[#6b7280] hover:bg-[#faf9f7]"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <nav className="flex flex-col gap-1 p-3">
          <a href="/" className={linkClass("/")} onClick={onClose}>
            Home
          </a>
          <a href="/chat" className={linkClass("/chat")} onClick={onClose}>
            Chat
          </a>
          <a
            href="/"
            className="block px-4 py-3 text-sm font-medium text-white bg-[#44312a] hover:bg-[#5a4238] rounded-lg transition-colors min-h-11 flex items-center justify-center mt-2"
            onClick={onClose}
          >
            + New Research
          </a>
        </nav>
      </div>
    </>
  );
}
