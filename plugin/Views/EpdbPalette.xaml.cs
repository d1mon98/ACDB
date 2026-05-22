using System.Windows;
using System.Windows.Controls;
using AcDbPlugin.ViewModels;

namespace AcDbPlugin.Views
{
    public partial class EpdbPalette : UserControl
    {
        public EpdbPalette()
        {
            InitializeComponent();
            ViewModel  = new MainViewModel();
            DataContext = ViewModel;
        }

        public MainViewModel ViewModel { get; }
    }
}
