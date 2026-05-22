using System;
using System.Collections.Generic;
using System.Data;
using System.Threading.Tasks;

namespace AcDbPlugin.ViewModels
{
    public class CatalogTabViewModel : ViewModelBase
    {
        private readonly MainViewModel _main;
        private DataTable? _rows;
        private string _selectedTable = "equip_catalog";

        public CatalogTabViewModel(MainViewModel main)
        {
            _main = main;
            RefreshCommand = new AsyncRelayCommand(LoadAsync);
        }

        public List<string> CatalogTables { get; } = new List<string>
        {
            "equip_catalog",
            "cable_catalog",
            "instrument_catalog",
            "conduit_catalog",
        };

        public string SelectedTable
        {
            get => _selectedTable;
            set
            {
                if (Set(ref _selectedTable, value))
                    _ = LoadAsync();
            }
        }

        public DataTable? Rows { get => _rows; private set => Set(ref _rows, value); }

        public AsyncRelayCommand RefreshCommand { get; }

        public async Task LoadAsync()
        {
            if (_main.Db == null) return;
            _main.IsBusy = true;
            try
            {
                Rows = await _main.Db.GetCatalogTableAsync(SelectedTable);
            }
            catch (Exception ex)
            {
                _main.Status = $"Catalog error: {ex.Message}";
            }
            finally { _main.IsBusy = false; }
        }
    }
}
