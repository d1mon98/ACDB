using System;
using Autodesk.AutoCAD.ApplicationServices;
using Autodesk.AutoCAD.Runtime;
using Autodesk.AutoCAD.Windows;
using Autodesk.Windows;
using AcDbPlugin.Data;
using AcDbPlugin.Views;

// Register the extension application and command class with AutoCAD
[assembly: ExtensionApplication(typeof(AcDbPlugin.Commands.PluginApp))]
[assembly: CommandClass(typeof(AcDbPlugin.Commands.EpdbCommand))]

namespace AcDbPlugin.Commands
{
    /// <summary>
    /// IExtensionApplication lifecycle — called by AutoCAD when the DLL is loaded
    /// via NETLOAD and when AutoCAD closes.
    /// </summary>
    public class PluginApp : IExtensionApplication
    {
        public void Initialize()
        {
            Application.DocumentManager.MdiActiveDocument?.Editor
                .WriteMessage("\nElectrical Project DB plugin loaded. Type EPDB to open.\n");

            // Build ribbon tab — defer if the ribbon isn't ready yet
            if (ComponentManager.Ribbon != null)
                RibbonBuilder.Build();
            else
                ComponentManager.ItemInitialized += OnRibbonReady;
        }

        private static void OnRibbonReady(object sender, RibbonItemEventArgs e)
        {
            if (ComponentManager.Ribbon == null) return;
            ComponentManager.ItemInitialized -= OnRibbonReady;
            RibbonBuilder.Build();
        }

        public void Terminate() { /* nothing to clean up */ }
    }

    /// <summary>
    /// AutoCAD commands exposed by the plugin.
    /// </summary>
    public class EpdbCommand
    {
        // PaletteSet is static: created once, reused for the AutoCAD session lifetime.
        private static PaletteSet? _ps;
        private static EpdbPalette? _palette;

        // Exposed so LinkCommand can reach the currently-selected equipment and DB.
        public static EpdbPalette? Palette => _palette;

        // Stable GUID — identifies this PaletteSet across AutoCAD sessions
        private static readonly Guid PaletteGuid =
            new Guid("3A7F2C91-4D5B-4E8A-9F6C-1B2E3D4A5678");

        /// <summary>
        /// EPDB — opens or re-shows the Electrical Project DB palette.
        /// </summary>
        [CommandMethod("EPDB", CommandFlags.Modal)]
        public void ShowPalette()
        {
            if (_ps == null || _ps.IsDisposed)
            {
                _palette = new EpdbPalette();

                _ps = new PaletteSet("Electrical Project DB", PaletteGuid)
                {
                    MinimumSize = new System.Drawing.Size(440, 500),
                    Style       = PaletteSetStyles.ShowTabForSingle |
                                  PaletteSetStyles.NameEditable      |
                                  PaletteSetStyles.ShowPropertiesMenu |
                                  PaletteSetStyles.Snappable,
                };

                // AddVisual() hosts the WPF UserControl directly (AutoCAD 2019+)
                _ps.AddVisual("Electrical DB", _palette);
            }

            _ps.Visible = true;
        }

        /// <summary>
        /// EPDBSET — opens a file browser to select the .db database file.
        /// Equivalent to clicking "Set Database" inside the palette.
        /// </summary>
        [CommandMethod("EPDBSET", CommandFlags.Modal)]
        public void SetDatabase()
        {
            var dlg = new Microsoft.Win32.OpenFileDialog
            {
                Title  = "Select Electrical Project Database",
                Filter = "SQLite Database (*.db)|*.db|All files (*.*)|*.*",
            };

            var saved = PluginSettings.DatabasePath;
            if (!string.IsNullOrEmpty(saved))
                dlg.InitialDirectory = System.IO.Path.GetDirectoryName(saved);

            if (dlg.ShowDialog() != true) return;

            // Ensure palette is open, then push the new path into the VM
            if (_ps == null || _ps.IsDisposed) ShowPalette();
            _ = _palette?.ViewModel.InitDatabaseAsync(dlg.FileName);
        }
    }
}
