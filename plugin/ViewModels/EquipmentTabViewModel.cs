using System;
using System.Collections.ObjectModel;
using System.Threading.Tasks;
using AcDbPlugin.Data;

namespace AcDbPlugin.ViewModels
{
    public class EquipmentTabViewModel : ViewModelBase
    {
        private readonly MainViewModel _main;
        private Equipment? _selected;
        private string _filterText = "";

        public EquipmentTabViewModel(MainViewModel main)
        {
            _main = main;
            RefreshCommand         = new AsyncRelayCommand(LoadAsync);
            AddCommand             = new AsyncRelayCommand(AddAsync);
            EditCommand            = new AsyncRelayCommand(EditAsync,    () => _selected != null);
            DeleteCommand          = new AsyncRelayCommand(DeleteAsync,  () => _selected != null);
            InsertDrawingCommand   = new RelayCommand(InsertIntoDrawing, () => _selected != null);
            LinkObjectCommand      = new RelayCommand(LinkObject,        () => _selected != null);
        }

        public ObservableCollection<Equipment> Rows { get; } = new ObservableCollection<Equipment>();

        public Equipment? Selected
        {
            get => _selected;
            set => Set(ref _selected, value);
        }

        public string FilterText
        {
            get => _filterText;
            set => Set(ref _filterText, value);
        }

        public AsyncRelayCommand RefreshCommand       { get; }
        public AsyncRelayCommand AddCommand           { get; }
        public AsyncRelayCommand EditCommand          { get; }
        public AsyncRelayCommand DeleteCommand        { get; }
        public RelayCommand      InsertDrawingCommand { get; }
        public RelayCommand      LinkObjectCommand    { get; }

        public async Task LoadAsync()
        {
            var proj = _main.SelectedProject;
            if (_main.Db == null || proj == null) { Rows.Clear(); return; }
            _main.IsBusy = true;
            try
            {
                var list = await _main.Db.GetEquipmentAsync(proj.ProjectId);
                Rows.Clear();
                foreach (var e in list) Rows.Add(e);
            }
            catch (Exception ex) { _main.Status = $"Equipment error: {ex.Message}"; }
            finally { _main.IsBusy = false; }
        }

        private async Task AddAsync()
        {
            var proj = _main.SelectedProject;
            if (_main.Db == null || proj == null) return;

            var vm = new RecordEntryViewModel(RecordType.Equipment, _main.Db, proj.ProjectId);
            await vm.LoadCatalogsAsync();

            var win = new Views.RecordEntryWindow(vm);
            if (win.ShowDialog() != true) return;

            try
            {
                var e = vm.ToEquipment();
                await _main.Db.AddEquipmentAsync(e);
                _main.Status = $"Equipment {e.Tag} added.";
                await LoadAsync();
            }
            catch (Exception ex) { _main.Status = $"Add failed: {ex.Message}"; }
        }

        private async Task EditAsync()
        {
            if (_main.Db == null || _selected == null || _main.SelectedProject == null) return;

            var vm = new RecordEntryViewModel(RecordType.Equipment, _main.Db,
                                              _main.SelectedProject.ProjectId);
            await vm.LoadCatalogsAsync();
            vm.LoadEquipment(_selected);

            var win = new Views.RecordEntryWindow(vm);
            if (win.ShowDialog() != true) return;

            try
            {
                var e = vm.ToEquipment();
                e.EquipId    = _selected.EquipId;
                e.ProjectId  = _selected.ProjectId;
                await _main.Db.UpdateEquipmentAsync(e);
                _main.Status = $"Equipment {e.Tag} updated.";
                await LoadAsync();
            }
            catch (Exception ex) { _main.Status = $"Edit failed: {ex.Message}"; }
        }

        private async Task DeleteAsync()
        {
            if (_main.Db == null || _selected == null) return;
            var result = System.Windows.MessageBox.Show(
                $"Delete equipment '{_selected.Tag}'?",
                "Confirm Delete",
                System.Windows.MessageBoxButton.YesNo,
                System.Windows.MessageBoxImage.Warning);
            if (result != System.Windows.MessageBoxResult.Yes) return;

            try
            {
                await _main.Db.DeleteEquipmentAsync(_selected.EquipId);
                _main.Status = $"Equipment {_selected.Tag} deleted.";
                await LoadAsync();
            }
            catch (Exception ex) { _main.Status = $"Delete failed: {ex.Message}"; }
        }

        private void InsertIntoDrawing()
        {
            if (_selected == null) return;
            Integration.DrawingIntegration.InsertEquipment(_selected);
        }

        private void LinkObject()
        {
            if (_selected == null || _main.Db == null) return;
            Integration.LinkedBlockService.LinkObject(_selected, _main.Db);
        }
    }
}
