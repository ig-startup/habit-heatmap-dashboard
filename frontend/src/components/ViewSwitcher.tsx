const VIEWS = [
  { key: "single", label: "Single", enabled: false },
  { key: "weekly", label: "Weekly", enabled: false },
  { key: "yearly", label: "Yearly", enabled: true },
] as const;

export default function ViewSwitcher({ active }: { active: (typeof VIEWS)[number]["key"] }) {
  return (
    <div className="flex gap-1 font-mono text-sm">
      {VIEWS.map((view) => (
        <button
          key={view.key}
          disabled={!view.enabled}
          title={view.enabled ? undefined : "скоро"}
          className={[
            "px-3 py-1.5 border-b transition-colors",
            view.key === active
              ? "text-text border-text"
              : view.enabled
                ? "text-muted border-transparent hover:text-text"
                : "text-border border-transparent cursor-not-allowed",
          ].join(" ")}
        >
          {view.label}
        </button>
      ))}
    </div>
  );
}
