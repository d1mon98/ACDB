// Preset location lists for common facility types.
// One click fills the Locations table with typical area/room codes for that
// facility.  If locations from a different preset already exist a warning is
// shown before adding.

import { useState } from "react";
import { api } from "../api";

interface PresetLocation {
  location_code: string;
  building: string;
  area: string;
  process_system: string;
  indoor_outdoor: string;
  description: string;
}

interface Preset {
  label: string;
  tag: string; // short identifier used to detect conflicts
  facilityLabel: string; // value written to typical_facility column
  locations: PresetLocation[];
}

const PRESETS: Preset[] = [
  {
    label: "Water Treatment Plant",
    tag: "WTP",
    facilityLabel: "Water Treatment Plant",
    locations: [
      { location_code: "INTAKE",   building: "Intake Structure",    area: "Raw Water Intake",       process_system: "Intake",        indoor_outdoor: "OUTDOOR", description: "Raw water intake screens and pumps" },
      { location_code: "CHEM-FD",  building: "Chemical Feed Bldg",  area: "Chemical Storage",       process_system: "Chemical Feed", indoor_outdoor: "INDOOR",  description: "Alum, polymer, chlorine storage and dosing" },
      { location_code: "FLOC",     building: "Treatment Bldg",      area: "Flocculation Basin",     process_system: "Coagulation",   indoor_outdoor: "OUTDOOR", description: "Rapid mix and flocculation basins" },
      { location_code: "SED",      building: "Treatment Bldg",      area: "Sedimentation Basin",    process_system: "Sedimentation", indoor_outdoor: "OUTDOOR", description: "Primary clarifiers" },
      { location_code: "FILTER",   building: "Filter Bldg",         area: "Filtration",             process_system: "Filtration",    indoor_outdoor: "INDOOR",  description: "Gravity sand / anthracite filters" },
      { location_code: "DISINFECT",building: "Disinfection Bldg",   area: "Chlorination",           process_system: "Disinfection",  indoor_outdoor: "INDOOR",  description: "Chlorine contact chamber and dosing" },
      { location_code: "CLEARWELL",building: "Clearwell",           area: "Finished Water Storage", process_system: "Storage",       indoor_outdoor: "OUTDOOR", description: "Finished water ground-level storage" },
      { location_code: "HIGHSERV", building: "High-Service Pump Stn",area: "High-Service Pumping",  process_system: "Distribution",  indoor_outdoor: "INDOOR",  description: "High-service pumps to distribution system" },
      { location_code: "BACKWASH", building: "Filter Bldg",         area: "Backwash Recovery",      process_system: "Filtration",    indoor_outdoor: "INDOOR",  description: "Backwash waste holding and recovery" },
      { location_code: "SLUDGE",   building: "Solids Handling Bldg",area: "Sludge Dewatering",      process_system: "Solids",        indoor_outdoor: "INDOOR",  description: "Sludge thickening and dewatering" },
      { location_code: "MCC-MAIN", building: "Electrical Bldg",     area: "Main MCC Room",          process_system: "Electrical",    indoor_outdoor: "INDOOR",  description: "Main motor control center and switchgear" },
      { location_code: "SCADA",    building: "Electrical Bldg",     area: "Control Room",           process_system: "Instrumentation",indoor_outdoor: "INDOOR", description: "SCADA / operator workstation" },
      { location_code: "MAINT",    building: "Maintenance Bldg",    area: "Workshop",               process_system: "Maintenance",   indoor_outdoor: "INDOOR",  description: "Maintenance shop and equipment storage" },
      { location_code: "YARD",     building: "Site",                area: "Plant Yard",             process_system: "Site",          indoor_outdoor: "OUTDOOR", description: "General outdoor yard area" },
    ],
  },
  {
    label: "Cement Plant",
    tag: "CEMENT",
    facilityLabel: "Cement Plant",
    locations: [
      { location_code: "QUARRY",   building: "Quarry",              area: "Raw Material Extraction", process_system: "Mining",       indoor_outdoor: "OUTDOOR", description: "Limestone quarry and primary crusher" },
      { location_code: "CRUSH",    building: "Crushing Bldg",       area: "Primary Crushing",        process_system: "Crushing",     indoor_outdoor: "INDOOR",  description: "Jaw / impact crushers" },
      { location_code: "RAWMILL",  building: "Raw Mill Bldg",       area: "Raw Grinding",            process_system: "Raw Milling",  indoor_outdoor: "INDOOR",  description: "Vertical roller mill — raw meal preparation" },
      { location_code: "BLENDING", building: "Blending Silo",       area: "Raw Meal Blending",       process_system: "Blending",     indoor_outdoor: "INDOOR",  description: "Raw meal homogenisation silos" },
      { location_code: "KILN",     building: "Kiln Building",       area: "Rotary Kiln",             process_system: "Pyroprocess",  indoor_outdoor: "INDOOR",  description: "Pre-heater tower, calciner and rotary kiln" },
      { location_code: "COOLER",   building: "Kiln Building",       area: "Clinker Cooler",          process_system: "Pyroprocess",  indoor_outdoor: "INDOOR",  description: "Grate cooler and clinker conveying" },
      { location_code: "CLKRSILO", building: "Clinker Silo",        area: "Clinker Storage",         process_system: "Storage",      indoor_outdoor: "INDOOR",  description: "Clinker intermediate storage silo" },
      { location_code: "CEMENTMILL",building:"Cement Mill Bldg",    area: "Finish Grinding",         process_system: "Cement Milling",indoor_outdoor: "INDOOR", description: "Ball mill / roller press for finish grinding" },
      { location_code: "CEMENTSILO",building:"Cement Silo",         area: "Cement Storage",          process_system: "Storage",      indoor_outdoor: "INDOOR",  description: "Bulk cement storage silos" },
      { location_code: "PACKING",  building: "Packing House",       area: "Bagging & Dispatch",      process_system: "Dispatch",     indoor_outdoor: "INDOOR",  description: "Rotary packer and truck / rail loading" },
      { location_code: "RAWCOAL",  building: "Coal Storage",        area: "Coal Yard",               process_system: "Fuel",         indoor_outdoor: "OUTDOOR", description: "Coal stockpile and reclaim" },
      { location_code: "COALMILL", building: "Coal Mill Bldg",      area: "Coal Grinding",           process_system: "Fuel",         indoor_outdoor: "INDOOR",  description: "Coal mill and bag filter" },
      { location_code: "COMPAIR",  building: "Compressor House",    area: "Compressed Air",          process_system: "Utilities",    indoor_outdoor: "INDOOR",  description: "Instrument and plant air compressors" },
      { location_code: "MCC-MAIN", building: "Main Electrical Bldg",area: "Main MCC / Switchgear",  process_system: "Electrical",   indoor_outdoor: "INDOOR",  description: "11 kV / LV switchgear and MCC" },
      { location_code: "SCADA",    building: "Main Electrical Bldg",area: "Central Control Room",    process_system: "Instrumentation",indoor_outdoor: "INDOOR","description": "DCS / SCADA central control" },
      { location_code: "YARD",     building: "Site",                area: "Plant Yard",              process_system: "Site",         indoor_outdoor: "OUTDOOR", description: "General outdoor yard and roads" },
    ],
  },
  {
    label: "Manufacturing / Industrial",
    tag: "MFG",
    facilityLabel: "Manufacturing / Industrial",
    locations: [
      { location_code: "RECEIVING", building: "Warehouse",          area: "Receiving Dock",          process_system: "Logistics",    indoor_outdoor: "INDOOR",  description: "Incoming materials receiving" },
      { location_code: "RAW-STORE", building: "Warehouse",          area: "Raw Material Storage",    process_system: "Logistics",    indoor_outdoor: "INDOOR",  description: "Raw material racks and staging" },
      { location_code: "PROD-A",   building: "Production Bldg A",   area: "Production Line A",       process_system: "Production",   indoor_outdoor: "INDOOR",  description: "Main production line A" },
      { location_code: "PROD-B",   building: "Production Bldg B",   area: "Production Line B",       process_system: "Production",   indoor_outdoor: "INDOOR",  description: "Production line B" },
      { location_code: "ASSEMBLY", building: "Assembly Hall",        area: "Assembly",                process_system: "Assembly",     indoor_outdoor: "INDOOR",  description: "Component assembly and testing" },
      { location_code: "PAINT",    building: "Paint Shop",           area: "Surface Finishing",       process_system: "Finishing",    indoor_outdoor: "INDOOR",  description: "Paint booths and curing ovens" },
      { location_code: "QA-LAB",   building: "QA Building",          area: "Quality Lab",             process_system: "Quality",      indoor_outdoor: "INDOOR",  description: "Quality assurance and testing lab" },
      { location_code: "COMPAIR",  building: "Utility Room",         area: "Compressed Air",          process_system: "Utilities",    indoor_outdoor: "INDOOR",  description: "Air compressors and dryers" },
      { location_code: "CHILLER",  building: "Utility Room",         area: "HVAC / Cooling",          process_system: "Utilities",    indoor_outdoor: "INDOOR",  description: "Process chillers and cooling towers" },
      { location_code: "SHIPPING", building: "Warehouse",            area: "Shipping Dock",           process_system: "Logistics",    indoor_outdoor: "INDOOR",  description: "Finished goods staging and outbound shipping" },
      { location_code: "MCC-MAIN", building: "Electrical Room",      area: "Main MCC",                process_system: "Electrical",   indoor_outdoor: "INDOOR",  description: "Main motor control centre and switchgear" },
      { location_code: "SCADA",    building: "Electrical Room",      area: "Control Room",            process_system: "Instrumentation",indoor_outdoor: "INDOOR","description": "PLC / SCADA control room" },
      { location_code: "MAINT",    building: "Maintenance Shop",     area: "Maintenance",             process_system: "Maintenance",  indoor_outdoor: "INDOOR",  description: "Maintenance workshop and spares store" },
      { location_code: "YARD",     building: "Site",                 area: "Plant Yard",              process_system: "Site",         indoor_outdoor: "OUTDOOR", description: "External yard, parking and roads" },
    ],
  },
];

// Maps facilityLabel values back to preset tags for conflict detection.
const FACILITY_TO_TAG: Record<string, string> = {
  "Water Treatment Plant": "WTP",
  "Cement Plant": "CEMENT",
  "Manufacturing / Industrial": "MFG",
};

interface Props {
  projectId: number | null;
  onAdded: () => void;
}

export default function LocationPresets({ projectId, onAdded }: Props) {
  const [busy, setBusy] = useState(false);
  const [lastApplied, setLastApplied] = useState<string | null>(null);
  const [pendingPreset, setPendingPreset] = useState<Preset | null>(null);
  const [existingTag, setExistingTag] = useState<string | null>(null);

  async function detectExistingTag(): Promise<string | null> {
    if (!projectId) return null;
    const res = await api.list("project-locations", { project_id: projectId, limit: 500 });
    for (const row of res.items) {
      const facility: string = row.typical_facility ?? "";
      const tag = FACILITY_TO_TAG[facility];
      if (tag) return tag;
    }
    return null;
  }

  async function applyPreset(preset: Preset, force = false) {
    if (!projectId) return;
    setBusy(true);
    try {
      if (!force) {
        const tag = await detectExistingTag();
        if (tag && tag !== preset.tag) {
          setExistingTag(tag);
          setPendingPreset(preset);
          return;
        }
      }
      for (const loc of preset.locations) {
        try {
          await api.create("project-locations", {
            ...loc,
            project_id: projectId,
            typical_facility: preset.facilityLabel,
          });
        } catch (e: any) {
          // Skip locations whose code already exists in this project (UNIQUE constraint).
          const msg: string = e?.message ?? "";
          if (!msg.includes("unique") && !msg.includes("UNIQUE") && !msg.includes("already exists")) {
            throw e; // re-throw unexpected errors
          }
        }
      }
      setLastApplied(preset.tag);
      setPendingPreset(null);
      setExistingTag(null);
      onAdded();
    } catch (e: any) {
      alert(e?.message ?? String(e));
    } finally {
      setBusy(false);
    }
  }

  const existingLabel = existingTag
    ? (PRESETS.find((p) => p.tag === existingTag)?.label ?? existingTag)
    : null;

  return (
    <div className="location-presets">
      <div className="location-presets-header">
        <span className="section-label" style={{ margin: 0 }}>Facility presets</span>
        <span className="muted" style={{ fontSize: 12 }}>
          Click a button to insert typical locations for that facility type.
        </span>
      </div>
      <div className="location-presets-buttons">
        {PRESETS.map((preset) => (
          <button
            key={preset.tag}
            className={"btn btn-sm" + (lastApplied === preset.tag ? " btn-primary" : "")}
            disabled={busy}
            onClick={() => applyPreset(preset)}
            title={`Add ${preset.locations.length} typical locations for a ${preset.label}`}
          >
            + {preset.label}
          </button>
        ))}
      </div>

      {pendingPreset && existingTag && (
        <div className="modal-overlay" onMouseDown={(e) => { if (e.target === e.currentTarget) setPendingPreset(null); }}>
          <div className="modal modal-sm" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Mixed facility locations</h3>
              <button className="btn-icon" onClick={() => setPendingPreset(null)}>×</button>
            </div>
            <div className="modal-body">
              <p style={{ margin: "0 0 12px" }}>
                This project already has locations from the{" "}
                <strong>{existingLabel}</strong> preset. Adding{" "}
                <strong>{pendingPreset.label}</strong> locations will mix two
                different facility types in the same list.
              </p>
              <p style={{ margin: 0 }}>Do you want to add them anyway?</p>
            </div>
            <div className="modal-footer">
              <button className="btn" onClick={() => setPendingPreset(null)}>
                Cancel
              </button>
              <button
                className="btn btn-primary"
                disabled={busy}
                onClick={() => applyPreset(pendingPreset, true)}
              >
                {busy ? "Adding…" : "Add anyway"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
