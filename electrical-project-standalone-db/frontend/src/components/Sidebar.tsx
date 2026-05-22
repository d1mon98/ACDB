// Left-hand navigation: the Database Browser and Dashboard, then the chapters
// grouped into the two table classes -- General Catalogs (Class A) and Project
// Tables (Class B).

import { CATALOG_CHAPTERS, PROJECT_CHAPTERS } from "../chapters";

interface Props {
  active: string; // chapter key, "dashboard", or "database"
  onSelect: (key: string) => void;
}

export default function Sidebar({ active, onSelect }: Props) {
  function item(key: string, label: string) {
    return (
      <button
        key={key}
        className={"nav-item" + (active === key ? " nav-active" : "")}
        onClick={() => onSelect(key)}
      >
        {label}
      </button>
    );
  }

  return (
    <nav className="sidebar">
      {item("database", "Database Browser")}
      {item("dashboard", "Dashboard")}

      <div className="nav-group">General Catalogs</div>
      {CATALOG_CHAPTERS.map((c) => item(c.key, c.title))}

      <div className="nav-group">Project Tables</div>
      {PROJECT_CHAPTERS.map((c) => item(c.key, c.title))}
    </nav>
  );
}
