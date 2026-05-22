using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Interop;
using AcDbPlugin.ViewModels;
using AcadApp = Autodesk.AutoCAD.ApplicationServices.Application;

namespace AcDbPlugin.Views
{
    public partial class RecordEntryWindow : Window
    {
        public RecordEntryWindow(RecordEntryViewModel vm)
        {
            InitializeComponent();
            DataContext = vm;
            Loaded += OnLoaded;
        }

        // Parent this window to AutoCAD's main window.
        // Without this, AutoCAD captures all keyboard input and the TextBoxes
        // appear to do nothing when you type.
        protected override void OnSourceInitialized(EventArgs e)
        {
            base.OnSourceInitialized(e);
            try
            {
                new WindowInteropHelper(this).Owner =
                    AcadApp.MainWindow.Handle;
            }
            catch { /* non-fatal — window still usable without correct parent */ }
        }

        private void OnLoaded(object sender, RoutedEventArgs e)
        {
            // Move keyboard focus to the first editable TextBox automatically
            var first = FindFirstTextBox(this);
            first?.Focus();
            first?.SelectAll();
        }

        private static TextBox? FindFirstTextBox(DependencyObject parent)
        {
            for (int i = 0; i < System.Windows.Media.VisualTreeHelper.GetChildrenCount(parent); i++)
            {
                var child = System.Windows.Media.VisualTreeHelper.GetChild(parent, i);
                if (child is TextBox tb && tb.IsEnabled && tb.Visibility == Visibility.Visible)
                    return tb;
                var found = FindFirstTextBox(child);
                if (found != null) return found;
            }
            return null;
        }

        private void OkButton_Click(object sender, RoutedEventArgs e)
        {
            DialogResult = true;
            Close();
        }

        private void CancelButton_Click(object sender, RoutedEventArgs e)
        {
            DialogResult = false;
            Close();
        }
    }
}
