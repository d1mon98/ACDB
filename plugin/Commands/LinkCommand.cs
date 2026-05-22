using Autodesk.AutoCAD.ApplicationServices;
using Autodesk.AutoCAD.Runtime;
using AcDbPlugin.Integration;

// Register this class so AutoCAD discovers EPDBLINK / EPDBSYNC / EPDBUNLINK.
[assembly: CommandClass(typeof(AcDbPlugin.Commands.LinkCommand))]

namespace AcDbPlugin.Commands
{
    /// <summary>
    /// AutoCAD command wrappers for the linked-block feature.
    /// These can be typed at the command line or triggered via ribbon/script.
    ///
    /// EPDBLINK  — Select an object and link it to the equipment record currently
    ///             selected in the EPDB palette.
    /// EPDBSYNC  — Re-read the database and refresh every linked block in model space.
    /// EPDBUNLINK — Remove the EPDB_LINK XData from a selected block reference.
    /// </summary>
    public class LinkCommand
    {
        [CommandMethod("EPDBLINK", CommandFlags.Modal)]
        public void LinkObject()
        {
            var doc = Application.DocumentManager.MdiActiveDocument;
            if (doc == null) return;
            var ed = doc.Editor;

            // Read the equipment selected in the palette.
            var equip = EpdbCommand.Palette?.ViewModel.Equipment.Selected;
            if (equip == null)
            {
                ed.WriteMessage(
                    "\nNo equipment selected in the EPDB palette. " +
                    "Open EPDB, select a project, and click an equipment row first.");
                return;
            }

            var db = EpdbCommand.Palette?.ViewModel.Db;
            if (db == null)
            {
                ed.WriteMessage("\nNo database loaded. Use EPDBSET to select a .db file.");
                return;
            }

            LinkedBlockService.LinkObject(equip, db);
        }

        [CommandMethod("EPDBSYNC", CommandFlags.Modal)]
        public void SyncLinkedBlocks()
        {
            var doc = Application.DocumentManager.MdiActiveDocument;
            if (doc == null) return;
            var ed = doc.Editor;

            var db = EpdbCommand.Palette?.ViewModel.Db;
            if (db == null)
            {
                ed.WriteMessage("\nNo database loaded. Use EPDBSET to select a .db file.");
                return;
            }

            LinkedBlockService.RefreshAll(doc, db);
        }

        [CommandMethod("EPDBUNLINK", CommandFlags.Modal)]
        public void UnlinkObject()
        {
            LinkedBlockService.UnlinkObject();
        }
    }
}
