using System;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using Autodesk.Windows;
using AcApp = Autodesk.AutoCAD.ApplicationServices.Core.Application;

namespace AcDbPlugin.Commands
{
    /// <summary>
    /// Creates the "Electrical DB" ribbon tab with EPDB and Set DB buttons.
    /// Call Build() from Initialize() — or from ItemInitialized if the ribbon
    /// isn't ready yet at plugin load time.
    /// </summary>
    internal static class RibbonBuilder
    {
        private const string TabId   = "ACDBPLUGIN_TAB";
        private const string PanelId = "ACDBPLUGIN_PANEL";

        public static void Build()
        {
            var ribbon = ComponentManager.Ribbon;
            if (ribbon == null) return;

            // Guard: don't add twice if NETLOAD is called again
            if (ribbon.FindTab(TabId) != null) return;

            // ── Tab ──────────────────────────────────────────────────────────
            var tab = new RibbonTab
            {
                Title = "Electrical DB",
                Id    = TabId,
            };

            // ── Panel ─────────────────────────────────────────────────────────
            var panelSrc = new RibbonPanelSource
            {
                Title = "Database",
                Id    = PanelId,
            };

            // ── Large EPDB button ─────────────────────────────────────────────
            var epdbBtn = new RibbonButton
            {
                Text           = "Open\nEPDB",
                CommandHandler = new RibbonCmd("EPDB "),
                LargeImage     = DbIcon(32),
                Image          = DbIcon(16),
                ShowText       = true,
                Size           = RibbonItemSize.Large,
                Orientation    = System.Windows.Controls.Orientation.Vertical,
                ToolTip        = Tip("Electrical Project Database",
                                     "Open the EPDB palette to browse catalogs, " +
                                     "add/edit project records, and push data into the drawing."),
            };

            // ── Small "Set DB" button ─────────────────────────────────────────
            var setBtn = new RibbonButton
            {
                Text           = "Set DB",
                CommandHandler = new RibbonCmd("EPDBSET "),
                LargeImage     = FolderIcon(32),
                Image          = FolderIcon(16),
                ShowText       = true,
                Size           = RibbonItemSize.Standard,
                Orientation    = System.Windows.Controls.Orientation.Horizontal,
                ToolTip        = Tip("Set Database File",
                                     "Browse to select the .db SQLite project database."),
            };

            panelSrc.Items.Add(epdbBtn);
            panelSrc.Items.Add(new RibbonSeparator());
            panelSrc.Items.Add(setBtn);

            var panel = new RibbonPanel { Source = panelSrc };
            tab.Panels.Add(panel);
            ribbon.Tabs.Add(tab);

            // Make the new tab active so the user sees it immediately
            tab.IsActive = true;
        }

        // ── ICommand handler that sends a string to the AutoCAD command line ──

        private sealed class RibbonCmd : ICommand
        {
            private readonly string _cmd;
            public RibbonCmd(string cmd) => _cmd = cmd;
            public bool CanExecute(object parameter) => true;
            public event EventHandler? CanExecuteChanged;
            public void Execute(object parameter)
            {
                var doc = AcApp.DocumentManager.MdiActiveDocument;
                doc?.SendStringToExecute(_cmd + "\n", true, false, true);
            }
        }

        // ── Tooltip helper ────────────────────────────────────────────────────

        private static RibbonToolTip Tip(string title, string body) =>
            new RibbonToolTip
            {
                Title         = title,
                Content       = body,
                IsHelpEnabled = false,
            };

        // ── Icon generators (pure WPF — no image files needed) ───────────────

        /// <summary>Blue database-cylinder icon.</summary>
        private static BitmapSource DbIcon(int sz)
        {
            var v = new DrawingVisual();
            using (var dc = v.RenderOpen())
            {
                // Blue rounded background
                dc.DrawRoundedRectangle(
                    new SolidColorBrush(Color.FromRgb(43, 87, 154)),
                    null,
                    new Rect(0.5, 0.5, sz - 1, sz - 1),
                    sz * 0.18, sz * 0.18);

                // Draw a database cylinder in white
                double cx  = sz / 2.0;
                double rw  = sz * 0.36;       // half-width of ellipse
                double ry  = sz * 0.11;       // vertical radius of ellipse
                double top = sz * 0.20;       // top of cylinder
                double bot = sz * 0.75;       // bottom of cylinder
                double gap = (bot - top) / 3.0;

                var white = Brushes.White;

                // Cylinder body (filled rectangle between top and bottom ellipses)
                dc.DrawRectangle(white, null,
                    new Rect(cx - rw, top + ry, rw * 2, bot - top));

                // Bottom ellipse
                dc.DrawEllipse(white, null, new Point(cx, bot + ry), rw, ry);

                // Two "shelf" lines inside the cylinder
                dc.DrawEllipse(
                    new SolidColorBrush(Color.FromRgb(43, 87, 154)), null,
                    new Point(cx, top + gap + ry), rw, ry);
                dc.DrawEllipse(
                    new SolidColorBrush(Color.FromRgb(43, 87, 154)), null,
                    new Point(cx, top + gap * 2 + ry), rw, ry);

                // Top ellipse (cap)
                dc.DrawEllipse(white, null, new Point(cx, top + ry), rw, ry);
            }

            return Render(v, sz);
        }

        /// <summary>Green folder icon for "Set DB".</summary>
        private static BitmapSource FolderIcon(int sz)
        {
            var v = new DrawingVisual();
            using (var dc = v.RenderOpen())
            {
                // Green rounded background
                dc.DrawRoundedRectangle(
                    new SolidColorBrush(Color.FromRgb(56, 120, 56)),
                    null,
                    new Rect(0.5, 0.5, sz - 1, sz - 1),
                    sz * 0.18, sz * 0.18);

                double m  = sz * 0.15;
                double t  = sz * 0.30;
                double b  = sz * 0.80;
                double r  = sz - m;
                double nt = sz * 0.42;   // top of the folder body

                var white = Brushes.White;

                // Folder tab (upper-left bump)
                var tab = new StreamGeometry();
                using (var ctx = tab.Open())
                {
                    ctx.BeginFigure(new Point(m, nt), true, true);
                    ctx.LineTo(new Point(m, t), true, false);
                    ctx.LineTo(new Point(sz * 0.45, t), true, false);
                    ctx.LineTo(new Point(sz * 0.53, nt), true, false);
                }
                dc.DrawGeometry(white, null, tab);

                // Folder body
                dc.DrawRoundedRectangle(white, null,
                    new Rect(m, nt, r - m, b - nt), sz * 0.05, sz * 0.05);
            }

            return Render(v, sz);
        }

        private static BitmapSource Render(DrawingVisual v, int sz)
        {
            var bmp = new RenderTargetBitmap(sz, sz, 96, 96, PixelFormats.Pbgra32);
            bmp.Render(v);
            bmp.Freeze();
            return bmp;
        }
    }
}
