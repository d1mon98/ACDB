using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Interop;
using AcDbPlugin.ViewModels;
using AcadApp = Autodesk.AutoCAD.ApplicationServices.Application;

namespace AcDbPlugin.Views
{
    public partial class ProjectEntryWindow : Window
    {
        public string Title { get; }

        public ProjectEntryWindow(ProjectEntryViewModel vm, string title)
        {
            InitializeComponent();
            Title = title;
            DataContext = vm;
            Loaded += OnLoaded;
        }

        protected override void OnSourceInitialized(EventArgs e)
        {
            base.OnSourceInitialized(e);
            try { new WindowInteropHelper(this).Owner = AcadApp.MainWindow.Handle; }
            catch { }
        }

        private void OnLoaded(object sender, RoutedEventArgs e)
        {
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
