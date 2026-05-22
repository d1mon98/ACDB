using System;
using System.Collections.Generic;
using Autodesk.AutoCAD.ApplicationServices;
using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.AutoCAD.EditorInput;
using Autodesk.AutoCAD.Geometry;
using Autodesk.AutoCAD.Runtime;
using AcDbPlugin.Data;

namespace AcDbPlugin.Integration
{
    /// <summary>
    /// Links AutoCAD block references to equipment records in the SQLite database.
    ///
    /// HOW THE LINK IS STORED
    /// -----------------------
    /// The database is the single source of truth. Only the primary key is persisted
    /// on the drawing object — never the field values. Specifically:
    ///
    ///   XData RegApp : "EPDB_LINK"
    ///   Code 1071    : equip_id (32-bit integer)
    ///
    /// Block attributes are a display cache only. "Refresh" means re-reading the DB
    /// row by equip_id and rewriting the attribute strings.
    ///
    /// ATTRIBUTE MAPPING
    /// -----------------
    /// AttrMap defines the single authoritative mapping between attribute TAG names
    /// and Equipment properties. Extend this dictionary to add new fields; the rest
    /// of the logic adapts automatically.
    ///
    /// SYNC / REFRESH
    /// --------------
    /// RefreshAll() iterates model-space block references, finds every one carrying
    /// EPDB_LINK XData, reads its equip_id, queries the DB, and rewrites attribute
    /// values. If the equip_id no longer exists the block is flagged as STALE.
    ///
    /// The optional background poller (MainViewModel.PollerEnabled) checks the DB
    /// file's last-write-time on a configurable interval and calls RefreshAll when
    /// the file has changed. This is POLLING — AutoCAD has no push mechanism for
    /// external SQLite file changes.
    /// </summary>
    public static class LinkedBlockService
    {
        public const string RegAppName = "EPDB_LINK";

        // ── Single authoritative attribute-tag → Equipment-property mapping ──
        // Keys must be valid AutoCAD attribute tag strings (no spaces, ≤255 chars).
        public static readonly IReadOnlyDictionary<string, Func<Equipment, string>> AttrMap =
            new Dictionary<string, Func<Equipment, string>>(StringComparer.OrdinalIgnoreCase)
            {
                ["TAG"]            = e => e.Tag,
                ["NAME"]           = e => e.Name,
                ["BUS_VOLTAGE_V"]  = e => e.BusVoltageV?.ToString()   ?? "",
                ["RATED_CURRENT_A"]= e => e.RatedCurrentA?.ToString() ?? "",
                ["IC_RATING_KA"]   = e => e.IcRatingKa?.ToString()    ?? "",
                ["FED_FROM_TAG"]   = e => e.FedFromTag,
                ["BREAKER_TRIP_A"] = e => e.BreakerTripA?.ToString()  ?? "",
                ["DRAWING_REF"]    = e => e.DrawingRef,
                ["SHEET_NUMBER"]   = e => e.SheetNumber,
                ["ONE_LINE_REF"]   = e => e.OneLineRef,
                ["STATUS"]         = e => e.Status,
            };

        // ------------------------------------------------------------------ //
        // Public entry points
        // ------------------------------------------------------------------ //

        /// <summary>
        /// Called from the palette "Link to Block" button.
        /// Prompts the user to select an object, then links it to <paramref name="equip"/>.
        /// </summary>
        public static void LinkObject(Equipment equip, DbContext db)
        {
            var doc = Application.DocumentManager.MdiActiveDocument;
            if (doc == null) return;
            var ed = doc.Editor;

            var selRes = ed.GetEntity(
                $"\nSelect object to link to '{equip.Tag}' (block ref or loose geometry): ");
            if (selRes.Status != PromptStatus.OK) return;

            using var docLock = doc.LockDocument();
            using var tr = doc.Database.TransactionManager.StartTransaction();
            try
            {
                var ent = tr.GetObject(selRes.ObjectId, OpenMode.ForRead);

                if (ent is BlockReference bref)
                {
                    // Use the existing block reference directly.
                    bref.UpgradeOpen();
                    var btr = (BlockTableRecord)tr.GetObject(
                        bref.BlockTableRecord, OpenMode.ForWrite);
                    EnsureAttributeDefs(btr, tr);
                    InitAttributeRefs(bref, tr);
                    WriteXData(bref, equip.EquipId, tr, doc.Database);
                    FillAttributes(bref, equip, tr);
                }
                else if (ent is Entity looseEnt)
                {
                    // Wrap the loose geometry in a new named block.
                    var brefId = CreateBlockFromEntity(looseEnt, equip, tr, doc.Database);
                    var newBref = (BlockReference)tr.GetObject(brefId, OpenMode.ForWrite);
                    WriteXData(newBref, equip.EquipId, tr, doc.Database);
                    FillAttributes(newBref, equip, tr);
                }
                else
                {
                    ed.WriteMessage("\nSelected object cannot be linked.");
                    tr.Abort();
                    return;
                }

                tr.Commit();
                ed.WriteMessage(
                    $"\nLinked to equipment '{equip.Tag}' (equip_id={equip.EquipId}).");
            }
            catch (System.Exception ex)
            {
                tr.Abort();
                ed.WriteMessage($"\nLink error: {ex.Message}");
            }
        }

        /// <summary>
        /// Removes the EPDB_LINK XData from a user-selected block reference.
        /// </summary>
        public static void UnlinkObject()
        {
            var doc = Application.DocumentManager.MdiActiveDocument;
            if (doc == null) return;
            var ed = doc.Editor;

            var selRes = ed.GetEntity("\nSelect a linked block reference to unlink: ");
            if (selRes.Status != PromptStatus.OK) return;

            using var docLock = doc.LockDocument();
            using var tr = doc.Database.TransactionManager.StartTransaction();
            try
            {
                var ent = tr.GetObject(selRes.ObjectId, OpenMode.ForRead);
                if (ent is not BlockReference bref)
                {
                    ed.WriteMessage("\nSelected entity is not a block reference.");
                    tr.Abort();
                    return;
                }

                var existing = ReadXData(bref);
                if (!existing.HasValue)
                {
                    ed.WriteMessage("\nThis block does not carry an EPDB link.");
                    tr.Abort();
                    return;
                }

                bref.UpgradeOpen();
                RemoveXData(bref);
                tr.Commit();
                ed.WriteMessage($"\nEPDB link removed (was equip_id={existing.Value}).");
            }
            catch (System.Exception ex)
            {
                tr.Abort();
                ed.WriteMessage($"\nUnlink error: {ex.Message}");
            }
        }

        /// <summary>
        /// Iterates all block references in model space, finds those carrying EPDB_LINK
        /// XData, re-queries the database, and rewrites their attribute values.
        /// Blocks whose equip_id no longer exists in the DB are flagged as STALE.
        /// All drawing modifications are wrapped in DocumentLock + Transaction.
        /// </summary>
        public static (int updated, int missing) RefreshAll(Document doc, DbContext db)
        {
            var ed = doc.Editor;

            // Phase 1 — read-only pass: collect (ObjectId, equip_id) pairs.
            var links = new List<(ObjectId objId, int equipId)>();
            using (var trRead = doc.Database.TransactionManager.StartTransaction())
            {
                var bt = (BlockTable)trRead.GetObject(
                    doc.Database.BlockTableId, OpenMode.ForRead);
                var ms = (BlockTableRecord)trRead.GetObject(
                    bt[BlockTableRecord.ModelSpace], OpenMode.ForRead);

                foreach (ObjectId eid in ms)
                {
                    var ent = trRead.GetObject(eid, OpenMode.ForRead);
                    if (ent is not BlockReference bref) continue;
                    var xId = ReadXData(bref);
                    if (xId.HasValue) links.Add((eid, xId.Value));
                }
                trRead.Commit();
            }

            if (links.Count == 0)
            {
                ed.WriteMessage("\nNo EPDB-linked blocks found in model space.");
                return (0, 0);
            }

            // Phase 2 — DB queries (synchronous; runs on the AutoCAD main thread,
            // but Task.Run is not used here to avoid holding a transaction open).
            var equipCache = new Dictionary<int, Equipment?>();
            foreach (var (_, equipId) in links)
            {
                if (!equipCache.ContainsKey(equipId))
                    equipCache[equipId] = db.GetEquipmentById(equipId);
            }

            // Phase 3 — write transaction: rewrite attribute values.
            int updated = 0, missing = 0;
            using var docLock = doc.LockDocument();
            using var trWrite = doc.Database.TransactionManager.StartTransaction();
            try
            {
                foreach (var (objId, equipId) in links)
                {
                    var bref = (BlockReference)trWrite.GetObject(objId, OpenMode.ForWrite);
                    if (equipCache.TryGetValue(equipId, out var equip) && equip != null)
                    {
                        FillAttributes(bref, equip, trWrite);
                        updated++;
                    }
                    else
                    {
                        MarkStale(bref, trWrite);
                        missing++;
                    }
                }
                trWrite.Commit();
            }
            catch
            {
                trWrite.Abort();
                throw;
            }

            ed.WriteMessage(
                $"\nEPDB sync: {updated} refreshed, {missing} stale (record deleted).");
            return (updated, missing);
        }

        // ------------------------------------------------------------------ //
        // XData helpers
        // ------------------------------------------------------------------ //

        public static void EnsureRegApp(Database db, Transaction tr)
        {
            var rat = (RegAppTable)tr.GetObject(db.RegAppTableId, OpenMode.ForRead);
            if (rat.Has(RegAppName)) return;
            rat.UpgradeOpen();
            var entry = new RegAppTableRecord { Name = RegAppName };
            rat.Add(entry);
            tr.AddNewlyCreatedDBObject(entry, true);
        }

        /// <summary>Writes equip_id as XData under the EPDB_LINK RegApp.</summary>
        public static void WriteXData(BlockReference bref, int equipId,
                                       Transaction tr, Database db)
        {
            EnsureRegApp(db, tr);
            // Code 1071 = DxfCode.ExtendedDataInteger32 (32-bit signed int in XData).
            using var xdata = new ResultBuffer(
                new TypedValue((int)DxfCode.ExtendedDataRegAppName, RegAppName),
                new TypedValue((int)DxfCode.ExtendedDataInteger32,  equipId));
            bref.XData = xdata;
        }

        /// <summary>Returns the stored equip_id, or null if not linked.</summary>
        public static int? ReadXData(BlockReference bref)
        {
            using var xdata = bref.GetXDataForApplication(RegAppName);
            if (xdata == null) return null;
            foreach (TypedValue tv in xdata)
            {
                if (tv.TypeCode == (short)DxfCode.ExtendedDataInteger32)
                    return Convert.ToInt32(tv.Value);
            }
            return null;
        }

        /// <summary>
        /// Clears the EPDB_LINK XData by writing a buffer containing only the
        /// RegApp name (the AutoCAD convention for removing XData for an app).
        /// </summary>
        public static void RemoveXData(BlockReference bref)
        {
            using var xdata = new ResultBuffer(
                new TypedValue((int)DxfCode.ExtendedDataRegAppName, RegAppName));
            bref.XData = xdata;
        }

        // ------------------------------------------------------------------ //
        // Attribute definition / reference helpers
        // ------------------------------------------------------------------ //

        /// <summary>
        /// Ensures every key in AttrMap has a corresponding AttributeDefinition in
        /// the block table record. Existing definitions are left untouched.
        /// </summary>
        public static void EnsureAttributeDefs(BlockTableRecord btr, Transaction tr)
        {
            var existing = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (ObjectId id in btr)
            {
                if (tr.GetObject(id, OpenMode.ForRead) is AttributeDefinition ad)
                    existing.Add(ad.Tag);
            }

            // Match the drawing's current text height (TEXTSIZE); fall back to 2.5.
            var db = btr.Database;
            double th = db != null && db.Textsize > 0 ? db.Textsize : 2.5;
            double rowH = th * 1.6;

            double y = -rowH * 0.5;
            foreach (var key in AttrMap.Keys)
            {
                if (existing.Contains(key)) continue;
                y -= rowH;
                var atDef = new AttributeDefinition
                {
                    Tag        = key,
                    Prompt     = key.Replace('_', ' ') + ": ",
                    TextString = "",
                    Position   = new Point3d(0, y, 0),
                    Height     = th,
                    Invisible  = false,
                    Layer      = "0",
                };
                btr.AppendEntity(atDef);
                tr.AddNewlyCreatedDBObject(atDef, true);
            }
        }

        /// <summary>
        /// Adds AttributeReference objects to <paramref name="bref"/> for any
        /// AttributeDefinition in its block definition that is not yet represented.
        /// Call this after EnsureAttributeDefs when the block ref already exists.
        /// </summary>
        public static void InitAttributeRefs(BlockReference bref, Transaction tr)
        {
            var existing = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (ObjectId atId in bref.AttributeCollection)
                existing.Add(((AttributeReference)tr.GetObject(atId, OpenMode.ForRead)).Tag);

            var btr = (BlockTableRecord)tr.GetObject(bref.BlockTableRecord, OpenMode.ForRead);
            foreach (ObjectId id in btr)
            {
                var obj = tr.GetObject(id, OpenMode.ForRead);
                if (obj is not AttributeDefinition atDef || atDef.Constant) continue;
                if (existing.Contains(atDef.Tag)) continue;

                var atRef = new AttributeReference();
                atRef.SetAttributeFromBlock(atDef, bref.BlockTransform);
                atRef.TextString = "";
                bref.AttributeCollection.AppendAttribute(atRef);
                tr.AddNewlyCreatedDBObject(atRef, true);
            }
        }

        /// <summary>Writes equipment field values to the block's attribute references.</summary>
        public static void FillAttributes(BlockReference bref, Equipment equip, Transaction tr)
        {
            foreach (ObjectId atId in bref.AttributeCollection)
            {
                var atRef = (AttributeReference)tr.GetObject(atId, OpenMode.ForWrite);
                if (AttrMap.TryGetValue(atRef.Tag, out var fn))
                    atRef.TextString = fn(equip);
            }
        }

        // ------------------------------------------------------------------ //
        // Block creation from loose geometry
        // ------------------------------------------------------------------ //

        /// <summary>
        /// Creates a named block from a single loose entity, inserts a block reference
        /// in its place, and returns the ObjectId of the new block reference.
        /// </summary>
        private static ObjectId CreateBlockFromEntity(Entity source, Equipment equip,
                                                       Transaction tr, Database db)
        {
            // Choose a unique block name derived from the equipment tag.
            var blockName = $"EPDB_{equip.Tag}";
            var bt = (BlockTable)tr.GetObject(db.BlockTableId, OpenMode.ForRead);
            if (bt.Has(blockName)) blockName = $"EPDB_{equip.Tag}_{equip.EquipId}";

            // Use the entity's min-extents corner as the block insertion base point.
            Point3d basePt;
            try   { basePt = source.GeometricExtents.MinPoint; }
            catch { basePt = Point3d.Origin; }

            // Create the block definition.
            bt.UpgradeOpen();
            var btr = new BlockTableRecord { Name = blockName };
            bt.Add(btr);
            tr.AddNewlyCreatedDBObject(btr, true);

            // Clone the entity into the block definition (shift to block-local coords).
            if (source.Clone() is Entity clone)
            {
                clone.TransformBy(Matrix3d.Displacement(basePt.GetAsVector().Negate()));
                btr.AppendEntity(clone);
                tr.AddNewlyCreatedDBObject(clone, true);
            }

            // Add all attribute definitions from AttrMap.
            EnsureAttributeDefs(btr, tr);

            // Erase the original entity.
            source.UpgradeOpen();
            source.Erase();

            // Insert a block reference at basePt in model space.
            var ms = (BlockTableRecord)tr.GetObject(
                bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);
            var bref = new BlockReference(basePt, bt[blockName]);
            ms.AppendEntity(bref);
            tr.AddNewlyCreatedDBObject(bref, true);

            // Initialise attribute references on the new block reference.
            InitAttributeRefs(bref, tr);

            return bref.ObjectId;
        }

        /// <summary>
        /// Visually flags a block whose equip_id no longer exists in the database.
        /// Sets TAG = "RECORD DELETED" and STATUS = "STALE" so operators notice.
        /// </summary>
        private static void MarkStale(BlockReference bref, Transaction tr)
        {
            foreach (ObjectId atId in bref.AttributeCollection)
            {
                var atRef = (AttributeReference)tr.GetObject(atId, OpenMode.ForWrite);
                if (string.Equals(atRef.Tag, "TAG",    StringComparison.OrdinalIgnoreCase))
                    atRef.TextString = "RECORD DELETED";
                else if (string.Equals(atRef.Tag, "STATUS", StringComparison.OrdinalIgnoreCase))
                    atRef.TextString = "STALE";
            }
        }
    }
}
