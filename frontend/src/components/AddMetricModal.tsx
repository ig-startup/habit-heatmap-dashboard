import { useState } from "react";

import { createMetric, type Unit } from "../api";

export default function AddMetricModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const [name, setName] = useState("");
  const [icon, setIcon] = useState("📊");
  const [unit, setUnit] = useState<Unit>("count");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await createMetric({ name: name.trim(), icon, unit });
      onCreated();
      onClose();
    } catch {
      setError("Не удалось создать метрику");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50">
      <form
        onSubmit={handleSubmit}
        className="bg-surface border border-border rounded-lg p-6 w-full max-w-sm flex flex-col gap-4"
      >
        <h2 className="font-mono text-sm text-text">Новая метрика</h2>

        <label className="flex flex-col gap-1 text-xs text-muted font-mono">
          Иконка (emoji)
          <input
            value={icon}
            onChange={(e) => setIcon(e.target.value)}
            maxLength={4}
            className="bg-bg border border-border rounded px-3 py-2 text-text text-sm"
          />
        </label>

        <label className="flex flex-col gap-1 text-xs text-muted font-mono">
          Название
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="bg-bg border border-border rounded px-3 py-2 text-text text-sm"
          />
        </label>

        <label className="flex flex-col gap-1 text-xs text-muted font-mono">
          Тип значения
          <select
            value={unit}
            onChange={(e) => setUnit(e.target.value as Unit)}
            className="bg-bg border border-border rounded px-3 py-2 text-text text-sm"
          >
            <option value="count">Число (count)</option>
            <option value="duration">Длительность (мин)</option>
            <option value="boolean">Отметка (да/нет)</option>
          </select>
        </label>

        {error && <p className="text-xs text-red-400 font-mono">{error}</p>}

        <div className="flex justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 text-sm text-muted hover:text-text font-mono"
          >
            Отмена
          </button>
          <button
            type="submit"
            disabled={submitting}
            className="px-3 py-1.5 text-sm bg-accent/20 border border-accent text-accent rounded font-mono disabled:opacity-50"
          >
            {submitting ? "Создаю..." : "Создать"}
          </button>
        </div>
      </form>
    </div>
  );
}
