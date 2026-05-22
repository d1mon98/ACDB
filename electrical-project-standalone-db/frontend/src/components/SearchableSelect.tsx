// A small searchable single-select combobox.
//
// Used for every foreign-key field and for the catalog picker in the merge
// form.  Kept dependency-free on purpose -- it is just an input with a
// filtered dropdown.

import { useEffect, useRef, useState } from "react";

export interface Option {
  value: number;
  label: string;
}

interface Props {
  options: Option[];
  value: number | null;
  onChange: (value: number | null) => void;
  placeholder?: string;
  disabled?: boolean;
}

export default function SearchableSelect({
  options,
  value,
  onChange,
  placeholder,
  disabled,
}: Props) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const ref = useRef<HTMLDivElement>(null);

  const selected = options.find((o) => o.value === value) ?? null;

  // Close the dropdown when the user clicks elsewhere.
  useEffect(() => {
    function onMouseDown(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
        setQuery("");
      }
    }
    document.addEventListener("mousedown", onMouseDown);
    return () => document.removeEventListener("mousedown", onMouseDown);
  }, []);

  const filtered = options.filter((o) =>
    o.label.toLowerCase().includes(query.toLowerCase()),
  );

  function pick(v: number | null) {
    onChange(v);
    setOpen(false);
    setQuery("");
  }

  return (
    <div className="ss" ref={ref}>
      <input
        className="input"
        disabled={disabled}
        value={open ? query : selected?.label ?? ""}
        placeholder={placeholder ?? "Select..."}
        onFocus={() => !disabled && setOpen(true)}
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
        }}
      />
      {selected && !open && !disabled && (
        <button
          type="button"
          className="ss-clear"
          title="Clear"
          onClick={() => pick(null)}
        >
          &times;
        </button>
      )}
      {open && (
        <div className="ss-menu">
          <div className="ss-option ss-none" onClick={() => pick(null)}>
            (none)
          </div>
          {filtered.map((o) => (
            <div
              key={o.value}
              className={"ss-option" + (o.value === value ? " ss-active" : "")}
              onClick={() => pick(o.value)}
            >
              {o.label}
            </div>
          ))}
          {filtered.length === 0 && (
            <div className="ss-option ss-empty">No matches</div>
          )}
        </div>
      )}
    </div>
  );
}
