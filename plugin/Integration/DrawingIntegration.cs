using System;
using System.Collections.Generic;
using Autodesk.AutoCAD.ApplicationServices;
using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.AutoCAD.EditorInput;
using Autodesk.AutoCAD.Geometry;
using AcDbPlugin.Data;

namespace AcDbPlugin.Integration
{
    /// <summary>
    /// Pushes database records into the active AutoCAD drawing.
    ///
    /// Three operations are offered for each entity type:
    ///   1. Insert a block reference at a user-picked point.
    ///   2. Write fields into the attributes of a selected existing block.
    ///   3. Append a row to a selected AutoCAD Table object.
    ///
    /// Every drawing-database write is wrapped in a Transaction with DocumentLock.
    /// </summary>
    public static class DrawingIntegration
    {
        // ------------------------------------------------------------------ //
        // Public entry points called from the palette ViewModels
        // ------------------------------------------------------------------ //

        public static void InsertEquipment(Equipment e)
        {
            var fields = EquipFields(e);
            RunInsertWorkflow($"EQUIP_{e.Tag}", fields, e.Tag);
        }

        public static void InsertInstrument(Instrument inst)
        {
            var fields = InstrFields(inst);
            RunInsertWorkflow($"INSTR_{inst.Tag}", fields, inst.Tag);
        }

        public static void InsertCable(Cable c)
        {
            var fields = CableFields(c);
            RunInsertWorkflow($"CABLE_{c.CableTag}", fields, c.CableTag);
        }

        // ------------------------------------------------------------------ //
        // Workflow — ask user what action to take, then dispatch
        // ------------------------------------------------------------------ //

        private static void RunInsertWorkflow(string defaultBlockName,
                                              Dictionary<string, string> fields,
                                              string tag)
        {
            var doc = Application.DocumentManager.MdiActiveDocument;
            if (doc == null) return;
            var ed = doc.Editor;

            var kw = new PromptKeywordOptions(
                $"\nInsert '{tag}' into drawing [Block/Attributes/Table/Cancel]")
            {
                AllowNone = false,
            };
            kw.Keywords.Add("Block");
            kw.Keywords.Add("Attributes");
            kw.Keywords.Add("Table");
            kw.Keywords.Add("Cancel");

            var res = ed.GetKeywords(kw);
            if (res.Status != PromptStatus.OK) return;

            switch (res.StringResult)
            {
                case "Block":      InsertBlock(doc, defaultBlockName, fields); break;
                case "Attributes": WriteToExistingBlock(doc, fields);          break;
                case "Table":      AppendToTable(doc, tag, fields);            break;
                // Cancel — do nothing
            }
        }

        // ------------------------------------------------------------------ //
        // Operation 1 — Insert a block reference at a picked point
        // ------------------------------------------------------------------ //

        private static void InsertBlock(Document doc,
                                        string blockName,
                                        Dictionary<string, string> fields)
        {
            var ed = doc.Editor;

            // Let the user pick an insertion point
            var ptRes = ed.GetPoint("\nPick insertion point: ");
            if (ptRes.Status != PromptStatus.OK) return;
            var insertPt = ptRes.Value;

            using var docLock = doc.LockDocument();
            using var tr = doc.Database.TransactionManager.StartTransaction();
            try
            {
                var bt = (BlockTable)tr.GetObject(
                    doc.Database.BlockTableId, OpenMode.ForRead);

                if (!bt.Has(blockName))
                {
                    // Block definition doesn't exist — create a minimal placeholder
                    CreatePlaceholderBlock(doc.Database, tr, blockName, fields);
                }

                var btr = (BlockTableRecord)tr.GetObject(
                    bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite);

                var blockRef = new BlockReference(insertPt, bt[blockName]);
                btr.AppendEntity(blockRef);
                tr.AddNewlyCreatedDBObject(blockRef, true);

                // Write attributes if the block definition has them
                WriteBlockAttributes(tr, blockRef, fields);

                tr.Commit();
                ed.WriteMessage($"\nInserted block '{blockName}' at {insertPt}.");
            }
            catch (Exception ex)
            {
                tr.Abort();
                ed.WriteMessage($"\nInsert error: {ex.Message}");
            }
        }

        private static void CreatePlaceholderBlock(Database db, Transaction tr,
                                                    string blockName,
                                                    Dictionary<string, string> fields)
        {
            var bt = (BlockTable)tr.GetObject(db.BlockTableId, OpenMode.ForWrite);
            var btr = new BlockTableRecord { Name = blockName };
            bt.Add(btr);
            tr.AddNewlyCreatedDBObject(btr, true);

            // Use the drawing's current text size; fall back to 2.5 (standard mm height).
            double th = db.Textsize > 0 ? db.Textsize : 2.5;
            double pad = th * 0.5;
            double rowH = th * 1.6;
            double boxW = 40 * th;           // generous width for field values
            double boxH = (fields.Count + 1) * rowH + pad * 2;

            // Visible bounding rectangle so the block is never invisible.
            var rect = new Polyline();
            rect.AddVertexAt(0, new Point2d(0,      0),     0, 0, 0);
            rect.AddVertexAt(1, new Point2d(boxW,   0),     0, 0, 0);
            rect.AddVertexAt(2, new Point2d(boxW,  -boxH),  0, 0, 0);
            rect.AddVertexAt(3, new Point2d(0,     -boxH),  0, 0, 0);
            rect.Closed = true;
            rect.Layer = "0";
            btr.AppendEntity(rect);
            tr.AddNewlyCreatedDBObject(rect, true);

            // Block-name label at the top of the rectangle.
            var label = new DBText
            {
                Position   = new Point3d(pad, -pad - th, 0),
                Height     = th,
                TextString = blockName,
                Layer      = "0",
            };
            btr.AppendEntity(label);
            tr.AddNewlyCreatedDBObject(label, true);

            // One attribute definition per field, stacked inside the box.
            double y = -pad - th - rowH * 0.5;
            foreach (var kvp in fields)
            {
                y -= rowH;
                var atDef = new AttributeDefinition
                {
                    Tag        = kvp.Key,
                    Prompt     = kvp.Key + ": ",
                    TextString = kvp.Value,
                    Position   = new Point3d(pad, y, 0),
                    Height     = th,
                    Invisible  = false,
                    Layer      = "0",
                };
                btr.AppendEntity(atDef);
                tr.AddNewlyCreatedDBObject(atDef, true);
            }
        }

        private static void WriteBlockAttributes(Transaction tr,
                                                  BlockReference bref,
                                                  Dictionary<string, string> fields)
        {
            // AttributeCollection has no Clear(); populate from the block definition instead.
            var btr = (BlockTableRecord)tr.GetObject(bref.BlockTableRecord, OpenMode.ForRead);
            foreach (ObjectId id in btr)
            {
                var ent = tr.GetObject(id, OpenMode.ForRead);
                if (ent is not AttributeDefinition atDef || atDef.Constant) continue;

                var atRef = new AttributeReference();
                atRef.SetAttributeFromBlock(atDef, bref.BlockTransform);

                if (fields.TryGetValue(atDef.Tag.ToUpperInvariant(), out var val))
                    atRef.TextString = val;

                bref.AttributeCollection.AppendAttribute(atRef);
                tr.AddNewlyCreatedDBObject(atRef, true);
            }
        }

        // ------------------------------------------------------------------ //
        // Operation 2 — Write fields into attributes of a selected block
        // ------------------------------------------------------------------ //

        private static void WriteToExistingBlock(Document doc,
                                                  Dictionary<string, string> fields)
        {
            var ed = doc.Editor;
            var selRes = ed.GetEntity("\nSelect a block reference to populate: ");
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

                bref.UpgradeOpen();
                int updated = 0;
                foreach (ObjectId atId in bref.AttributeCollection)
                {
                    var atRef = (AttributeReference)tr.GetObject(atId, OpenMode.ForWrite);
                    if (fields.TryGetValue(atRef.Tag.ToUpperInvariant(), out var val))
                    {
                        atRef.TextString = val;
                        updated++;
                    }
                }

                tr.Commit();
                ed.WriteMessage($"\nUpdated {updated} attribute(s).");
            }
            catch (Exception ex)
            {
                tr.Abort();
                ed.WriteMessage($"\nAttribute write error: {ex.Message}");
            }
        }

        // ------------------------------------------------------------------ //
        // Operation 3 — Append a row to a selected Table object
        // ------------------------------------------------------------------ //

        private static void AppendToTable(Document doc,
                                           string tag,
                                           Dictionary<string, string> fields)
        {
            var ed = doc.Editor;
            var selRes = ed.GetEntity("\nSelect an AutoCAD Table to append to: ");
            if (selRes.Status != PromptStatus.OK) return;

            using var docLock = doc.LockDocument();
            using var tr = doc.Database.TransactionManager.StartTransaction();
            try
            {
                var tbl = tr.GetObject(selRes.ObjectId, OpenMode.ForWrite) as Table;
                if (tbl == null)
                {
                    ed.WriteMessage("\nSelected entity is not a Table.");
                    tr.Abort();
                    return;
                }

                int newRow = tbl.Rows.Count;
                tbl.InsertRows(newRow, tbl.Rows[newRow - 1].Height, 1);

                // Map fields to columns by matching the header row (row 0)
                for (int col = 0; col < tbl.Columns.Count; col++)
                {
                    var header = tbl.Cells[0, col].TextString?.ToUpperInvariant()?.Trim();
                    if (header != null && fields.TryGetValue(header, out var val))
                        tbl.Cells[newRow, col].TextString = val;
                }

                // Fallback: fill by position if headers don't match
                var values = new List<string>(fields.Values);
                for (int col = 0; col < Math.Min(tbl.Columns.Count, values.Count); col++)
                {
                    if (string.IsNullOrEmpty(tbl.Cells[newRow, col].TextString))
                        tbl.Cells[newRow, col].TextString = values[col];
                }

                tr.Commit();
                ed.WriteMessage($"\nAppended row for '{tag}' to table.");
            }
            catch (Exception ex)
            {
                tr.Abort();
                ed.WriteMessage($"\nTable append error: {ex.Message}");
            }
        }

        // ------------------------------------------------------------------ //
        // Field dictionaries — key must match attribute tag names
        // ------------------------------------------------------------------ //

        private static Dictionary<string, string> EquipFields(Equipment e) =>
            new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
            {
                ["TAG"]           = e.Tag,
                ["NAME"]          = e.Name,
                ["BUS_VOLTAGE_V"] = e.BusVoltageV?.ToString() ?? "",
                ["FED_FROM_TAG"]  = e.FedFromTag,
                ["BREAKER_TRIP"]  = e.BreakerTripA?.ToString() ?? "",
                ["DRAWING_REF"]   = e.DrawingRef,
                ["SHEET_NUMBER"]  = e.SheetNumber,
                ["ONE_LINE_REF"]  = e.OneLineRef,
                ["STATUS"]        = e.Status,
            };

        private static Dictionary<string, string> InstrFields(Instrument i) =>
            new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
            {
                ["TAG"]             = i.Tag,
                ["SERVICE"]         = i.ServiceDescription,
                ["LOOP_NUMBER"]     = i.LoopNumber,
                ["P_AND_ID_REF"]    = i.PAndIdRef,
                ["PANEL_TAG"]       = i.PanelTag,
                ["SIGNAL_TYPE"]     = i.SignalType,
                ["SUPPLY_SOURCE"]   = i.SupplySourceTag,
                ["DRAWING_REF"]     = i.DrawingRef,
                ["SHEET_NUMBER"]    = i.SheetNumber,
                ["STATUS"]          = i.Status,
            };

        private static Dictionary<string, string> CableFields(Cable c) =>
            new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
            {
                ["CABLE_TAG"]   = c.CableTag,
                ["SERVICE"]     = c.ServiceDescription,
                ["FROM_TAG"]    = c.FromTag,
                ["FROM_TERM"]   = c.FromTerminal,
                ["TO_TAG"]      = c.ToTag,
                ["TO_TERM"]     = c.ToTerminal,
                ["CONDUIT_TAG"] = c.ConduitTag,
                ["LENGTH_FT"]   = c.LengthFt?.ToString() ?? "",
                ["STATUS"]      = c.Status,
            };
    }
}
