using System;
using System.Collections.ObjectModel;
using System.Threading.Tasks;
using System.Windows;
using AcDbPlugin.Data;

namespace AcDbPlugin.ViewModels
{
    public class CablesTabViewModel : ViewModelBase
    {
        private readonly MainViewModel _main;
        private Cable? _selected;

        public CablesTabViewModel(MainViewModel main)
        {
            _main = main;
            RefreshCommand       = new AsyncRelayCommand(LoadAsync);
            AddCommand           = new AsyncRelayCommand(AddAsync);
            EditCommand          = new AsyncRelayCommand(EditAsync,   () => _selected != null);
            DeleteCommand        = new AsyncRelayCommand(DeleteAsync, () => _selected != null);
            InsertDrawingCommand = new RelayCommand(InsertIntoDrawing, () => _selected != null);
        }

        public ObservableCollection<Cable> Rows { get; } = new ObservableCollection<Cable>();

        public Cable? Selected { get => _selected; set => Set(ref _selected, value); }

        public AsyncRelayCommand RefreshCommand       { get; }
        public AsyncRelayCommand AddCommand           { get; }
        public AsyncRelayCommand EditCommand          { get; }
        public AsyncRelayCommand DeleteCommand        { get; }
        public RelayCommand      InsertDrawingCommand { get; }

        public async Task LoadAsync()
        {
            var proj = _main.SelectedProject;
            if (_main.Db == null || proj == null) { Rows.Clear(); return; }
            _main.IsBusy = true;
            try
            {
                var list = await _main.Db.GetCablesAsync(proj.ProjectId);
                Rows.Clear();
                foreach (var c in list) Rows.Add(c);
            }
            catch (Exception ex) { _main.Status = $"Cables error: {ex.Message}"; }
            finally { _main.IsBusy = false; }
        }

        private async Task AddAsync()
        {
            var proj = _main.SelectedProject;
            if (_main.Db == null || proj == null) return;

            var vm = new RecordEntryViewModel(RecordType.Cable, _main.Db, proj.ProjectId);
            await vm.LoadCatalogsAsync();

            var win = new Views.RecordEntryWindow(vm);
            if (win.ShowDialog() != true) return;

            var cable = vm.ToCable();
            var err = await ResolveCableEndpointsAsync(cable, proj.ProjectId);
            if (err != null) { _main.Status = err; return; }

            try
            {
                await _main.Db.AddCableAsync(cable);
                _main.Status = $"Cable {cable.CableTag} added.";
                await LoadAsync();
            }
            catch (Exception ex) { _main.Status = $"Add failed: {ex.Message}"; }
        }

        private async Task EditAsync()
        {
            if (_main.Db == null || _selected == null || _main.SelectedProject == null) return;

            var vm = new RecordEntryViewModel(RecordType.Cable, _main.Db,
                                              _main.SelectedProject.ProjectId);
            await vm.LoadCatalogsAsync();
            vm.LoadCable(_selected);

            var win = new Views.RecordEntryWindow(vm);
            if (win.ShowDialog() != true) return;

            var cable = vm.ToCable();
            cable.CableId   = _selected.CableId;
            cable.ProjectId = _selected.ProjectId;

            var err = await ResolveCableEndpointsAsync(cable, _main.SelectedProject.ProjectId);
            if (err != null) { _main.Status = err; return; }

            try
            {
                await _main.Db.UpdateCableAsync(cable);
                _main.Status = $"Cable {cable.CableTag} updated.";
                await LoadAsync();
            }
            catch (Exception ex) { _main.Status = $"Edit failed: {ex.Message}"; }
        }

        /// <summary>
        /// Resolves cable.FromTag / cable.ToTag to FK IDs.
        /// Returns null on success, or an error string to display.
        /// </summary>
        private async Task<string?> ResolveCableEndpointsAsync(Cable cable, int projectId)
        {
            if (_main.Db == null) return "No database.";

            // --- FROM endpoint ---
            if (string.IsNullOrWhiteSpace(cable.FromTag))
                return "FROM tag is required.";

            var fromEquip = await _main.Db.FindEquipmentByTagAsync(projectId, cable.FromTag);
            if (fromEquip != null)
            {
                cable.FromEquipmentId  = fromEquip.EquipId;
                cable.FromInstrumentId = null;
            }
            else
            {
                var fromInstr = await _main.Db.FindInstrumentByTagAsync(projectId, cable.FromTag);
                if (fromInstr == null)
                    return $"FROM tag '{cable.FromTag}' not found in equipment or instruments.";
                cable.FromEquipmentId  = null;
                cable.FromInstrumentId = fromInstr.InstrumentId;
            }

            // --- TO endpoint ---
            if (string.IsNullOrWhiteSpace(cable.ToTag))
                return "TO tag is required.";

            var toEquip = await _main.Db.FindEquipmentByTagAsync(projectId, cable.ToTag);
            if (toEquip != null)
            {
                cable.ToEquipmentId  = toEquip.EquipId;
                cable.ToInstrumentId = null;
            }
            else
            {
                var toInstr = await _main.Db.FindInstrumentByTagAsync(projectId, cable.ToTag);
                if (toInstr == null)
                    return $"TO tag '{cable.ToTag}' not found in equipment or instruments.";
                cable.ToEquipmentId  = null;
                cable.ToInstrumentId = toInstr.InstrumentId;
            }

            return null;
        }

        private async Task DeleteAsync()
        {
            if (_main.Db == null || _selected == null) return;
            var r = MessageBox.Show(
                $"Delete cable '{_selected.CableTag}'?", "Confirm Delete",
                MessageBoxButton.YesNo, MessageBoxImage.Warning);
            if (r != MessageBoxResult.Yes) return;

            try
            {
                await _main.Db.DeleteCableAsync(_selected.CableId);
                _main.Status = $"Cable {_selected.CableTag} deleted.";
                await LoadAsync();
            }
            catch (Exception ex) { _main.Status = $"Delete failed: {ex.Message}"; }
        }

        private void InsertIntoDrawing()
        {
            if (_selected == null) return;
            Integration.DrawingIntegration.InsertCable(_selected);
        }
    }
}
